"""Type-safe data models for LLM cataloging responses and state management.

Provides Pydantic models for structured LLM outputs compatible with OpenAI's
strict mode, immutable catalog entry storage, and state management for sequential
table processing with parent context extraction.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from data_cataloger.schema.models import TableMetadata


class TableCatalog(BaseModel):
    """Pydantic model for LLM-generated table catalog response.

    Designed for OpenAI structured outputs with strict mode. Uses simple types
    only (str, list, Literal) without validators, computed fields, or complex
    unions to ensure compatibility.

    Why Literal instead of Enum:
        OpenAI strict mode requires JSON Schema-compatible types. Literal maps
        directly to JSON Schema enum, while Python Enum requires serialization
        configuration. Literal["PII", "financial", "public", "internal"] is
        simpler and more explicit.

    Attributes:
        description: Business purpose of the table in 1-2 sentences. Should
            explain what the table represents, not how it's implemented.
        sensitivity: Data sensitivity classification. Must be one of:
            - "PII": Personal Identifiable Information (names, emails, SSNs)
            - "financial": Financial data (transactions, account balances)
            - "public": Public data (marketing content, product catalog)
            - "internal": Internal business data (employee IDs, department codes)
        example_queries: 2-3 representative SQL queries demonstrating typical
            use cases for this table. Should include realistic WHERE clauses
            and JOINs if applicable.
    """

    description: str = Field(
        description="Business purpose of the table in 1-2 sentences"
    )
    sensitivity: Literal["PII", "financial", "public", "internal"] = Field(
        description="Data sensitivity classification"
    )
    example_queries: list[str] = Field(
        description="2-3 example SQL queries demonstrating typical usage"
    )


@dataclass(frozen=True)
class CatalogEntry:
    """Immutable catalog entry for a cataloged table.

    Why frozen dataclass:
        Catalog entries should never be modified after creation. Frozen=True
        prevents accidental mutation and makes entries safe to share across
        threads or store in cache structures. Dataclass is preferred over
        Pydantic here because we don't need validation (data comes from
        validated TableCatalog) and immutability is the priority.

    Attributes:
        table_name: Name of the cataloged table
        description: Business purpose (from TableCatalog.description)
        sensitivity: Data sensitivity classification (from TableCatalog.sensitivity)
        example_queries: Representative SQL queries (from TableCatalog.example_queries)
    """

    table_name: str
    description: str
    sensitivity: str
    example_queries: list[str]


@dataclass
class CatalogState:
    """State manager for sequential table cataloging with parent context tracking.

    Maintains a registry of cataloged tables and provides parent context extraction
    for dependency-aware analysis. When cataloging a table with foreign key
    references, we can include descriptions of already-cataloged parent tables
    to improve LLM understanding of relationships.

    Attributes:
        entries: Registry of cataloged tables keyed by table name. Use dict for
            O(1) lookup during parent context extraction.
    """

    entries: dict[str, CatalogEntry] = field(default_factory=dict)

    def add_entry(self, entry: CatalogEntry) -> None:
        """Add or update a catalog entry in state.

        Args:
            entry: Catalog entry to store. If table_name already exists,
                replaces the old entry.
        """
        self.entries[entry.table_name] = entry

    def get_parent_context(self, table: TableMetadata) -> list[CatalogEntry]:
        """Extract already-cataloged parent tables from foreign key references.

        How it enables context-aware analysis:
            When cataloging table B that references table A via foreign key,
            we can provide A's catalog entry to the LLM. This gives context
            like "users table stores customer account information (PII)" when
            analyzing "orders.user_id references users.id", improving description
            quality and relationship understanding.

        Args:
            table: Table metadata with foreign key information

        Returns:
            List of catalog entries for parent tables that:
            1. Are referenced in table.foreign_keys
            2. Have already been cataloged (exist in self.entries)

            Returns empty list if table has no foreign keys or none of the
            referenced tables have been cataloged yet.

        Note:
            Deduplicates parent tables (composite foreign keys may reference
            the same parent multiple times). Filters out self-references
            (hierarchical tables) and missing parents (circular dependencies
            or not-yet-processed tables).
        """
        if not table.foreign_keys:
            return []

        # Extract unique parent table names from foreign keys
        parent_names = {fk.referenced_table for fk in table.foreign_keys}

        # Return catalog entries for parents that exist in state
        # Filter out self-references and missing parents
        return [
            self.entries[name]
            for name in parent_names
            if name != table.table_name and name in self.entries
        ]
