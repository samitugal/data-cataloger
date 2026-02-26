"""Unit tests for table API endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.web.app import create_app
from data_cataloger.web.dependencies import get_database_name, get_graph_repository


@pytest.fixture
def mock_repo() -> MagicMock:
    """Create mock GraphRepository."""
    return MagicMock()


@pytest.fixture
def client(mock_repo: MagicMock) -> TestClient:
    """Create test client with mocked dependencies."""
    app = create_app()
    app.dependency_overrides[get_graph_repository] = lambda: mock_repo
    app.dependency_overrides[get_database_name] = lambda: "test_db"
    return TestClient(app)


def test_list_tables(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/tables returns list of tables."""
    mock_repo.list_tables.return_value = [
        CatalogEntry(
            table_name="users",
            description="User accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        ),
        CatalogEntry(
            table_name="orders",
            description="Customer orders",
            sensitivity="financial",
            example_queries=["SELECT * FROM orders"],
        ),
    ]

    response = client.get("/api/tables")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["tables"]) == 2
    assert data["tables"][0]["name"] == "users"


def test_get_table_found(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/tables/{name} returns table details."""
    mock_repo.get_table.return_value = CatalogEntry(
        table_name="users",
        description="User accounts",
        sensitivity="PII",
        example_queries=["SELECT * FROM users"],
    )

    response = client.get("/api/tables/users")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "users"
    assert data["sensitivity"] == "PII"


def test_get_table_not_found(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/tables/{name} returns 404 for missing table."""
    mock_repo.get_table.return_value = None

    response = client.get("/api/tables/nonexistent")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_search_tables(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/tables/search?q=keyword returns filtered results."""
    mock_repo.search_by_keyword.return_value = [
        CatalogEntry(
            table_name="users",
            description="User accounts",
            sensitivity="PII",
            example_queries=[],
        ),
    ]

    response = client.get("/api/tables/search?q=user")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    mock_repo.search_by_keyword.assert_called_once_with("user", "test_db")


def test_filter_by_sensitivity(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/tables/sensitivity/{level} returns filtered results."""
    mock_repo.search_by_sensitivity.return_value = [
        CatalogEntry(
            table_name="users",
            description="User accounts",
            sensitivity="PII",
            example_queries=[],
        ),
    ]

    response = client.get("/api/tables/sensitivity/PII")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    mock_repo.search_by_sensitivity.assert_called_once_with("PII", "test_db")
