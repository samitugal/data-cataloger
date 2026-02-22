"""Tests for database configuration models."""

import pytest
from pydantic import ValidationError

from data_cataloger.connection.config import DatabaseConfig


def test_valid_postgresql_config() -> None:
    """Test creating valid PostgreSQL configuration."""
    config = DatabaseConfig(
        db_type="postgresql",
        host="localhost",
        port=5432,
        database="testdb",
        username="testuser",
        password="testpass",
    )
    assert config.db_type == "postgresql"
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "testdb"
    assert config.username == "testuser"
    assert config.password == "testpass"
    assert config.ssl_enabled is False
    assert config.connection_timeout == 10


def test_valid_mysql_config() -> None:
    """Test creating valid MySQL configuration."""
    config = DatabaseConfig(
        db_type="mysql",
        host="db.example.com",
        port=3306,
        database="proddb",
        username="admin",
        password="secure123",
        ssl_enabled=True,
        connection_timeout=30,
    )
    assert config.db_type == "mysql"
    assert config.host == "db.example.com"
    assert config.port == 3306
    assert config.ssl_enabled is True
    assert config.connection_timeout == 30


@pytest.mark.parametrize(
    "port,should_pass",
    [
        (0, False),  # Below valid range
        (-1, False),  # Negative
        (1, True),  # Minimum valid
        (5432, True),  # PostgreSQL default
        (3306, True),  # MySQL default
        (65535, True),  # Maximum valid
        (65536, False),  # Above valid range
        (100000, False),  # Far above valid range
    ],
)
def test_port_validation(port: int, should_pass: bool) -> None:
    """Test port range validation."""
    if should_pass:
        config = DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=port,
            database="testdb",
            username="user",
            password="pass",
        )
        assert config.port == port
    else:
        with pytest.raises(ValidationError) as exc_info:
            DatabaseConfig(
                db_type="postgresql",
                host="localhost",
                port=port,
                database="testdb",
                username="user",
                password="pass",
            )
        assert "port" in str(exc_info.value).lower()


def test_missing_required_fields() -> None:
    """Test that missing required fields raise validation errors."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig()  # type: ignore[call-arg]
    error_msg = str(exc_info.value)
    assert "db_type" in error_msg
    assert "host" in error_msg
    assert "port" in error_msg
    assert "database" in error_msg
    assert "username" in error_msg
    assert "password" in error_msg


@pytest.mark.parametrize("field_name", ["host", "database", "username", "password"])
def test_empty_string_validation(field_name: str) -> None:
    """Test that empty strings are rejected for required string fields."""
    config_data = {
        "db_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "username": "user",
        "password": "pass",
    }
    config_data[field_name] = ""

    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(**config_data)
    assert field_name in str(exc_info.value).lower()


def test_invalid_db_type() -> None:
    """Test that invalid database types are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(
            db_type="oracle",  # type: ignore[arg-type]
            host="localhost",
            port=1521,
            database="testdb",
            username="user",
            password="pass",
        )
    assert "db_type" in str(exc_info.value).lower()


def test_negative_connection_timeout() -> None:
    """Test that negative connection timeout is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            connection_timeout=-5,
        )
    assert "connection_timeout" in str(exc_info.value).lower()


def test_zero_connection_timeout() -> None:
    """Test that zero connection timeout is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        DatabaseConfig(
            db_type="postgresql",
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            connection_timeout=0,
        )
    assert "connection_timeout" in str(exc_info.value).lower()
