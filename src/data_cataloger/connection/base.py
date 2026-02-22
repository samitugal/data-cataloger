"""Database connector protocol and connection test result types.

Defines the interface that all database connectors must implement using
structural subtyping (Protocol). Provides ConnectionTestResult for detailed
error reporting.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ConnectionTestResult:
    """Result of a database connection test.

    Attributes:
        success: Whether the connection test succeeded
        message: Human-readable message describing the result
        error_type: Type of error if failed (None on success)
    """

    success: bool
    message: str
    error_type: str | None


class DatabaseConnector(Protocol):
    """Protocol defining the interface for database connectors.

    All database connector implementations must implement these methods
    to be compatible with the factory pattern and connection manager.

    Methods:
        connect: Establish connection to the database
        test_connection: Test if connection is alive
        close: Close the database connection
    """

    def connect(self) -> None:
        """Establish connection to the database.

        Raises:
            Exception: If connection fails (implementation-specific)
        """
        ...

    def test_connection(self) -> bool:
        """Test if the database connection is alive.

        Returns:
            True if connection is alive and can execute queries, False otherwise
        """
        ...

    def close(self) -> None:
        """Close the database connection.

        Should be idempotent - safe to call multiple times.
        """
        ...
