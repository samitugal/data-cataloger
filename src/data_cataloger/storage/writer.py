"""Neo4j graph database writer for catalog entries with MERGE-based upsert.

Provides atomic write operations for transforming CatalogEntry dataclasses into
Neo4j graph nodes with Database parent nodes and REFERENCES_VIA relationship edges.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import neo4j

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.schema.models import ForeignKeyMetadata


class Neo4jWriter:
    """Neo4j writer for catalog entries with MERGE-based upsert operations.

    Provides atomic write methods for persisting catalog data as graph nodes:
    - Table nodes with flat properties (description, sensitivity, example_queries)
    - Database parent nodes for grouping tables via HAS_TABLE edges
    - REFERENCES_VIA edges for foreign key relationships with metadata properties

    Uses MERGE operations to support re-cataloging without creating duplicates.
    All operations execute within the specified database (default: "neo4j").

    Attributes:
        _driver: Neo4j driver instance for executing queries
        _database: Target database name for query execution
    """

    def __init__(self, driver: neo4j.Driver, database: str = "neo4j") -> None:
        """Initialize writer with driver and verify connectivity.

        Args:
            driver: Neo4j driver instance (from GraphDatabase.driver())
            database: Target database name (default: neo4j). Always specified
                to avoid Neo4j driver bugs with database selection.

        Raises:
            neo4j.exceptions.ServiceUnavailable: If driver cannot connect to Neo4j
        """
        self._driver = driver
        self._database = database
        # Fail fast if Neo4j is unreachable (health check on startup)
        self._driver.verify_connectivity()

    def write_entry(
        self,
        entry: CatalogEntry,
        database_name: str,
        database_type: str = "postgresql",
        embedding: list[float] | None = None,
    ) -> None:
        """Write catalog entry as Table node with Database parent using MERGE upsert.

        Creates or updates three graph components atomically:
        1. Database node with name and type properties
        2. Table node with flat properties (description, sensitivity, example_queries)
        3. HAS_TABLE relationship connecting Database to Table

        MERGE behavior:
        - First catalog: Creates Database node, Table node, and HAS_TABLE edge
          with created_at
        - Re-catalog: Updates Table properties and updated_at, leaves Database
          and edge unchanged

        Args:
            entry: Catalog entry containing table_name and analysis results
            database_name: Database name for grouping (becomes Database node name)
            database_type: Database type identifier (default: postgresql)
            embedding: Optional embedding vector for semantic search (1536 dimensions)

        Example:
            >>> entry = CatalogEntry(
            ...     table_name="users",
            ...     description="Customer accounts",
            ...     sensitivity="PII",
            ...     example_queries=["SELECT * FROM users WHERE email = ?"]
            ... )
            >>> writer.write_entry(entry, "production_db", "postgresql")
            # Creates: (db:Database)-[:HAS_TABLE]->(users:Table)
        """
        now = datetime.now(UTC).isoformat()

        query = """
        MERGE (repo:MetadataRepository {name: 'default'})
        ON CREATE SET repo.created_at = $timestamp

        MERGE (db:Database {name: $database_name, type: $database_type})
        ON CREATE SET db.created_at = $timestamp

        MERGE (repo)-[:CONTAINS_DATABASE]->(db)

        MERGE (t:Table {name: $table_name, database: $database_name})
        ON CREATE SET
            t.description = $description,
            t.sensitivity = $sensitivity,
            t.example_queries = $example_queries,
            t.embedding = $embedding,
            t.created_at = $timestamp
        ON MATCH SET
            t.description = $description,
            t.sensitivity = $sensitivity,
            t.example_queries = $example_queries,
            t.embedding = $embedding,
            t.updated_at = $timestamp

        MERGE (db)-[:HAS_TABLE]->(t)
        """

        self._driver.execute_query(
            query,
            database_name=database_name,
            database_type=database_type,
            table_name=entry.table_name,
            description=entry.description,
            sensitivity=entry.sensitivity,
            example_queries=entry.example_queries,
            embedding=embedding,
            timestamp=now,
            database_=self._database,
        )

    def write_relationships(
        self,
        table_name: str,
        foreign_keys: tuple[ForeignKeyMetadata, ...],
        database_name: str,
    ) -> None:
        """Write foreign key relationships as REFERENCES_VIA edges with FK metadata.

        Creates REFERENCES_VIA edges from source table to referenced tables using
        node-first MERGE pattern. Creates stub Table nodes for uncataloged referenced
        tables (allows FK edges before target table is cataloged).

        Each FK creates:
        - Source Table node (with database property for multi-tenant support)
        - Target Table node (stub if not yet cataloged)
        - REFERENCES_VIA edge with FK metadata (fk_column, referenced_column,
          constraint_name)

        Args:
            table_name: Source table name (the table with the foreign key)
            foreign_keys: Tuple of FK metadata from schema introspection
            database_name: Database name for node identification

        Example:
            >>> fks = (
            ...     ForeignKeyMetadata(
            ...         constraint_name="fk_orders_user",
            ...         column_name="user_id",
            ...         referenced_table="users",
            ...         referenced_column="id",
            ...         ordinal_position=1
            ...     ),
            ... )
            >>> writer.write_relationships("orders", fks, "production_db")
            # Creates: (orders:Table)-[:REFERENCES_VIA {fk_column: "user_id", ...}]
            # ->(users:Table)
        """
        for fk in foreign_keys:
            # Node-first MERGE pattern to avoid relationship duplication pitfall
            query = """
            MERGE (source:Table {name: $source_table, database: $database})
            MERGE (target:Table {name: $target_table, database: $database})
            MERGE (source)-[r:REFERENCES_VIA {
                fk_column: $fk_column,
                referenced_column: $referenced_column,
                constraint_name: $constraint_name
            }]->(target)
            """

            self._driver.execute_query(
                query,
                source_table=table_name,
                target_table=fk.referenced_table,
                database=database_name,
                fk_column=fk.column_name,
                referenced_column=fk.referenced_column,
                constraint_name=fk.constraint_name,
                database_=self._database,
            )

    def create_vector_index(self) -> None:
        """Create vector index for semantic search on table embeddings.

        Creates a Neo4j vector index on the embedding property of Table nodes.
        Uses cosine similarity with 1536 dimensions (OpenAI text-embedding-3-small).

        Safe to call multiple times - uses IF NOT EXISTS clause.
        """
        query = """
        CREATE VECTOR INDEX table_embedding_index IF NOT EXISTS
        FOR (t:Table)
        ON t.embedding
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
        self._driver.execute_query(query, database_=self._database)

    def close(self) -> None:
        """Close the Neo4j driver connection.

        Should be called when done with the writer to release connection
        resources. Consider using context manager (__enter__/__exit__) instead
        for automatic cleanup.
        """
        self._driver.close()

    def __enter__(self) -> Neo4jWriter:
        """Enter context manager (with statement support).

        Returns:
            Self for use in with statement body
        """
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Exit context manager and close driver connection.

        Args:
            exc_type: Exception type (if exception occurred)
            exc_val: Exception value (if exception occurred)
            exc_tb: Exception traceback (if exception occurred)
        """
        self.close()
