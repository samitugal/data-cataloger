"""Unit tests for GraphRepository with mocked Neo4j driver."""

from unittest.mock import MagicMock

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.storage.repository import GraphRepository


def _create_mock_record(data: dict) -> MagicMock:
    """Create a mock Neo4j Record with dict-like access."""
    record = MagicMock()
    record.__getitem__ = lambda self, key: data[key]
    record.keys.return_value = data.keys()
    return record


def _create_dict_record(data: dict) -> dict:
    """Create a dict that acts like a Neo4j Record for dict() conversion.

    The repository uses dict(record) which iterates over the record.
    For simplicity, we just return the dict directly since dict(dict) = dict.
    """
    return data


def test_get_table_found() -> None:
    """Mock driver returns one record, verify CatalogEntry returned."""
    # Arrange
    mock_driver = MagicMock()
    record_data = {
        "name": "users",
        "description": "Customer accounts",
        "sensitivity": "PII",
        "example_queries": ["SELECT * FROM users"],
    }
    mock_record = _create_mock_record(record_data)
    mock_driver.execute_query.return_value = ([mock_record], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_table("users", "production_db")

    # Assert
    assert result is not None
    assert isinstance(result, CatalogEntry)
    assert result.table_name == "users"
    assert result.description == "Customer accounts"
    assert result.sensitivity == "PII"
    assert result.example_queries == ["SELECT * FROM users"]


def test_get_table_not_found() -> None:
    """Mock driver returns empty list, verify returns None."""
    # Arrange
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = ([], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_table("nonexistent", "production_db")

    # Assert
    assert result is None


def test_list_tables() -> None:
    """Mock driver returning 3 records, verify returns list of 3 CatalogEntry."""
    # Arrange
    mock_driver = MagicMock()
    records = [
        _create_mock_record({
            "name": "orders",
            "description": "Customer orders",
            "sensitivity": "financial",
            "example_queries": ["SELECT * FROM orders"],
        }),
        _create_mock_record({
            "name": "products",
            "description": "Product catalog",
            "sensitivity": "public",
            "example_queries": ["SELECT * FROM products"],
        }),
        _create_mock_record({
            "name": "users",
            "description": "Customer accounts",
            "sensitivity": "PII",
            "example_queries": ["SELECT * FROM users"],
        }),
    ]
    mock_driver.execute_query.return_value = (records, None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.list_tables("production_db")

    # Assert
    assert len(result) == 3
    assert all(isinstance(entry, CatalogEntry) for entry in result)
    table_names = [entry.table_name for entry in result]
    assert "orders" in table_names
    assert "products" in table_names
    assert "users" in table_names


def test_get_relationships() -> None:
    """Mock driver returning 2 FK records, verify returns list of 2 dicts."""
    # Arrange
    mock_driver = MagicMock()

    # Create mock records that support dict() conversion
    record1_data = {
        "referenced_table": "users",
        "fk_column": "user_id",
        "referenced_column": "id",
        "constraint_name": "fk_orders_user",
    }
    record2_data = {
        "referenced_table": "products",
        "fk_column": "product_id",
        "referenced_column": "id",
        "constraint_name": "fk_orders_product",
    }

    record1 = _create_dict_record(record1_data)
    record2 = _create_dict_record(record2_data)

    mock_driver.execute_query.return_value = ([record1, record2], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_relationships("orders", "production_db")

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, dict) for r in result)

    # Verify FK metadata present
    ref_tables = [r["referenced_table"] for r in result]
    assert "users" in ref_tables
    assert "products" in ref_tables


def test_get_full_graph() -> None:
    """Mock driver returning nodes and edges, verify dict with nodes and edges."""
    # Arrange
    mock_driver = MagicMock()

    # Node records (use dict directly for dict() conversion)
    node1_data = {"name": "users", "description": "Accounts", "sensitivity": "PII"}
    node2_data = {"name": "orders", "description": "Orders", "sensitivity": "financial"}

    # Edge records
    edge1_data = {
        "source": "orders",
        "target": "users",
        "fk_column": "user_id",
        "referenced_column": "id",
    }

    # First call returns nodes, second call returns edges
    mock_driver.execute_query.side_effect = [
        ([node1_data, node2_data], None, None),
        ([edge1_data], None, None),
    ]

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_full_graph("production_db")

    # Assert
    assert "nodes" in result
    assert "edges" in result
    assert len(result["nodes"]) == 2
    assert len(result["edges"]) == 1

    # Verify execute_query called twice (nodes + edges)
    assert mock_driver.execute_query.call_count == 2


def test_search_by_sensitivity() -> None:
    """Mock driver, verify correct WHERE clause in query."""
    # Arrange
    mock_driver = MagicMock()
    record = _create_mock_record({
        "name": "users",
        "description": "Customer accounts",
        "sensitivity": "PII",
        "example_queries": ["SELECT * FROM users"],
    })
    mock_driver.execute_query.return_value = ([record], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.search_by_sensitivity("PII", "production_db")

    # Assert
    assert len(result) == 1
    assert result[0].sensitivity == "PII"

    # Verify query contains sensitivity filter
    call_args = mock_driver.execute_query.call_args
    query = call_args[0][0]
    assert "sensitivity = $sensitivity" in query
    assert call_args[1]["sensitivity"] == "PII"


def test_search_by_keyword() -> None:
    """Mock driver, verify toLower/CONTAINS pattern in query."""
    # Arrange
    mock_driver = MagicMock()
    record = _create_mock_record({
        "name": "users",
        "description": "Customer accounts and profiles",
        "sensitivity": "PII",
        "example_queries": ["SELECT * FROM users"],
    })
    mock_driver.execute_query.return_value = ([record], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.search_by_keyword("customer", "production_db")

    # Assert
    assert len(result) == 1
    assert "Customer" in result[0].description

    # Verify query contains case-insensitive CONTAINS pattern
    call_args = mock_driver.execute_query.call_args
    query = call_args[0][0]
    assert "toLower" in query
    assert "CONTAINS" in query
    assert call_args[1]["keyword"] == "customer"


def test_list_tables_empty() -> None:
    """Verify empty list returned when no tables exist."""
    # Arrange
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = ([], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.list_tables("empty_db")

    # Assert
    assert result == []


def test_get_relationships_empty() -> None:
    """Verify empty list returned when table has no FKs."""
    # Arrange
    mock_driver = MagicMock()
    mock_driver.execute_query.return_value = ([], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_relationships("standalone_table", "production_db")

    # Assert
    assert result == []


def test_to_catalog_entry_handles_none_example_queries() -> None:
    """Verify _to_catalog_entry handles None example_queries (stub nodes)."""
    # Arrange
    mock_driver = MagicMock()
    record = _create_mock_record({
        "name": "stub_table",
        "description": "Some description",
        "sensitivity": "internal",
        "example_queries": None,  # Stub node may have None
    })
    mock_driver.execute_query.return_value = ([record], None, None)

    repo = GraphRepository(mock_driver, database="neo4j")

    # Act
    result = repo.get_table("stub_table", "production_db")

    # Assert
    assert result is not None
    assert result.example_queries == []  # None converted to empty list
