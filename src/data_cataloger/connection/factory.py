"""Database connector factory for creating database-specific connectors.

Implements the factory pattern to create appropriate connector instances
based on database type configuration.
"""

from data_cataloger.connection.base import DatabaseConnector
from data_cataloger.connection.config import DatabaseConfig


class DatabaseFactory:
    """Factory for creating database-specific connector instances.

    Uses the factory pattern to instantiate the correct connector class
    based on the database type in the configuration.
    """

    @staticmethod
    def create_connector(config: DatabaseConfig) -> DatabaseConnector:
        """Create a database connector based on configuration.

        Args:
            config: Database configuration containing connection parameters

        Returns:
            DatabaseConnector instance for the specified database type

        Raises:
            ValueError: If database type is not supported
        """
        # Import here to avoid circular imports and enable lazy loading
        if config.db_type == "postgresql":
            from data_cataloger.connection.postgres import PostgreSQLConnector

            return PostgreSQLConnector(config)
        elif config.db_type == "mysql":
            from data_cataloger.connection.mysql import MySQLConnector

            return MySQLConnector(config)
        else:
            raise ValueError(
                f"Unsupported database type: {config.db_type}. "
                f"Supported types: postgresql, mysql"
            )
