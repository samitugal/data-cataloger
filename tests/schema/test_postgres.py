"""Tests for PostgreSQL schema extractor using mocked database cursors.

Tests all extraction methods without requiring a real PostgreSQL database by
mocking cursor.fetchall() and cursor.execute() calls.
"""

from unittest.mock import MagicMock

from data_cataloger.schema.models import ColumnMetadata, ForeignKeyMetadata
from data_cataloger.schema.postgres import PostgreSQLExtractor


def test_get_tables() -> None:
    """Test extracting table names from PostgreSQL."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("users",), ("products",), ("orders",)]

    extractor = PostgreSQLExtractor()
    tables = extractor.get_tables(mock_connector)

    assert tables == ["users", "products", "orders"]
    mock_cursor.execute.assert_called_once()
    # Verify SQL contains BASE TABLE filter
    call_args = mock_cursor.execute.call_args
    assert "BASE TABLE" in call_args[0][0]


def test_get_tables_filters_schema() -> None:
    """Test that get_tables passes schema parameter to query."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    extractor = PostgreSQLExtractor()
    extractor.get_tables(mock_connector, schema="myschema")

    # Verify execute called with schema parameter
    call_args = mock_cursor.execute.call_args
    assert call_args[0][1] == ("myschema",)


def test_get_columns() -> None:
    """Test extracting column metadata from PostgreSQL table."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Mock fetchall with column data: (name, type, is_nullable, position, default)
    mock_cursor.fetchall.return_value = [
        ("id", "integer", "NO", 1, None),
        ("email", "character varying", "NO", 2, None),
        ("created_at", "timestamp without time zone", "NO", 3, "now()"),
        ("bio", "text", "YES", 4, None),
    ]

    extractor = PostgreSQLExtractor()
    columns = extractor.get_columns(mock_connector, "users")

    assert len(columns) == 4
    assert columns[0] == ColumnMetadata(
        name="id",
        data_type="integer",
        is_nullable=False,
        ordinal_position=1,
        column_default=None,
    )
    assert columns[3] == ColumnMetadata(
        name="bio",
        data_type="text",
        is_nullable=True,
        ordinal_position=4,
        column_default=None,
    )
    # Verify execute called with schema and table parameters
    call_args = mock_cursor.execute.call_args
    assert call_args[0][1] == ("public", "users")


def test_get_columns_nullable_conversion() -> None:
    """Test that is_nullable string 'YES'/'NO' is converted to boolean."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("id", "integer", "NO", 1, None),
        ("name", "varchar", "YES", 2, None),
    ]

    extractor = PostgreSQLExtractor()
    columns = extractor.get_columns(mock_connector, "test_table")

    # Verify boolean conversion: 'NO' -> False, 'YES' -> True
    assert columns[0].is_nullable is False
    assert columns[1].is_nullable is True


def test_get_primary_keys() -> None:
    """Test extracting primary key column names."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("id",)]

    extractor = PostgreSQLExtractor()
    pk_columns = extractor.get_primary_keys(mock_connector, "users")

    assert pk_columns == ["id"]
    # Verify SQL contains PRIMARY KEY filter
    call_args = mock_cursor.execute.call_args
    assert "PRIMARY KEY" in call_args[0][0]


def test_get_primary_keys_composite() -> None:
    """Test extracting composite primary key with multiple columns."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Composite PK ordered by ordinal_position
    mock_cursor.fetchall.return_value = [("user_id",), ("product_id",)]

    extractor = PostgreSQLExtractor()
    pk_columns = extractor.get_primary_keys(mock_connector, "user_products")

    assert pk_columns == ["user_id", "product_id"]
    # Verify SQL orders by ordinal_position
    call_args = mock_cursor.execute.call_args
    assert "ordinal_position" in call_args[0][0]


def test_get_foreign_keys() -> None:
    """Test extracting foreign key constraints."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Mock FK data: (constraint_name, column_name, referenced_table,
    # referenced_column, ordinal_position)
    mock_cursor.fetchall.return_value = [
        ("fk_user", "user_id", "users", "id", 1),
        ("fk_product", "product_id", "products", "id", 1),
    ]

    extractor = PostgreSQLExtractor()
    fk_constraints = extractor.get_foreign_keys(mock_connector, "orders")

    assert len(fk_constraints) == 2
    assert fk_constraints[0] == ForeignKeyMetadata(
        constraint_name="fk_user",
        column_name="user_id",
        referenced_table="users",
        referenced_column="id",
        ordinal_position=1,
    )
    assert fk_constraints[1] == ForeignKeyMetadata(
        constraint_name="fk_product",
        column_name="product_id",
        referenced_table="products",
        referenced_column="id",
        ordinal_position=1,
    )


def test_get_foreign_keys_composite() -> None:
    """Test extracting composite foreign key with same constraint_name."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Composite FK: same constraint_name, different ordinal_position
    mock_cursor.fetchall.return_value = [
        ("fk_composite", "user_id", "users", "id", 1),
        ("fk_composite", "product_id", "users", "product_id", 2),
    ]

    extractor = PostgreSQLExtractor()
    fk_constraints = extractor.get_foreign_keys(mock_connector, "order_items")

    assert len(fk_constraints) == 2
    # Both share same constraint_name
    assert fk_constraints[0].constraint_name == "fk_composite"
    assert fk_constraints[1].constraint_name == "fk_composite"
    # Different ordinal positions
    assert fk_constraints[0].ordinal_position == 1
    assert fk_constraints[1].ordinal_position == 2
    # Verify SQL orders by constraint_name and ordinal_position
    call_args = mock_cursor.execute.call_args
    assert "constraint_name" in call_args[0][0]
    assert "ordinal_position" in call_args[0][0]


def test_get_foreign_keys_self_referencing() -> None:
    """Test extracting self-referencing foreign key (hierarchical table)."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Self-referencing FK: categories.parent_id -> categories.id
    mock_cursor.fetchall.return_value = [
        ("fk_parent", "parent_id", "categories", "id", 1),
    ]

    extractor = PostgreSQLExtractor()
    fk_constraints = extractor.get_foreign_keys(mock_connector, "categories")

    assert len(fk_constraints) == 1
    assert fk_constraints[0] == ForeignKeyMetadata(
        constraint_name="fk_parent",
        column_name="parent_id",
        referenced_table="categories",
        referenced_column="id",
        ordinal_position=1,
    )
    # Verify table references itself
    assert fk_constraints[0].referenced_table == "categories"
