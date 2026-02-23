"""Integration tests for CatalogingAgent orchestrator with mocked LLM."""

from unittest.mock import Mock

import pytest

from data_cataloger.cataloging.agent import CatalogingAgent
from data_cataloger.cataloging.models import CatalogEntry, TableCatalog
from data_cataloger.schema.introspector import SchemaAnalysisResult
from data_cataloger.schema.models import (
    ColumnMetadata,
    ForeignKeyMetadata,
    TableMetadata,
)


def test_catalog_database_single_table() -> None:
    """Test cataloging a single table with no foreign keys."""
    # Create schema result with one simple table
    users_table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(
            ColumnMetadata("id", "integer", False, 1),
            ColumnMetadata("email", "varchar", False, 2),
        ),
        primary_keys=("id",),
        foreign_keys=(),
    )
    schema_result = SchemaAnalysisResult(
        tables=[users_table], processing_order=["users"], circular_dependencies=None
    )

    # Mock client to return TableCatalog
    mock_client = Mock()
    mock_client.analyze_table.return_value = TableCatalog(
        description="User account information",
        sensitivity="PII",
        example_queries=["SELECT * FROM users WHERE id = 1"],
    )

    # Catalog database
    agent = CatalogingAgent(client=mock_client)
    catalog = agent.catalog_database(schema_result)

    # Verify results
    assert len(catalog) == 1
    assert "users" in catalog
    assert isinstance(catalog["users"], CatalogEntry)
    assert catalog["users"].description == "User account information"
    assert catalog["users"].sensitivity == "PII"

    # Verify analyze_table called once with empty parent context
    assert mock_client.analyze_table.call_count == 1
    call_args = mock_client.analyze_table.call_args
    messages = call_args[0][0]
    # Check that user prompt doesn't contain "Referenced Tables Context"
    user_content = messages[1]["content"]
    assert "Referenced Tables Context" not in user_content


def test_catalog_database_dependency_chain() -> None:
    """Test cataloging tables in dependency order with context accumulation."""
    # Create 3 tables: users -> posts -> comments
    users_table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(ColumnMetadata("id", "integer", False, 1),),
        primary_keys=("id",),
        foreign_keys=(),
    )
    posts_table = TableMetadata(
        schema_name="public",
        table_name="posts",
        columns=(
            ColumnMetadata("id", "integer", False, 1),
            ColumnMetadata("user_id", "integer", False, 2),
        ),
        primary_keys=("id",),
        foreign_keys=(
            ForeignKeyMetadata("fk_posts_user", "user_id", "users", "id", 1),
        ),
    )
    comments_table = TableMetadata(
        schema_name="public",
        table_name="comments",
        columns=(
            ColumnMetadata("id", "integer", False, 1),
            ColumnMetadata("post_id", "integer", False, 2),
        ),
        primary_keys=("id",),
        foreign_keys=(
            ForeignKeyMetadata("fk_comments_post", "post_id", "posts", "id", 1),
        ),
    )

    schema_result = SchemaAnalysisResult(
        tables=[users_table, posts_table, comments_table],
        processing_order=["users", "posts", "comments"],
        circular_dependencies=None,
    )

    # Mock client to return different descriptions for each table
    mock_client = Mock()
    mock_client.analyze_table.side_effect = [
        TableCatalog(
            description="User accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        ),
        TableCatalog(
            description="Blog posts",
            sensitivity="public",
            example_queries=["SELECT * FROM posts"],
        ),
        TableCatalog(
            description="Post comments",
            sensitivity="public",
            example_queries=["SELECT * FROM comments"],
        ),
    ]

    # Catalog database
    agent = CatalogingAgent(client=mock_client)
    catalog = agent.catalog_database(schema_result)

    # Verify all tables cataloged
    assert len(catalog) == 3
    assert catalog["users"].description == "User accounts"
    assert catalog["posts"].description == "Blog posts"
    assert catalog["comments"].description == "Post comments"

    # Verify analyze_table called 3 times
    assert mock_client.analyze_table.call_count == 3

    # Verify 1st call (users) has empty parent context
    call_1_messages = mock_client.analyze_table.call_args_list[0][0][0]
    assert "Referenced Tables Context" not in call_1_messages[1]["content"]

    # Verify 2nd call (posts) has users in parent context
    call_2_messages = mock_client.analyze_table.call_args_list[1][0][0]
    assert "Referenced Tables Context" in call_2_messages[1]["content"]
    assert "users: User accounts" in call_2_messages[1]["content"]

    # Verify 3rd call (comments) has posts in parent context
    call_3_messages = mock_client.analyze_table.call_args_list[2][0][0]
    assert "Referenced Tables Context" in call_3_messages[1]["content"]
    assert "posts: Blog posts" in call_3_messages[1]["content"]


def test_catalog_database_multiple_parents() -> None:
    """Test table with multiple foreign keys receives context from all parents."""
    # Create tables: orders, products, order_items (references both)
    orders_table = TableMetadata(
        schema_name="public",
        table_name="orders",
        columns=(ColumnMetadata("id", "integer", False, 1),),
        primary_keys=("id",),
        foreign_keys=(),
    )
    products_table = TableMetadata(
        schema_name="public",
        table_name="products",
        columns=(ColumnMetadata("id", "integer", False, 1),),
        primary_keys=("id",),
        foreign_keys=(),
    )
    order_items_table = TableMetadata(
        schema_name="public",
        table_name="order_items",
        columns=(
            ColumnMetadata("order_id", "integer", False, 1),
            ColumnMetadata("product_id", "integer", False, 2),
        ),
        primary_keys=("order_id", "product_id"),
        foreign_keys=(
            ForeignKeyMetadata("fk_order", "order_id", "orders", "id", 1),
            ForeignKeyMetadata("fk_product", "product_id", "products", "id", 1),
        ),
    )

    schema_result = SchemaAnalysisResult(
        tables=[orders_table, products_table, order_items_table],
        processing_order=["orders", "products", "order_items"],
        circular_dependencies=None,
    )

    # Mock client
    mock_client = Mock()
    mock_client.analyze_table.side_effect = [
        TableCatalog(
            description="Customer orders",
            sensitivity="internal",
            example_queries=["SELECT * FROM orders"],
        ),
        TableCatalog(
            description="Product catalog",
            sensitivity="public",
            example_queries=["SELECT * FROM products"],
        ),
        TableCatalog(
            description="Order line items",
            sensitivity="internal",
            example_queries=["SELECT * FROM order_items"],
        ),
    ]

    # Catalog database
    agent = CatalogingAgent(client=mock_client)
    agent.catalog_database(schema_result)

    # Verify order_items has both parents in context
    call_3_messages = mock_client.analyze_table.call_args_list[2][0][0]
    user_content = call_3_messages[1]["content"]
    assert "Referenced Tables Context" in user_content
    assert "orders: Customer orders" in user_content
    assert "products: Product catalog" in user_content


def test_catalog_database_circular_dependency() -> None:
    """Test that circular dependencies raise ValueError."""
    # Create schema result with circular dependency
    schema_result = SchemaAnalysisResult(
        tables=[],
        processing_order=[],
        circular_dependencies=["table_a", "table_b"],
    )

    # Attempt to catalog
    agent = CatalogingAgent()
    with pytest.raises(ValueError) as exc_info:
        agent.catalog_database(schema_result)

    # Verify error message mentions circular dependencies
    assert "circular dependencies" in str(exc_info.value).lower()
    assert "table_a" in str(exc_info.value)
    assert "table_b" in str(exc_info.value)


def test_catalog_database_missing_parent() -> None:
    """Test that agent handles missing parents gracefully (no crash)."""
    # Create scenario where child appears in processing_order but parent
    # isn't cataloged yet (shouldn't happen with SchemaIntrospector,
    # but test defensive behavior)
    posts_table = TableMetadata(
        schema_name="public",
        table_name="posts",
        columns=(ColumnMetadata("user_id", "integer", False, 1),),
        primary_keys=(),
        foreign_keys=(ForeignKeyMetadata("fk_user", "user_id", "users", "id", 1),),
    )

    # Only posts in the schema, but it references users
    schema_result = SchemaAnalysisResult(
        tables=[posts_table], processing_order=["posts"], circular_dependencies=None
    )

    # Mock client
    mock_client = Mock()
    mock_client.analyze_table.return_value = TableCatalog(
        description="Blog posts",
        sensitivity="public",
        example_queries=["SELECT * FROM posts"],
    )

    # Catalog database - should not crash
    agent = CatalogingAgent(client=mock_client)
    catalog = agent.catalog_database(schema_result)

    # Verify posts cataloged successfully
    assert len(catalog) == 1
    assert "posts" in catalog

    # Verify parent context was empty (no "users" reference)
    call_messages = mock_client.analyze_table.call_args[0][0]
    assert "Referenced Tables Context" not in call_messages[1]["content"]


def test_catalog_table_converts_pydantic_to_dataclass() -> None:
    """Test that _catalog_table converts TableCatalog to CatalogEntry."""
    # Create table metadata
    table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(ColumnMetadata("id", "integer", False, 1),),
        primary_keys=("id",),
        foreign_keys=(),
    )

    # Mock client
    mock_client = Mock()
    mock_client.analyze_table.return_value = TableCatalog(
        description="User accounts",
        sensitivity="PII",
        example_queries=[
            "SELECT * FROM users WHERE id = 1",
            "SELECT count(*) FROM users",
        ],
    )

    # Call _catalog_table directly
    agent = CatalogingAgent(client=mock_client)
    entry = agent._catalog_table(table, [])

    # Verify returns CatalogEntry (frozen dataclass)
    assert isinstance(entry, CatalogEntry)
    assert entry.table_name == "users"
    assert entry.description == "User accounts"
    assert entry.sensitivity == "PII"
    assert len(entry.example_queries) == 2

    # Verify CatalogEntry is immutable (frozen)
    with pytest.raises(AttributeError):
        entry.description = "New description"  # type: ignore[misc]
