"""Unit tests for graph API endpoints."""

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


def test_get_full_graph(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/graph returns full graph."""
    mock_repo.get_full_graph.return_value = {
        "nodes": [
            {"name": "users", "description": "Users", "sensitivity": "PII"},
            {"name": "orders", "description": "Orders", "sensitivity": "financial"},
        ],
        "edges": [
            {
                "source": "orders",
                "target": "users",
                "fk_column": "user_id",
                "referenced_column": "id",
            }
        ],
    }

    response = client.get("/api/graph")

    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1
    assert data["nodes"][0]["id"] == "users"
    assert data["edges"][0]["source"] == "orders"
    assert data["edges"][0]["target"] == "users"


def test_get_table_neighbors(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/graph/{table}/neighbors returns table with relationships."""
    mock_repo.get_table.side_effect = [
        CatalogEntry(
            table_name="orders",
            description="Orders",
            sensitivity="financial",
            example_queries=[],
        ),
        CatalogEntry(
            table_name="users",
            description="Users",
            sensitivity="PII",
            example_queries=[],
        ),
    ]
    mock_repo.get_relationships.return_value = [
        {
            "referenced_table": "users",
            "fk_column": "user_id",
            "referenced_column": "id",
            "constraint_name": "fk_orders_user",
        }
    ]

    response = client.get("/api/graph/orders/neighbors")

    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1

    node_ids = [n["id"] for n in data["nodes"]]
    assert "orders" in node_ids
    assert "users" in node_ids


def test_get_table_neighbors_not_found(
    client: TestClient, mock_repo: MagicMock
) -> None:
    """Test GET /api/graph/{table}/neighbors returns 404 for missing table."""
    mock_repo.get_table.return_value = None

    response = client.get("/api/graph/nonexistent/neighbors")

    assert response.status_code == 404


def test_graph_empty(client: TestClient, mock_repo: MagicMock) -> None:
    """Test GET /api/graph returns empty graph when no data."""
    mock_repo.get_full_graph.return_value = {"nodes": [], "edges": []}

    response = client.get("/api/graph")

    assert response.status_code == 200
    data = response.json()
    assert data["nodes"] == []
    assert data["edges"] == []
