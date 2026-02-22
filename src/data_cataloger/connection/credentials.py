"""Secure credential management for database connections.

Provides credential storage using OS keyring and environment variable loading
for database connection configuration.
"""

import os

import keyring

from data_cataloger.connection.config import DatabaseConfig


class CredentialManager:
    """Manages database credentials securely using OS keyring.

    Stores passwords in the OS keyring (Keychain on macOS,
    Credential Manager on Windows, Secret Service on Linux) instead of
    plain text. Also supports loading configuration from environment variables.

    Attributes:
        service_name: Service name used for keyring storage
    """

    def __init__(self, service_name: str = "AutomatedDataCataloger") -> None:
        """Initialize credential manager.

        Args:
            service_name: Service name for keyring storage
                (default: AutomatedDataCataloger)
        """
        self.service_name = service_name

    def store_password(self, username: str, password: str) -> None:
        """Store password in OS keyring.

        Args:
            username: Username to associate with password
            password: Password to store securely
        """
        keyring.set_password(self.service_name, username, password)

    def get_password(self, username: str) -> str | None:
        """Retrieve password from OS keyring.

        Args:
            username: Username to retrieve password for

        Returns:
            Password if found in keyring, None otherwise
        """
        return keyring.get_password(self.service_name, username)

    def get_from_env(self, key: str) -> str | None:
        """Get credential from environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value if set, None otherwise
        """
        return os.getenv(key)

    def build_config_from_env(self) -> DatabaseConfig:
        """Build DatabaseConfig from environment variables.

        Reads configuration from the following environment variables:
        - DB_TYPE: Database type (postgresql or mysql)
        - DB_HOST: Database hostname
        - DB_PORT: Database port number
        - DB_NAME: Database name
        - DB_USER: Database username
        - DB_PASSWORD: Database password (falls back to keyring if not set)
        - DB_SSL: Enable SSL (true/false, default: false)
        - DB_TIMEOUT: Connection timeout in seconds (default: 10)

        Returns:
            DatabaseConfig instance built from environment variables

        Raises:
            ValueError: If required environment variables are missing or invalid
            pydantic.ValidationError: If configuration values fail validation
        """
        db_type = self.get_from_env("DB_TYPE")
        if not db_type:
            raise ValueError("DB_TYPE environment variable is required")

        host = self.get_from_env("DB_HOST")
        if not host:
            raise ValueError("DB_HOST environment variable is required")

        port_str = self.get_from_env("DB_PORT")
        if not port_str:
            raise ValueError("DB_PORT environment variable is required")
        try:
            port = int(port_str)
        except ValueError:
            raise ValueError(f"DB_PORT must be a valid integer, got '{port_str}'")

        database = self.get_from_env("DB_NAME")
        if not database:
            raise ValueError("DB_NAME environment variable is required")

        username = self.get_from_env("DB_USER")
        if not username:
            raise ValueError("DB_USER environment variable is required")

        # Try environment variable first, then fall back to keyring
        password = self.get_from_env("DB_PASSWORD")
        if not password:
            password = self.get_password(username)
        if not password:
            raise ValueError(
                "DB_PASSWORD environment variable or keyring entry required"
            )

        # Optional parameters with defaults
        ssl_str = self.get_from_env("DB_SSL")
        ssl_enabled = ssl_str is not None and ssl_str.lower() in ("true", "1", "yes")

        timeout_str = self.get_from_env("DB_TIMEOUT")
        connection_timeout = 10
        if timeout_str:
            try:
                connection_timeout = int(timeout_str)
            except ValueError:
                raise ValueError(
                    f"DB_TIMEOUT must be a valid integer, got '{timeout_str}'"
                )

        return DatabaseConfig(
            db_type=db_type,  # type: ignore[arg-type]
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            connection_timeout=connection_timeout,
        )
