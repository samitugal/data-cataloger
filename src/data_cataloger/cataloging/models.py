"""Catalog entry models for LLM-generated table documentation.

Minimal stub to support prompt generation (Plan 04-03).
Full implementation in Plan 04-01.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
    """Immutable catalog entry for a documented table.

    Attributes:
        table_name: Name of the cataloged table
        description: Business purpose description
        sensitivity: Data sensitivity classification
        example_queries: List of example SQL queries
    """

    table_name: str
    description: str
    sensitivity: str
    example_queries: list[str]
