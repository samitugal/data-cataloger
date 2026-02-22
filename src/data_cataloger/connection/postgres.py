"""PostgreSQL database connector implementation.

Provides connection management and testing for PostgreSQL databases using psycopg.
Includes detailed error handling for common connection failures.
"""

import psycopg
from psycopg import Connection

from data_cataloger.connection.base import ConnectionTestResult
from data_cataloger.connection.config import DatabaseConfig


class PostgreSQLConnector:
    """PostgreSQL database connector implementation.

    Manages connections to PostgreSQL databases with connection testing
    and detailed error reporting.

    Attributes:
        config: Database configuration
        conn: Active database connection (None if not connected)
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize PostgreSQL connector.

        Args:
            config: Database configuration with connection parameters
        """
        self.config = config
        self.conn: Connection[tuple[object, ...]] | None = None

    @property
    def connection(self) -> Connection[tuple[object, ...]]:
        """Active database connection.

        Returns:
            Active psycopg Connection object

        Raises:
            RuntimeError: If not connected
        """
        if self.conn is None:
            raise RuntimeError("Not connected to database. Call connect() first.")
        return self.conn

    def connect(self) -> None:
        """Establish connection to PostgreSQL database.

        Raises:
            psycopg.OperationalError: If connection fails
            psycopg.ConnectionTimeout: If connection times out
        """
        self.conn = psycopg.connect(
            host=self.config.host,
            port=self.config.port,
            dbname=self.config.database,
            user=self.config.username,
            password=self.config.password,
            connect_timeout=self.config.connection_timeout,
        )

    def test_connection(self) -> bool:
        """Test if the PostgreSQL connection is alive.

        Returns:
            True if connection is alive and can execute queries, False otherwise
        """
        if self.conn is None:
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the PostgreSQL connection.

        Idempotent - safe to call multiple times.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def check_postgresql_connection(config: DatabaseConfig) -> ConnectionTestResult:
    """Test PostgreSQL connection with detailed error reporting.

    Args:
        config: Database configuration to test

    Returns:
        ConnectionTestResult with success status, message, and error type
    """
    try:
        # Attempt to connect to PostgreSQL
        with psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.database,
            user=config.username,
            password=config.password,
            connect_timeout=config.connection_timeout,
        ) as conn:
            # Verify connection by executing simple query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")

            return ConnectionTestResult(
                success=True,
                message=(
                    f"Successfully connected to PostgreSQL database "
                    f"'{config.database}' at {config.host}:{config.port}"
                ),
                error_type=None,
            )

    except psycopg.OperationalError as e:
        error_message = str(e)

        # Parse error message to determine specific error type
        if "password authentication failed" in error_message:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Authentication failed for user '{config.username}' "
                    f"on database '{config.database}'"
                ),
                error_type="AUTH_FAILED",
            )
        elif "could not connect to server" in error_message:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Could not connect to PostgreSQL server at "
                    f"{config.host}:{config.port}. "
                    f"Server may be down or unreachable."
                ),
                error_type="CONNECTION_REFUSED",
            )
        elif "database" in error_message and "does not exist" in error_message:
            return ConnectionTestResult(
                success=False,
                message=(
                    f"Database '{config.database}' does not exist on server "
                    f"{config.host}:{config.port}"
                ),
                error_type="DB_NOT_FOUND",
            )
        else:
            return ConnectionTestResult(
                success=False,
                message=f"PostgreSQL operational error: {error_message}",
                error_type="OPERATIONAL_ERROR",
            )

    except TimeoutError:
        return ConnectionTestResult(
            success=False,
            message=(
                f"Connection to {config.host}:{config.port} timed out after "
                f"{config.connection_timeout} seconds"
            ),
            error_type="TIMEOUT",
        )

    except psycopg.InterfaceError as e:
        return ConnectionTestResult(
            success=False,
            message=f"PostgreSQL interface error: {str(e)}",
            error_type="INTERFACE_ERROR",
        )

    except Exception as e:
        return ConnectionTestResult(
            success=False,
            message=f"Unexpected error connecting to PostgreSQL: {str(e)}",
            error_type="UNKNOWN_ERROR",
        )
