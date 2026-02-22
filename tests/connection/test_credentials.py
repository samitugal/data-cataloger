"""Tests for credential management."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from data_cataloger.connection.config import DatabaseConfig
from data_cataloger.connection.credentials import CredentialManager


@pytest.fixture
def credential_manager() -> CredentialManager:
    """Create a credential manager for testing."""
    return CredentialManager(service_name="TestService")


def test_store_and_get_password(credential_manager: CredentialManager) -> None:
    """Test storing and retrieving password from keyring."""
    with (
        patch("keyring.set_password") as mock_set,
        patch("keyring.get_password") as mock_get,
    ):
        mock_get.return_value = "test_password"

        # Store password
        credential_manager.store_password("testuser", "test_password")
        mock_set.assert_called_once_with("TestService", "testuser", "test_password")

        # Retrieve password
        password = credential_manager.get_password("testuser")
        assert password == "test_password"
        mock_get.assert_called_once_with("TestService", "testuser")


def test_get_password_not_found(credential_manager: CredentialManager) -> None:
    """Test retrieving non-existent password returns None."""
    with patch("keyring.get_password") as mock_get:
        mock_get.return_value = None
        password = credential_manager.get_password("nonexistent")
        assert password is None


def test_get_from_env(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test getting values from environment variables."""
    monkeypatch.setenv("TEST_VAR", "test_value")
    value = credential_manager.get_from_env("TEST_VAR")
    assert value == "test_value"


def test_get_from_env_not_set(credential_manager: CredentialManager) -> None:
    """Test getting unset environment variable returns None."""
    value = credential_manager.get_from_env("NONEXISTENT_VAR")
    assert value is None


def test_build_config_from_env(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test building DatabaseConfig from environment variables."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "testuser")
    monkeypatch.setenv("DB_PASSWORD", "testpass")

    config = credential_manager.build_config_from_env()

    assert isinstance(config, DatabaseConfig)
    assert config.db_type == "postgresql"
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.database == "testdb"
    assert config.username == "testuser"
    assert config.password == "testpass"
    assert config.ssl_enabled is False
    assert config.connection_timeout == 10


def test_build_config_from_env_with_ssl(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test building config with SSL enabled."""
    monkeypatch.setenv("DB_TYPE", "mysql")
    monkeypatch.setenv("DB_HOST", "db.example.com")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_NAME", "proddb")
    monkeypatch.setenv("DB_USER", "admin")
    monkeypatch.setenv("DB_PASSWORD", "secure123")
    monkeypatch.setenv("DB_SSL", "true")
    monkeypatch.setenv("DB_TIMEOUT", "30")

    config = credential_manager.build_config_from_env()

    assert config.db_type == "mysql"
    assert config.ssl_enabled is True
    assert config.connection_timeout == 30


@pytest.mark.parametrize(
    "ssl_value,expected",
    [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("no", False),
        ("", False),
    ],
)
def test_build_config_ssl_parsing(
    credential_manager: CredentialManager,
    monkeypatch: pytest.MonkeyPatch,
    ssl_value: str,
    expected: bool,
) -> None:
    """Test SSL boolean parsing from environment variables."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_SSL", ssl_value)

    config = credential_manager.build_config_from_env()
    assert config.ssl_enabled is expected


def test_build_config_keyring_fallback(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test password fallback to keyring when DB_PASSWORD not set."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "testuser")
    # DB_PASSWORD not set - should fall back to keyring

    with patch("keyring.get_password") as mock_get:
        mock_get.return_value = "keyring_password"

        config = credential_manager.build_config_from_env()

        assert config.password == "keyring_password"
        mock_get.assert_called_once_with("TestService", "testuser")


def test_build_config_missing_db_type(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_TYPE is missing."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_TYPE" in str(exc_info.value)


def test_build_config_missing_db_host(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_HOST is missing."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_PORT", "5432")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_HOST" in str(exc_info.value)


def test_build_config_missing_db_port(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_PORT is missing."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_PORT" in str(exc_info.value)


def test_build_config_invalid_db_port(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_PORT is not a valid integer."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "invalid")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_PORT must be a valid integer" in str(exc_info.value)


def test_build_config_missing_db_name(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_NAME is missing."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_NAME" in str(exc_info.value)


def test_build_config_missing_db_user(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_USER is missing."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_USER" in str(exc_info.value)


def test_build_config_missing_password_and_keyring(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when both DB_PASSWORD and keyring password are missing."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "testuser")

    with patch("keyring.get_password") as mock_get:
        mock_get.return_value = None

        with pytest.raises(ValueError) as exc_info:
            credential_manager.build_config_from_env()
        assert "DB_PASSWORD" in str(exc_info.value)


def test_build_config_invalid_timeout(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error when DB_TIMEOUT is not a valid integer."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")
    monkeypatch.setenv("DB_TIMEOUT", "not_a_number")

    with pytest.raises(ValueError) as exc_info:
        credential_manager.build_config_from_env()
    assert "DB_TIMEOUT must be a valid integer" in str(exc_info.value)


def test_build_config_pydantic_validation_error(
    credential_manager: CredentialManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that Pydantic validation errors are propagated."""
    monkeypatch.setenv("DB_TYPE", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "99999")  # Invalid port range
    monkeypatch.setenv("DB_NAME", "testdb")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pass")

    with pytest.raises(ValidationError) as exc_info:
        credential_manager.build_config_from_env()
    assert "port" in str(exc_info.value).lower()
