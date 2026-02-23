"""Unit tests for Neo4jWriter with mocked Neo4j driver."""

from unittest.mock import MagicMock

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.schema.models import ForeignKeyMetadata
from data_cataloger.storage.writer import Neo4jWriter


def test_write_entry_creates_table_and_database_nodes() -> None:
    """Verify execute_query called with correct MERGE Cypher."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    entry = CatalogEntry(
        table_name="users",
        description="Customer accounts",
        sensitivity="PII",
        example_queries=["SELECT * FROM users WHERE id = ?"],
    )

    # Act
    writer.write_entry(entry, "production_db", "postgresql")

    # Assert
    mock_driver.execute_query.assert_called_once()
    call_args = mock_driver.execute_query.call_args

    # Verify query contains MERGE patterns for Database and Table
    query = call_args[0][0]
    assert "MERGE (db:Database" in query
    assert "MERGE (t:Table" in query
    assert "MERGE (db)-[:HAS_TABLE]->(t)" in query

    # Verify parameters
    kwargs = call_args[1]
    assert kwargs["database_name"] == "production_db"
    assert kwargs["database_type"] == "postgresql"
    assert kwargs["table_name"] == "users"
    assert kwargs["description"] == "Customer accounts"
    assert kwargs["sensitivity"] == "PII"
    assert kwargs["example_queries"] == ["SELECT * FROM users WHERE id = ?"]
    assert kwargs["database_"] == "neo4j"


def test_write_entry_upsert_same_table() -> None:
    """Call write_entry twice with same table, verify MERGE pattern used."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    entry1 = CatalogEntry(
        table_name="users",
        description="Original description",
        sensitivity="PII",
        example_queries=["SELECT * FROM users"],
    )
    entry2 = CatalogEntry(
        table_name="users",
        description="Updated description",
        sensitivity="internal",
        example_queries=["SELECT * FROM users WHERE active = true"],
    )

    # Act
    writer.write_entry(entry1, "production_db")
    writer.write_entry(entry2, "production_db")

    # Assert - both calls use MERGE (upsert behavior)
    assert mock_driver.execute_query.call_count == 2

    for call in mock_driver.execute_query.call_args_list:
        query = call[0][0]
        assert "MERGE" in query
        assert "CREATE" not in query or "ON CREATE SET" in query


def test_write_relationships_creates_edges() -> None:
    """Verify MERGE pattern with source, target nodes and REFERENCES_VIA edge."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    fks = (
        ForeignKeyMetadata(
            constraint_name="fk_orders_user",
            column_name="user_id",
            referenced_table="users",
            referenced_column="id",
            ordinal_position=1,
        ),
    )

    # Act
    writer.write_relationships("orders", fks, "production_db")

    # Assert
    mock_driver.execute_query.assert_called_once()
    call_args = mock_driver.execute_query.call_args

    # Verify query contains MERGE patterns for nodes and edge
    query = call_args[0][0]
    assert "MERGE (source:Table" in query
    assert "MERGE (target:Table" in query
    assert "REFERENCES_VIA" in query

    # Verify parameters include FK metadata
    kwargs = call_args[1]
    assert kwargs["source_table"] == "orders"
    assert kwargs["target_table"] == "users"
    assert kwargs["database"] == "production_db"
    assert kwargs["fk_column"] == "user_id"
    assert kwargs["referenced_column"] == "id"
    assert kwargs["constraint_name"] == "fk_orders_user"


def test_write_relationships_stub_nodes() -> None:
    """Verify write_relationships MERGEs target Table node even if not yet cataloged."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    # FK references a table that hasn't been written via write_entry yet
    fks = (
        ForeignKeyMetadata(
            constraint_name="fk_posts_author",
            column_name="author_id",
            referenced_table="authors",  # Not yet cataloged
            referenced_column="id",
            ordinal_position=1,
        ),
    )

    # Act
    writer.write_relationships("posts", fks, "blog_db")

    # Assert - MERGE creates stub node for uncataloged target
    call_args = mock_driver.execute_query.call_args
    query = call_args[0][0]

    # Both source and target use MERGE (creates stub if not exists)
    assert "MERGE (source:Table" in query
    assert "MERGE (target:Table" in query
    assert call_args[1]["target_table"] == "authors"


def test_write_relationships_empty_fks() -> None:
    """Verify write_relationships with empty tuple does nothing."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    # Act
    writer.write_relationships("users", (), "production_db")

    # Assert - no execute_query calls for empty FK tuple
    # verify_connectivity is called in __init__, but execute_query should not be called
    assert mock_driver.execute_query.call_count == 0


def test_verify_connectivity_on_init() -> None:
    """Verify that Neo4jWriter constructor calls driver.verify_connectivity."""
    # Arrange
    mock_driver = MagicMock()

    # Act
    Neo4jWriter(mock_driver, database="neo4j")

    # Assert
    mock_driver.verify_connectivity.assert_called_once()


def test_context_manager() -> None:
    """Verify __enter__ returns self and __exit__ calls driver.close()."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    # Act & Assert - __enter__
    result = writer.__enter__()
    assert result is writer

    # Act & Assert - __exit__
    writer.__exit__(None, None, None)
    mock_driver.close.assert_called_once()


def test_context_manager_with_statement() -> None:
    """Verify context manager works with with statement."""
    # Arrange
    mock_driver = MagicMock()

    # Act
    with Neo4jWriter(mock_driver, database="neo4j") as writer:
        assert isinstance(writer, Neo4jWriter)

    # Assert - driver.close() called on exit
    mock_driver.close.assert_called_once()


def test_write_relationships_multiple_fks() -> None:
    """Verify write_relationships handles multiple foreign keys."""
    # Arrange
    mock_driver = MagicMock()
    writer = Neo4jWriter(mock_driver, database="neo4j")

    fks = (
        ForeignKeyMetadata(
            constraint_name="fk_order_items_order",
            column_name="order_id",
            referenced_table="orders",
            referenced_column="id",
            ordinal_position=1,
        ),
        ForeignKeyMetadata(
            constraint_name="fk_order_items_product",
            column_name="product_id",
            referenced_table="products",
            referenced_column="id",
            ordinal_position=1,
        ),
    )

    # Act
    writer.write_relationships("order_items", fks, "ecommerce_db")

    # Assert - execute_query called once per FK
    assert mock_driver.execute_query.call_count == 2

    # Verify both FKs were written
    calls = mock_driver.execute_query.call_args_list
    target_tables = [call[1]["target_table"] for call in calls]
    assert "orders" in target_tables
    assert "products" in target_tables
