"""Tests for SchemaIntrospector integration."""

from unittest.mock import MagicMock, patch

import pytest

from data_cataloger.schema.introspector import SchemaAnalysisResult, SchemaIntrospector
from data_cataloger.schema.models import ColumnMetadata, ForeignKeyMetadata


@pytest.fixture
def mock_connector_postgresql() -> MagicMock:
    """Mock PostgreSQL connector."""
    mock = MagicMock()
    mock.config.db_type = "postgresql"
    mock.config.database = "testdb"
    return mock


@pytest.fixture
def mock_connector_mysql() -> MagicMock:
    """Mock MySQL connector."""
    mock = MagicMock()
    mock.config.db_type = "mysql"
    mock.config.database = "mydb"
    return mock


def test_introspect_postgresql_schema(mock_connector_postgresql: MagicMock) -> None:
    """Test introspection of PostgreSQL schema with dependencies."""
    # Mock extractor responses
    users_columns = [
        ColumnMetadata("id", "integer", False, 1, None),
        ColumnMetadata("email", "varchar", False, 2, None),
    ]
    posts_columns = [
        ColumnMetadata("id", "integer", False, 1, None),
        ColumnMetadata("user_id", "integer", False, 2, None),
        ColumnMetadata("title", "varchar", False, 3, None),
    ]
    posts_fks = [
        ForeignKeyMetadata("posts_user_fk", "user_id", "users", "id", 1),
    ]

    with patch(
        "data_cataloger.schema.introspector.PostgreSQLExtractor"
    ) as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        # Mock extraction methods
        mock_extractor.get_tables.return_value = ["users", "posts"]
        mock_extractor.get_columns.side_effect = [users_columns, posts_columns]
        mock_extractor.get_primary_keys.side_effect = [["id"], ["id"]]
        mock_extractor.get_foreign_keys.side_effect = [[], posts_fks]

        # Execute introspection
        introspector = SchemaIntrospector()
        result = introspector.introspect_schema(mock_connector_postgresql)

        # Verify result structure
        assert isinstance(result, SchemaAnalysisResult)
        assert len(result.tables) == 2
        assert result.circular_dependencies is None

        # Verify processing order (users before posts)
        assert result.processing_order == ["users", "posts"]

        # Verify tables metadata
        users_meta = next(t for t in result.tables if t.table_name == "users")
        assert users_meta.schema_name == "public"
        assert len(users_meta.columns) == 2
        assert users_meta.primary_keys == ("id",)
        assert users_meta.foreign_keys == ()

        posts_meta = next(t for t in result.tables if t.table_name == "posts")
        assert posts_meta.schema_name == "public"
        assert len(posts_meta.columns) == 3
        assert posts_meta.primary_keys == ("id",)
        assert len(posts_meta.foreign_keys) == 1

        # Verify extractor called with correct schema
        mock_extractor.get_tables.assert_called_once_with(
            mock_connector_postgresql, "public"
        )


def test_introspect_mysql_schema(mock_connector_mysql: MagicMock) -> None:
    """Test introspection of MySQL schema with database name as schema."""
    # Mock extractor responses
    products_columns = [
        ColumnMetadata("id", "int", False, 1, None),
        ColumnMetadata("name", "varchar", False, 2, None),
    ]
    orders_columns = [
        ColumnMetadata("id", "int", False, 1, None),
        ColumnMetadata("product_id", "int", False, 2, None),
    ]
    orders_fks = [
        ForeignKeyMetadata("orders_product_fk", "product_id", "products", "id", 1),
    ]

    with patch(
        "data_cataloger.schema.introspector.MySQLExtractor"
    ) as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        # Mock extraction methods
        mock_extractor.get_tables.return_value = ["products", "orders"]
        mock_extractor.get_columns.side_effect = [products_columns, orders_columns]
        mock_extractor.get_primary_keys.side_effect = [["id"], ["id"]]
        mock_extractor.get_foreign_keys.side_effect = [[], orders_fks]

        # Execute introspection
        introspector = SchemaIntrospector()
        result = introspector.introspect_schema(mock_connector_mysql)

        # Verify schema='mydb' used (database name from config)
        assert result.tables[0].schema_name == "mydb"
        assert result.tables[1].schema_name == "mydb"

        # Verify processing order
        assert result.processing_order == ["products", "orders"]

        # Verify extractor called with database name as schema
        mock_extractor.get_tables.assert_called_once_with(mock_connector_mysql, "mydb")


def test_circular_dependency_detected(mock_connector_postgresql: MagicMock) -> None:
    """Test detection of circular dependencies between tables."""
    # Mock tables A and B with mutual dependencies
    a_columns = [ColumnMetadata("id", "integer", False, 1, None)]
    b_columns = [ColumnMetadata("id", "integer", False, 1, None)]
    a_fks = [ForeignKeyMetadata("a_b_fk", "b_id", "b", "id", 1)]
    b_fks = [ForeignKeyMetadata("b_a_fk", "a_id", "a", "id", 1)]

    with patch(
        "data_cataloger.schema.introspector.PostgreSQLExtractor"
    ) as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_tables.return_value = ["a", "b"]
        mock_extractor.get_columns.side_effect = [a_columns, b_columns]
        mock_extractor.get_primary_keys.side_effect = [["id"], ["id"]]
        mock_extractor.get_foreign_keys.side_effect = [a_fks, b_fks]

        # Execute introspection
        introspector = SchemaIntrospector()
        result = introspector.introspect_schema(mock_connector_postgresql)

        # Verify circular dependency detected
        assert result.circular_dependencies is not None
        assert len(result.circular_dependencies) > 0
        assert set(result.circular_dependencies) == {"a", "b"}

        # Verify processing order is empty when cycle detected
        assert result.processing_order == []


def test_self_referencing_table(mock_connector_postgresql: MagicMock) -> None:
    """Test self-referencing table is not treated as cycle."""
    # Mock categories table with parent_id FK to itself
    categories_columns = [
        ColumnMetadata("id", "integer", False, 1, None),
        ColumnMetadata("parent_id", "integer", True, 2, None),
    ]
    categories_fks = [
        ForeignKeyMetadata("categories_parent_fk", "parent_id", "categories", "id", 1),
    ]

    with patch(
        "data_cataloger.schema.introspector.PostgreSQLExtractor"
    ) as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_tables.return_value = ["categories"]
        mock_extractor.get_columns.return_value = categories_columns
        mock_extractor.get_primary_keys.return_value = ["id"]
        mock_extractor.get_foreign_keys.return_value = categories_fks

        # Execute introspection
        introspector = SchemaIntrospector()
        result = introspector.introspect_schema(mock_connector_postgresql)

        # Verify self-reference is NOT treated as circular dependency
        assert result.circular_dependencies is None
        assert result.processing_order == ["categories"]


def test_complex_dependency_graph(mock_connector_postgresql: MagicMock) -> None:
    """Test multi-level dependency graph ordering."""
    # users -> posts -> comments -> likes (linear chain)
    with patch(
        "data_cataloger.schema.introspector.PostgreSQLExtractor"
    ) as mock_extractor_class:
        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_tables.return_value = [
            "users",
            "posts",
            "comments",
            "likes",
        ]
        mock_extractor.get_columns.return_value = [
            ColumnMetadata("id", "integer", False, 1, None)
        ]
        mock_extractor.get_primary_keys.return_value = ["id"]

        # Define FKs for each table
        mock_extractor.get_foreign_keys.side_effect = [
            [],  # users: no FKs
            [ForeignKeyMetadata("posts_user_fk", "user_id", "users", "id", 1)],
            [ForeignKeyMetadata("comments_post_fk", "post_id", "posts", "id", 1)],
            [ForeignKeyMetadata("likes_comment_fk", "comment_id", "comments", "id", 1)],
        ]

        # Execute introspection
        introspector = SchemaIntrospector()
        result = introspector.introspect_schema(mock_connector_postgresql)

        # Verify processing order respects all dependencies
        assert result.circular_dependencies is None
        processing_order = result.processing_order

        # Verify dependency order: users before posts, posts before comments, etc.
        assert processing_order.index("users") < processing_order.index("posts")
        assert processing_order.index("posts") < processing_order.index("comments")
        assert processing_order.index("comments") < processing_order.index("likes")


def test_unsupported_database_type(mock_connector_postgresql: MagicMock) -> None:
    """Test error handling for unsupported database type."""
    # Mock connector with unsupported database type
    mock_connector_postgresql.config.db_type = "oracle"

    introspector = SchemaIntrospector()

    # Verify ValueError raised
    with pytest.raises(ValueError) as exc_info:
        introspector.introspect_schema(mock_connector_postgresql)

    assert "Unsupported database type: oracle" in str(exc_info.value)
