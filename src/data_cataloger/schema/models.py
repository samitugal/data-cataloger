"""Immutable dataclass models for database schema metadata.

Provides type-safe, read-only structures for representing database tables,
columns, primary keys, and foreign key relationships extracted from PostgreSQL
and MySQL databases.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMetadata:
    """Immutable representation of a database column.

    Attributes:
        name: Column name as it appears in the database
        data_type: Raw SQL data type from information_schema (e.g., 'varchar',
            'integer', 'timestamp without time zone'). Not normalized - LLM will
            interpret type semantics during cataloging.
        is_nullable: True if column accepts NULL values, False otherwise
        ordinal_position: Position of column in table (1-based index)
        column_default: Default value expression or None if no default
    """

    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    column_default: str | None = None


@dataclass(frozen=True)
class ForeignKeyMetadata:
    """Immutable representation of a foreign key constraint column.

    For composite multi-column foreign keys, multiple ForeignKeyMetadata
    instances share the same constraint_name but have different column_name
    and ordinal_position values.

    Attributes:
        constraint_name: Name of the foreign key constraint
        column_name: Source column name in the referencing table
        referenced_table: Target table name being referenced
        referenced_column: Target column name in the referenced table
        ordinal_position: Position within composite FK (1-based). For single-column
            FKs, this is always 1.
    """

    constraint_name: str
    column_name: str
    referenced_table: str
    referenced_column: str
    ordinal_position: int


@dataclass(frozen=True)
class TableMetadata:
    """Immutable representation of a database table with full schema metadata.

    Attributes:
        schema_name: Schema/database name. For PostgreSQL typically 'public',
            for MySQL this is the database name from the connection.
        table_name: Table name as it appears in the database
        columns: Tuple of column metadata, ordered by ordinal_position.
            Tuple ensures immutability.
        primary_keys: Tuple of column names forming the primary key, in order.
            Empty tuple if table has no primary key.
        foreign_keys: Tuple of foreign key constraint metadata. For composite
            FKs, multiple entries share constraint_name. Empty tuple if no FKs.
    """

    schema_name: str
    table_name: str
    columns: tuple[ColumnMetadata, ...]
    primary_keys: tuple[str, ...]
    foreign_keys: tuple[ForeignKeyMetadata, ...]
