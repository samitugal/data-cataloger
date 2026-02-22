"""Tests for schema metadata dataclass models.

Verifies immutability, type correctness, and proper instantiation of schema
metadata structures used throughout schema extraction and dependency analysis.
"""

import pytest

from data_cataloger.schema.models import (
    ColumnMetadata,
    ForeignKeyMetadata,
    TableMetadata,
)


def test_column_metadata_creation() -> None:
    """Test ColumnMetadata instantiation with all fields."""
    column = ColumnMetadata(
        name="user_id",
        data_type="integer",
        is_nullable=False,
        ordinal_position=1,
        column_default="nextval('users_id_seq'::regclass)",
    )

    assert column.name == "user_id"
    assert column.data_type == "integer"
    assert column.is_nullable is False
    assert column.ordinal_position == 1
    assert column.column_default == "nextval('users_id_seq'::regclass)"


def test_column_metadata_nullable_conversion() -> None:
    """Test is_nullable as boolean, not 'YES'/'NO' string."""
    nullable_column = ColumnMetadata(
        name="email",
        data_type="varchar",
        is_nullable=True,
        ordinal_position=2,
    )

    not_nullable_column = ColumnMetadata(
        name="id",
        data_type="integer",
        is_nullable=False,
        ordinal_position=1,
    )

    assert nullable_column.is_nullable is True
    assert not_nullable_column.is_nullable is False
    assert isinstance(nullable_column.is_nullable, bool)
    assert isinstance(not_nullable_column.is_nullable, bool)


def test_column_metadata_immutable() -> None:
    """Test that ColumnMetadata is frozen and cannot be modified."""
    column = ColumnMetadata(
        name="created_at",
        data_type="timestamp without time zone",
        is_nullable=False,
        ordinal_position=3,
        column_default="now()",
    )

    with pytest.raises(AttributeError):
        column.name = "updated_at"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        column.is_nullable = True  # type: ignore[misc]


def test_column_metadata_optional_default() -> None:
    """Test ColumnMetadata with None as column_default."""
    column = ColumnMetadata(
        name="status",
        data_type="varchar",
        is_nullable=True,
        ordinal_position=4,
    )

    assert column.column_default is None


def test_foreign_key_metadata_creation() -> None:
    """Test ForeignKeyMetadata instantiation with all fields."""
    fk = ForeignKeyMetadata(
        constraint_name="fk_orders_customer",
        column_name="customer_id",
        referenced_table="customers",
        referenced_column="id",
        ordinal_position=1,
    )

    assert fk.constraint_name == "fk_orders_customer"
    assert fk.column_name == "customer_id"
    assert fk.referenced_table == "customers"
    assert fk.referenced_column == "id"
    assert fk.ordinal_position == 1


def test_foreign_key_metadata_immutable() -> None:
    """Test that ForeignKeyMetadata is frozen and cannot be modified."""
    fk = ForeignKeyMetadata(
        constraint_name="fk_line_items_order",
        column_name="order_id",
        referenced_table="orders",
        referenced_column="id",
        ordinal_position=1,
    )

    with pytest.raises(AttributeError):
        fk.constraint_name = "fk_different_name"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        fk.referenced_table = "different_table"  # type: ignore[misc]


def test_foreign_key_metadata_composite() -> None:
    """Test ForeignKeyMetadata for composite multi-column foreign keys."""
    # Composite FK: FOREIGN KEY (dept_id, emp_id) REFERENCES assignments(dept, emp)
    fk1 = ForeignKeyMetadata(
        constraint_name="fk_composite",
        column_name="dept_id",
        referenced_table="assignments",
        referenced_column="dept",
        ordinal_position=1,
    )
    fk2 = ForeignKeyMetadata(
        constraint_name="fk_composite",
        column_name="emp_id",
        referenced_table="assignments",
        referenced_column="emp",
        ordinal_position=2,
    )

    # Same constraint_name, different columns and ordinal_positions
    assert fk1.constraint_name == fk2.constraint_name
    assert fk1.column_name != fk2.column_name
    assert fk1.ordinal_position == 1
    assert fk2.ordinal_position == 2


def test_table_metadata_creation() -> None:
    """Test TableMetadata instantiation with columns, PKs, and FKs."""
    columns = (
        ColumnMetadata(
            name="id",
            data_type="integer",
            is_nullable=False,
            ordinal_position=1,
        ),
        ColumnMetadata(
            name="name",
            data_type="varchar",
            is_nullable=False,
            ordinal_position=2,
        ),
        ColumnMetadata(
            name="parent_id",
            data_type="integer",
            is_nullable=True,
            ordinal_position=3,
        ),
    )

    foreign_keys = (
        ForeignKeyMetadata(
            constraint_name="fk_self_ref",
            column_name="parent_id",
            referenced_table="categories",
            referenced_column="id",
            ordinal_position=1,
        ),
    )

    table = TableMetadata(
        schema_name="public",
        table_name="categories",
        columns=columns,
        primary_keys=("id",),
        foreign_keys=foreign_keys,
    )

    assert table.schema_name == "public"
    assert table.table_name == "categories"
    assert len(table.columns) == 3
    assert table.columns[0].name == "id"
    assert table.primary_keys == ("id",)
    assert len(table.foreign_keys) == 1
    assert table.foreign_keys[0].referenced_table == "categories"


def test_table_metadata_empty_constraints() -> None:
    """Test TableMetadata with empty primary_keys and foreign_keys tuples."""
    columns = (
        ColumnMetadata(
            name="log_id",
            data_type="bigint",
            is_nullable=False,
            ordinal_position=1,
        ),
        ColumnMetadata(
            name="message",
            data_type="text",
            is_nullable=True,
            ordinal_position=2,
        ),
    )

    table = TableMetadata(
        schema_name="public",
        table_name="audit_log",
        columns=columns,
        primary_keys=(),  # No primary key
        foreign_keys=(),  # No foreign keys
    )

    assert table.primary_keys == ()
    assert table.foreign_keys == ()
    assert len(table.columns) == 2


def test_table_metadata_immutable() -> None:
    """Test that TableMetadata is frozen and cannot be modified."""
    table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(),
        primary_keys=(),
        foreign_keys=(),
    )

    with pytest.raises(AttributeError):
        table.table_name = "customers"  # type: ignore[misc]

    with pytest.raises(AttributeError):
        table.schema_name = "staging"  # type: ignore[misc]


def test_table_metadata_columns_tuple() -> None:
    """Test that columns field accepts tuple[ColumnMetadata, ...], not list."""
    columns_tuple = (
        ColumnMetadata(
            name="id",
            data_type="integer",
            is_nullable=False,
            ordinal_position=1,
        ),
    )

    # Should accept tuple
    table = TableMetadata(
        schema_name="public",
        table_name="test_table",
        columns=columns_tuple,
        primary_keys=("id",),
        foreign_keys=(),
    )

    assert isinstance(table.columns, tuple)
    assert len(table.columns) == 1

    # Verify tuples are immutable (can't append/extend)
    with pytest.raises(AttributeError):
        table.columns.append(  # type: ignore[attr-defined]
            ColumnMetadata(
                name="new_col",
                data_type="text",
                is_nullable=True,
                ordinal_position=2,
            )
        )


def test_table_metadata_composite_primary_key() -> None:
    """Test TableMetadata with composite multi-column primary key."""
    columns = (
        ColumnMetadata(
            name="dept_id",
            data_type="integer",
            is_nullable=False,
            ordinal_position=1,
        ),
        ColumnMetadata(
            name="emp_id",
            data_type="integer",
            is_nullable=False,
            ordinal_position=2,
        ),
    )

    table = TableMetadata(
        schema_name="public",
        table_name="assignments",
        columns=columns,
        primary_keys=("dept_id", "emp_id"),  # Composite PK
        foreign_keys=(),
    )

    assert table.primary_keys == ("dept_id", "emp_id")
    assert len(table.primary_keys) == 2
