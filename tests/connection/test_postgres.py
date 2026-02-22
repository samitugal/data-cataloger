"""Tests for PostgreSQL database connector."""

from unittest.mock import MagicMock, patch

import psycopg
import pytest

from data_cataloger.connection.config import DatabaseConfig
from data_cataloger.connection.postgres import (
    PostgreSQLConnector,
    check_postgresql_connection,
)


class TestPostgreSQLConnector:
    """Test suite for PostgreSQLConnector."""

    @pytest.fixture
    def config(self) -> DatabaseConfig:
        """Create test database configuration."""
        return DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass",
            connection_timeout=10,
        )

    def test_connect_success(self, config: DatabaseConfig) -> None:
        """Test successful connection to PostgreSQL."""
        connector = PostgreSQLConnector(config)

        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            connector.connect()

            mock_connect.assert_called_once_with(
                host="localhost",
                port=5432,
                dbname="testdb",
                user="testuser",
                password="testpass",
                connect_timeout=10,
            )
            assert connector.conn == mock_conn

    def test_test_connection_success(self, config: DatabaseConfig) -> None:
        """Test connection test succeeds when connection is alive."""
        connector = PostgreSQLConnector(config)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        connector.conn = mock_conn

        result = connector.test_connection()

        assert result is True
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_test_connection_no_connection(self, config: DatabaseConfig) -> None:
        """Test connection test fails when not connected."""
        connector = PostgreSQLConnector(config)

        result = connector.test_connection()

        assert result is False

    def test_test_connection_query_fails(self, config: DatabaseConfig) -> None:
        """Test connection test fails when query execution fails."""
        connector = PostgreSQLConnector(config)

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg.OperationalError("Connection lost")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        connector.conn = mock_conn

        result = connector.test_connection()

        assert result is False

    def test_close_connection(self, config: DatabaseConfig) -> None:
        """Test closing database connection."""
        connector = PostgreSQLConnector(config)

        mock_conn = MagicMock()
        connector.conn = mock_conn

        connector.close()

        mock_conn.close.assert_called_once()
        assert connector.conn is None

    def test_close_idempotent(self, config: DatabaseConfig) -> None:
        """Test close is idempotent (safe to call multiple times)."""
        connector = PostgreSQLConnector(config)

        # Close when already None should not raise
        connector.close()
        connector.close()

        assert connector.conn is None


class TestTestPostgreSQLConnection:
    """Test suite for check_postgresql_connection function."""

    @pytest.fixture
    def config(self) -> DatabaseConfig:
        """Create test database configuration."""
        return DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass",
            connection_timeout=10,
        )

    def test_successful_connection(self, config: DatabaseConfig) -> None:
        """Test successful connection returns success result."""
        with patch("psycopg.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
            mock_conn.__enter__.return_value = mock_conn
            mock_connect.return_value = mock_conn

            result = check_postgresql_connection(config)

            assert result.success is True
            assert "Successfully connected" in result.message
            assert "testdb" in result.message
            assert result.error_type is None
            mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_auth_failed_error(self, config: DatabaseConfig) -> None:
        """Test authentication failure returns AUTH_FAILED error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = psycopg.OperationalError(
                "password authentication failed for user"
            )

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "Authentication failed" in result.message
            assert "testuser" in result.message
            assert result.error_type == "AUTH_FAILED"

    def test_connection_refused_error(self, config: DatabaseConfig) -> None:
        """Test connection refused returns CONNECTION_REFUSED error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = psycopg.OperationalError(
                "could not connect to server"
            )

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "Could not connect" in result.message
            assert "localhost:5432" in result.message
            assert result.error_type == "CONNECTION_REFUSED"

    def test_database_not_found_error(self, config: DatabaseConfig) -> None:
        """Test database not found returns DB_NOT_FOUND error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = psycopg.OperationalError(
                'database "testdb" does not exist'
            )

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "does not exist" in result.message
            assert "testdb" in result.message
            assert result.error_type == "DB_NOT_FOUND"

    def test_timeout_error(self, config: DatabaseConfig) -> None:
        """Test connection timeout returns TIMEOUT error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = TimeoutError("connection timeout")

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "timed out" in result.message
            assert "10 seconds" in result.message
            assert result.error_type == "TIMEOUT"

    def test_interface_error(self, config: DatabaseConfig) -> None:
        """Test interface error returns INTERFACE_ERROR error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = psycopg.InterfaceError("interface error")

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "interface error" in result.message
            assert result.error_type == "INTERFACE_ERROR"

    def test_generic_operational_error(self, config: DatabaseConfig) -> None:
        """Test generic operational error returns OPERATIONAL_ERROR error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = psycopg.OperationalError(
                "some other operational error"
            )

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "operational error" in result.message
            assert result.error_type == "OPERATIONAL_ERROR"

    def test_unknown_error(self, config: DatabaseConfig) -> None:
        """Test unexpected error returns UNKNOWN_ERROR error type."""
        with patch("psycopg.connect") as mock_connect:
            mock_connect.side_effect = RuntimeError("unexpected error")

            result = check_postgresql_connection(config)

            assert result.success is False
            assert "Unexpected error" in result.message
            assert result.error_type == "UNKNOWN_ERROR"
