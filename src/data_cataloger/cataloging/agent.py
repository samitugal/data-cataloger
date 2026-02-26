"""Cataloging agent orchestrator for sequential LLM-powered table analysis.

Coordinates the complete cataloging workflow by processing tables in dependency
order (as provided by SchemaIntrospector), accumulating context from already-
cataloged parent tables, and generating rich catalog entries using GPT-4o with
automatic retry logic.

Why dependency order matters:
    When cataloging a table that references other tables via foreign keys, we
    want to include descriptions of those parent tables in the LLM prompt. This
    provides context that improves the quality and accuracy of the generated
    description. For example, when analyzing "orders" table, knowing that "users"
    table stores customer account information helps the LLM understand the
    relationship better.

Why circular dependencies must be rejected:
    Circular dependencies make it impossible to establish a consistent processing
    order. If table A references table B and B references A, we can't process
    one before the other. The agent requires SchemaIntrospector to detect and
    report these cycles so they can be resolved at the schema level (e.g., by
    breaking the cycle or accepting that some context will be missing).

How state accumulation enables context-aware analysis:
    CatalogState maintains a growing registry of cataloged tables. As we process
    each table in dependency order, we:
    1. Extract parent context from already-cataloged tables
    2. Generate catalog entry using LLM with this context
    3. Add the new entry to state for future tables to reference
    This creates a snowball effect where later tables benefit from richer context.
"""

import logging
from typing import Protocol

from data_cataloger.cataloging.client import CatalogClient
from data_cataloger.cataloging.models import CatalogEntry, CatalogState, TableCatalog
from data_cataloger.cataloging.prompts import SYSTEM_PROMPT, build_user_prompt
from data_cataloger.embeddings.client import EmbeddingClient
from data_cataloger.schema.introspector import SchemaAnalysisResult
from data_cataloger.schema.models import ForeignKeyMetadata, TableMetadata

logger = logging.getLogger(__name__)


class CatalogWriter(Protocol):
    """Protocol for catalog storage backends.

    Defines the interface for writing catalog entries and relationships to
    persistent storage. Implementations include Neo4jWriter for graph storage.
    """

    def write_entry(
        self,
        entry: CatalogEntry,
        database_name: str,
        database_type: str = "postgresql",
        embedding: list[float] | None = None,
    ) -> None:
        """Write a catalog entry to storage."""
        ...

    def write_relationships(
        self,
        table_name: str,
        foreign_keys: tuple[ForeignKeyMetadata, ...],
        database_name: str,
    ) -> None:
        """Write foreign key relationships to storage."""
        ...


class CatalogingAgent:
    """Orchestrate LLM-powered table cataloging with context accumulation.

    Processes tables in dependency order, maintaining state of cataloged tables
    to provide parent context for dependent table analysis.

    Example:
        >>> from data_cataloger.schema.introspector import SchemaIntrospector
        >>> from data_cataloger.connection.postgres import PostgreSQLConnector
        >>> connector = PostgreSQLConnector(config)
        >>> connector.connect()
        >>> introspector = SchemaIntrospector()
        >>> schema_result = introspector.introspect_schema(connector)
        >>> agent = CatalogingAgent()
        >>> catalog = agent.catalog_database(schema_result)
        >>> for table_name, entry in catalog.items():
        ...     print(f"{table_name}: {entry.description}")
    """

    def __init__(
        self,
        client: CatalogClient | None = None,
        writer: CatalogWriter | None = None,
        embedding_client: EmbeddingClient | None = None,
    ) -> None:
        """Initialize agent with OpenAI client and optional storage writer.

        Args:
            client: CatalogClient instance. If None, creates new client.
                    Allows dependency injection for testing with mock clients.
            writer: Optional storage writer implementing CatalogWriter protocol.
                    If provided, catalog entries are persisted after each table.
            embedding_client: Optional EmbeddingClient for generating embeddings.
                    If provided, embeddings are generated and stored with entries.
        """
        self.client = client or CatalogClient()
        self._writer = writer
        self._embedding_client = embedding_client

    def catalog_database(
        self,
        schema_result: SchemaAnalysisResult,
        database_name: str = "",
        database_type: str = "postgresql",
    ) -> dict[str, CatalogEntry]:
        """Catalog all tables in dependency order with context accumulation.

        Processes tables sequentially in the order specified by schema_result.
        processing_order, ensuring that parent tables are cataloged before their
        dependent children. Each table receives context from all previously
        cataloged parent tables.

        Args:
            schema_result: SchemaAnalysisResult from SchemaIntrospector containing
                          tables metadata and processing_order
            database_name: Database name for storage grouping. If empty and writer
                          is provided, derives from first table's schema_name.
            database_type: Database type identifier (default: postgresql)

        Returns:
            Dictionary mapping table_name to CatalogEntry for all tables

        Raises:
            ValueError: If schema_result has circular dependencies
        """
        # Check for circular dependencies first
        if schema_result.circular_dependencies:
            raise ValueError(
                f"Cannot catalog with circular dependencies: "
                f"{schema_result.circular_dependencies}"
            )

        # Derive database_name from first table's schema if not provided
        db_name = database_name
        if not db_name and self._writer and schema_result.tables:
            db_name = schema_result.tables[0].schema_name

        # Create fast lookup dict for table metadata
        tables_by_name: dict[str, TableMetadata] = {
            table.table_name: table for table in schema_result.tables
        }

        # Initialize catalog state for context accumulation
        state = CatalogState()

        # Process tables in dependency order
        for table_name in schema_result.processing_order:
            # Get metadata for this table
            table_meta = tables_by_name[table_name]

            # Get parent context from already-cataloged tables
            parent_context = state.get_parent_context(table_meta)

            # Catalog this table with parent context
            entry = self._catalog_table(table_meta, parent_context)

            # Add to state for future tables to reference
            state.add_entry(entry)

            # Write to storage if writer is provided
            if self._writer:
                self._write_to_storage(entry, table_meta, db_name, database_type)

        return state.entries

    def _write_to_storage(
        self,
        entry: CatalogEntry,
        table_meta: TableMetadata,
        database_name: str,
        database_type: str,
    ) -> None:
        """Write catalog entry and relationships to storage with error handling.

        Catches and logs write failures without halting the cataloging pipeline.
        This ensures that storage issues don't prevent catalog generation.

        If embedding_client is configured, generates embedding from description
        and stores it alongside the catalog entry.

        Args:
            entry: Catalog entry to persist
            table_meta: Table metadata with foreign key information
            database_name: Database name for storage grouping
            database_type: Database type identifier
        """
        if not self._writer:
            return

        try:
            embedding: list[float] | None = None
            if self._embedding_client and entry.description:
                try:
                    embedding = self._embedding_client.embed(entry.description)
                    logger.debug(f"Generated embedding for {entry.table_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to generate embedding for {entry.table_name}: {e}"
                    )

            self._writer.write_entry(entry, database_name, database_type, embedding)
            self._writer.write_relationships(
                entry.table_name, table_meta.foreign_keys, database_name
            )
        except Exception as e:
            logger.warning(f"Failed to write {entry.table_name} to storage: {e}")

    def _catalog_table(
        self, table: TableMetadata, parent_context: list[CatalogEntry]
    ) -> CatalogEntry:
        """Catalog single table using LLM with parent context.

        Builds prompt from table metadata and parent context, calls OpenAI API
        with retry logic, and converts Pydantic response to immutable CatalogEntry.

        Args:
            table: TableMetadata with columns, PKs, FKs
            parent_context: List of already-cataloged parent tables

        Returns:
            CatalogEntry with LLM-generated description, sensitivity, queries
        """
        # Build messages for LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(table, parent_context)},
        ]

        # Call LLM with retry logic (client handles exponential backoff)
        # Type assertion: analyze_table returns BaseModel but we know it's TableCatalog
        result = self.client.analyze_table(messages, TableCatalog)
        assert isinstance(result, TableCatalog)

        # Convert Pydantic TableCatalog to immutable CatalogEntry
        return CatalogEntry(
            table_name=table.table_name,
            description=result.description,
            sensitivity=result.sensitivity,
            example_queries=result.example_queries,
        )
