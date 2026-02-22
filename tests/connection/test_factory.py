"""Tests for database connector factory."""

from unittest.mock import MagicMock, patch

import pytest

from data_cataloger.connection.config import DatabaseConfig
from data_cataloger.connection.factory import DatabaseFactory


class TestDatabaseFactory:
    """Test suite for DatabaseFactory."""

    def test_create_postgresql_connector(self) -> None:
        """Test factory creates PostgreSQLConnector for postgresql db_type."""
        config = DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass",
        )

        # Patch where the class is defined (postgres module), not where it's imported
        with patch(
            "data_cataloger.connection.postgres.PostgreSQLConnector"
        ) as mock_connector:
            mock_instance = MagicMock()
            mock_connector.return_value = mock_instance

            result = DatabaseFactory.create_connector(config)

            mock_connector.assert_called_once_with(config)
            assert result == mock_instance

    def test_create_mysql_connector(self) -> None:
        """Test factory creates MySQLConnector for mysql db_type."""
        config = DatabaseConfig(
            db_type="mysql",
            host="localhost",
            port=3306,
            database="testdb",
            username="testuser",
            password="testpass",
        )

        # Patch where the class is defined (mysql module), not where it's imported
        with patch("data_cataloger.connection.mysql.MySQLConnector") as mock_connector:
            mock_instance = MagicMock()
            mock_connector.return_value = mock_instance

            result = DatabaseFactory.create_connector(config)

            mock_connector.assert_called_once_with(config)
            assert result == mock_instance

    def test_create_connector_invalid_db_type(self) -> None:
        """Test factory raises ValueError for unsupported database type."""
        # Create config with invalid type by constructing directly
        # (bypassing Pydantic validation for testing purposes)
        config = DatabaseConfig.model_construct(
            db_type="oracle",  # type: ignore[arg-type]
            host="localhost",
            port=1521,
            database="testdb",
            username="testuser",
            password="testpass",
        )

        with pytest.raises(ValueError) as exc_info:
            DatabaseFactory.create_connector(config)

        assert "Unsupported database type: oracle" in str(exc_info.value)
        assert "postgresql, mysql" in str(exc_info.value)
