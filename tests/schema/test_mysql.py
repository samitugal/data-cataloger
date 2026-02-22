"""Tests for MySQL schema extractor.

Verifies MySQL-specific INFORMATION_SCHEMA queries, uppercase column names,
nullable conversion, and proper FK filtering using mocked database cursors.
"""

from unittest.mock import MagicMock

from data_cataloger.schema.models import ColumnMetadata, ForeignKeyMetadata
from data_cataloger.schema.mysql import MySQLExtractor


def test_get_tables() -> None:
    """Test get_tables returns table names and filters to BASE TABLE."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("users",),
        ("products",),
        ("orders",),
    ]

    extractor = MySQLExtractor()
    tables = extractor.get_tables(mock_connector, schema="testdb")

    assert tables == ["users", "products", "orders"]
    mock_cursor.execute.assert_called_once()

    # Verify SQL uses uppercase TABLE_NAME and filters to BASE TABLE
    sql_call = mock_cursor.execute.call_args[0][0]
    assert "TABLE_NAME" in sql_call
    assert "BASE TABLE" in sql_call
    assert "TABLE_SCHEMA" in sql_call

    # Verify parameterized query with schema
    params = mock_cursor.execute.call_args[0][1]
    assert params == ("testdb",)


def test_get_tables_filters_schema() -> None:
    """Test get_tables uses correct schema parameter."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("table1",)]

    extractor = MySQLExtractor()
    extractor.get_tables(mock_connector, schema="mydb")

    # Verify execute called with correct schema parameter
    params = mock_cursor.execute.call_args[0][1]
    assert params == ("mydb",)


def test_get_columns() -> None:
    """Test get_columns returns ColumnMetadata objects."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("id", "int", "NO", 1, None),
        ("email", "varchar", "YES", 2, None),
        ("created_at", "timestamp", "NO", 3, "CURRENT_TIMESTAMP"),
    ]

    extractor = MySQLExtractor()
    columns = extractor.get_columns(mock_connector, table="users", schema="testdb")

    assert len(columns) == 3
    assert all(isinstance(col, ColumnMetadata) for col in columns)

    # Verify first column
    assert columns[0].name == "id"
    assert columns[0].data_type == "int"
    assert columns[0].is_nullable is False
    assert columns[0].ordinal_position == 1
    assert columns[0].column_default is None

    # Verify second column
    assert columns[1].name == "email"
    assert columns[1].data_type == "varchar"
    assert columns[1].is_nullable is True
    assert columns[1].ordinal_position == 2

    # Verify third column with default
    assert columns[2].name == "created_at"
    assert columns[2].column_default == "CURRENT_TIMESTAMP"


def test_get_columns_nullable_conversion() -> None:
    """Test is_nullable string 'YES'/'NO' converts to boolean."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Mix of YES and NO values
    mock_cursor.fetchall.return_value = [
        ("nullable_col", "varchar", "YES", 1, None),
        ("not_nullable_col", "int", "NO", 2, None),
    ]

    extractor = MySQLExtractor()
    columns = extractor.get_columns(mock_connector, table="test", schema="testdb")

    # Verify boolean conversion
    assert columns[0].is_nullable is True  # 'YES' -> True
    assert columns[1].is_nullable is False  # 'NO' -> False


def test_get_columns_query_parameters() -> None:
    """Test get_columns uses correct query parameters."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    extractor = MySQLExtractor()
    extractor.get_columns(mock_connector, table="users", schema="testdb")

    # Verify SQL uses uppercase column names
    sql_call = mock_cursor.execute.call_args[0][0]
    assert "COLUMN_NAME" in sql_call
    assert "DATA_TYPE" in sql_call
    assert "IS_NULLABLE" in sql_call
    assert "ORDINAL_POSITION" in sql_call

    # Verify parameters (schema, table)
    params = mock_cursor.execute.call_args[0][1]
    assert params == ("testdb", "users")


def test_get_primary_keys() -> None:
    """Test get_primary_keys returns column names."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("id",)]

    extractor = MySQLExtractor()
    pk_columns = extractor.get_primary_keys(
        mock_connector, table="users", schema="testdb"
    )

    assert pk_columns == ["id"]

    # Verify SQL uses CONSTRAINT_NAME = 'PRIMARY' (MySQL-specific)
    sql_call = mock_cursor.execute.call_args[0][0]
    assert "CONSTRAINT_NAME" in sql_call
    assert "'PRIMARY'" in sql_call or '"PRIMARY"' in sql_call


def test_get_primary_keys_composite() -> None:
    """Test get_primary_keys preserves order for composite keys."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Composite PK: (user_id, role_id) in specific order
    mock_cursor.fetchall.return_value = [
        ("user_id",),
        ("role_id",),
    ]

    extractor = MySQLExtractor()
    pk_columns = extractor.get_primary_keys(
        mock_connector, table="user_roles", schema="testdb"
    )

    # Verify order preserved
    assert pk_columns == ["user_id", "role_id"]


def test_get_primary_keys_none() -> None:
    """Test get_primary_keys returns empty list when no PK exists."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    extractor = MySQLExtractor()
    pk_columns = extractor.get_primary_keys(
        mock_connector, table="logs", schema="testdb"
    )

    assert pk_columns == []


def test_get_foreign_keys() -> None:
    """Test get_foreign_keys returns ForeignKeyMetadata objects."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("fk_user", "user_id", "users", "id", 1),
        ("fk_product", "product_id", "products", "id", 1),
    ]

    extractor = MySQLExtractor()
    fks = extractor.get_foreign_keys(mock_connector, table="orders", schema="testdb")

    assert len(fks) == 2
    assert all(isinstance(fk, ForeignKeyMetadata) for fk in fks)

    # Verify first FK
    assert fks[0].constraint_name == "fk_user"
    assert fks[0].column_name == "user_id"
    assert fks[0].referenced_table == "users"
    assert fks[0].referenced_column == "id"
    assert fks[0].ordinal_position == 1

    # Verify second FK
    assert fks[1].constraint_name == "fk_product"
    assert fks[1].column_name == "product_id"
    assert fks[1].referenced_table == "products"


def test_get_foreign_keys_filters_null_references() -> None:
    """Test get_foreign_keys uses REFERENCED_TABLE_NAME IS NOT NULL filter."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []

    extractor = MySQLExtractor()
    extractor.get_foreign_keys(mock_connector, table="users", schema="testdb")

    # Verify SQL filters with REFERENCED_TABLE_NAME IS NOT NULL
    # This is critical - it distinguishes FKs from PKs/unique constraints
    sql_call = mock_cursor.execute.call_args[0][0]
    assert "REFERENCED_TABLE_NAME IS NOT NULL" in sql_call


def test_get_foreign_keys_composite() -> None:
    """Test get_foreign_keys handles composite FKs with ordinal positions."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Composite FK: (user_id, role_id) references (user_id, role_id)
    mock_cursor.fetchall.return_value = [
        ("fk_user_role", "user_id", "user_roles", "user_id", 1),
        ("fk_user_role", "role_id", "user_roles", "role_id", 2),
    ]

    extractor = MySQLExtractor()
    fks = extractor.get_foreign_keys(
        mock_connector, table="permissions", schema="testdb"
    )

    assert len(fks) == 2

    # Both FKs share same constraint_name
    assert fks[0].constraint_name == fks[1].constraint_name == "fk_user_role"

    # But different columns and ordinal positions
    assert fks[0].column_name == "user_id"
    assert fks[0].ordinal_position == 1
    assert fks[1].column_name == "role_id"
    assert fks[1].ordinal_position == 2


def test_get_foreign_keys_self_referencing() -> None:
    """Test get_foreign_keys includes self-referencing FKs."""
    mock_connector = MagicMock()
    mock_cursor = MagicMock()
    mock_connector.connection.cursor.return_value.__enter__.return_value = mock_cursor
    # Hierarchical table: categories.parent_id -> categories.id
    mock_cursor.fetchall.return_value = [
        ("fk_parent", "parent_id", "categories", "id", 1),
    ]

    extractor = MySQLExtractor()
    fks = extractor.get_foreign_keys(
        mock_connector, table="categories", schema="testdb"
    )

    assert len(fks) == 1
    assert fks[0].column_name == "parent_id"
    assert fks[0].referenced_table == "categories"
    assert fks[0].referenced_column == "id"
