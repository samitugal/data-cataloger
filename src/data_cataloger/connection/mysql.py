"""MySQL/MariaDB database connector implementation.

Provides connection management and testing for MySQL and MariaDB databases
using mysql-connector-python. Includes detailed error handling for common
connection failures.
"""

from typing import Any

import mysql.connector
from mysql.connector import errorcode
from mysql.connector.errors import Error as MySQLError

from data_cataloger.connection.base import ConnectionTestResult
from data_cataloger.connection.config import DatabaseConfig


class MySQLConnector:
    """MySQL/MariaDB database connector implementation.

    Manages connections to MySQL and MariaDB databases with connection testing
    and detailed error reporting.

    Attributes:
        config: Database configuration
        conn: Active database connection (None if not connected)
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize MySQL connector.

        Args:
            config: Database configuration with connection parameters
        """
        self.config = config
        self.conn: Any = None  # mysql.connector.connect() returns union type

    @property
    def connection(self) -> Any:
        """Active database connection.

        Returns:
            Active mysql.connector connection object

        Raises:
            RuntimeError: If not connected
        """
        if self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
        return self.conn

    def connect(self) -> None:
        """Establish connection to MySQL database.

        Raises:
            mysql.connector.Error: If connection fails
        """
        self.conn = mysql.connector.connect(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.username,
            password=self.config.password,
            connection_timeout=self.config.connection_timeout,
        )

    def test_connection(self) -> bool:
        """Test if the MySQL connection is alive.

        Uses the .connected property (not deprecated is_connected() method).

        Returns:
            True if connection is alive and can execute queries, False otherwise
        """
        if self.conn is None:
            return False

        # Use .connected property, NOT is_connected() method (deprecated in 9.3.0+)
        return bool(self.conn.connected)

    def close(self) -> None:
        """Close the MySQL connection.

        Idempotent - safe to call multiple times.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def check_mysql_connection(config: DatabaseConfig) -> ConnectionTestResult:
    """Test MySQL connection with detailed error reporting.

    Args:
        config: Database configuration to test

    Returns:
        ConnectionTestResult with success status, message, and error type
    """
    try:
        # Attempt to connect to MySQL
        conn: Any = mysql.connector.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password,
            connection_timeout=config.connection_timeout,
        )

        # Verify connection using .connected property
        if not bool(conn.connected):
            conn.close()
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Connected to MySQL at {config.host}:{config.port} "
                    f"but connection is not active"
                ),
                error_type="CONNECTION_NOT_ACTIVE",
            )

        # Execute simple query to verify connection
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        return ConnectionTestResult(
            success=True,
            message=(
                f"Successfully connected to MySQL database "
                f"'{config.database}' at {config.host}:{config.port}"
            ),
            error_type=None,
        )

    except MySQLError as err:
        # Check specific MySQL error codes
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Authentication failed for user '{config.username}' "
                    f"on database '{config.database}'"
                ),
                error_type="AUTH_FAILED",
            )
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Database '{config.database}' does not exist on server "
                    f"{config.host}:{config.port}"
                ),
                error_type="DB_NOT_FOUND",
            )
        else:
            error_type = f"MYSQL_ERROR_{err.errno}" if err.errno else "MYSQL_ERROR"
            return ConnectionTestResult(
                success=False,
                message=f"MySQL error: {str(err)}",
                error_type=error_type,
            )

    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"Unexpected error connecting to MySQL: {str(e)}",
            error_type="UNKNOWN_ERROR",
        )
