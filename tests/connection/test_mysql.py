"""Tests for MySQL database connector."""

from unittest.mock import MagicMock, patch

import pytest
from mysql.connector import errorcode
from mysql.connector.errors import Error as MySQLError

from data_cataloger.connection.config import DatabaseConfig
from data_cataloger.connection.mysql import MySQLConnector, check_mysql_connection


class TestMySQLConnector:
    """Test suite for MySQLConnector."""

    @pytest.fixture
    def config(self) -> DatabaseConfig:
        """Create test database configuration."""
        return DatabaseConfig(
            db_type="mysql",
            host="localhost",
            port=3306,
            database="testdb",
            username="testuser",
            password="testpass",
            connection_timeout=10,
        )

    def test_connect_success(self, config: DatabaseConfig) -> None:
        """Test successful connection to MySQL."""
        connector = MySQLConnector(config)

        with patch("mysql.connector.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            connector.connect()

            mock_connect.assert_called_once_with(
                host="localhost",
                port=3306,
                database="testdb",
                user="testuser",
                password="testpass",
                connection_timeout=10,
            )
            assert connector.conn == mock_conn

    def test_test_connection_success(self, config: DatabaseConfig) -> None:
        """Test connection test succeeds when connection is alive."""
        connector = MySQLConnector(config)

        mock_conn = MagicMock()
        mock_conn.connected = True
        connector.conn = mock_conn

        result = connector.test_connection()

        assert result is True

    def test_test_connection_no_connection(self, config: DatabaseConfig) -> None:
        """Test connection test fails when not connected."""
        connector = MySQLConnector(config)

        result = connector.test_connection()

        assert result is False

    def test_test_connection_disconnected(self, config: DatabaseConfig) -> None:
        """Test connection test fails when connection is not active."""
        connector = MySQLConnector(config)

        mock_conn = MagicMock()
        mock_conn.connected = False
        connector.conn = mock_conn

        result = connector.test_connection()

        assert result is False

    def test_close_connection(self, config: DatabaseConfig) -> None:
        """Test closing database connection."""
        connector = MySQLConnector(config)

        mock_conn = MagicMock()
        connector.conn = mock_conn

        connector.close()

        mock_conn.close.assert_called_once()
        assert connector.conn is None

    def test_close_idempotent(self, config: DatabaseConfig) -> None:
        """Test close is idempotent (safe to call multiple times)."""
        connector = MySQLConnector(config)

        # Close when already None should not raise
        connector.close()
        connector.close()

        assert connector.conn is None


class TestTestMySQLConnection:
    """Test suite for check_mysql_connection function."""

    @pytest.fixture
    def config(self) -> DatabaseConfig:
        """Create test database configuration."""
        return DatabaseConfig(
            db_type="mysql",
            host="localhost",
            port=3306,
            database="testdb",
            username="testuser",
            password="testpass",
            connection_timeout=10,
        )

    def test_successful_connection(self, config: DatabaseConfig) -> None:
        """Test successful connection returns success result."""
        with patch("mysql.connector.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.connected = True
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            result = check_mysql_connection(config)

            assert result.success is True
            assert "Successfully connected" in result.message
            assert "testdb" in result.message
            assert result.error_type is None
            mock_cursor.execute.assert_called_once_with("SELECT 1")
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_connection_not_active(self, config: DatabaseConfig) -> None:
        """Test connection not active returns error."""
        with patch("mysql.connector.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_conn.connected = False
            mock_connect.return_value = mock_conn

            result = check_mysql_connection(config)

            assert result.success is False
            assert "not active" in result.message
            assert result.error_type == "CONNECTION_NOT_ACTIVE"
            mock_conn.close.assert_called_once()

    def test_auth_failed_error(self, config: DatabaseConfig) -> None:
        """Test authentication failure returns AUTH_FAILED error type."""
        with patch("mysql.connector.connect") as mock_connect:
            err = MySQLError("Access denied")
            err.errno = errorcode.ER_ACCESS_DENIED_ERROR
            mock_connect.side_effect = err

            result = check_mysql_connection(config)

            assert result.success is False
            assert "Authentication failed" in result.message
            assert "testuser" in result.message
            assert result.error_type == "AUTH_FAILED"

    def test_database_not_found_error(self, config: DatabaseConfig) -> None:
        """Test database not found returns DB_NOT_FOUND error type."""
        with patch("mysql.connector.connect") as mock_connect:
            err = MySQLError("Unknown database")
            err.errno = errorcode.ER_BAD_DB_ERROR
            mock_connect.side_effect = err

            result = check_mysql_connection(config)

            assert result.success is False
            assert "does not exist" in result.message
            assert "testdb" in result.message
            assert result.error_type == "DB_NOT_FOUND"

    def test_mysql_error_with_errno(self, config: DatabaseConfig) -> None:
        """Test MySQL error with error number returns MYSQL_ERROR_{errno}."""
        with patch("mysql.connector.connect") as mock_connect:
            err = MySQLError("Some MySQL error")
            err.errno = 2003  # Can't connect to MySQL server
            mock_connect.side_effect = err

            result = check_mysql_connection(config)

            assert result.success is False
            assert "MySQL error" in result.message
            assert result.error_type == "MYSQL_ERROR_2003"

    def test_mysql_error_without_errno(self, config: DatabaseConfig) -> None:
        """Test MySQL error without error number returns MYSQL_ERROR."""
        with patch("mysql.connector.connect") as mock_connect:
            err = MySQLError("Some MySQL error")
            err.errno = None
            mock_connect.side_effect = err

            result = check_mysql_connection(config)

            assert result.success is False
            assert "MySQL error" in result.message
            assert result.error_type == "MYSQL_ERROR"

    def test_unknown_error(self, config: DatabaseConfig) -> None:
        """Test unexpected error returns UNKNOWN_ERROR error type."""
        with patch("mysql.connector.connect") as mock_connect:
            mock_connect.side_effect = RuntimeError("unexpected error")

            result = check_mysql_connection(config)

            assert result.success is False
            assert "Unexpected error" in result.message
            assert result.error_type == "UNKNOWN_ERROR"
