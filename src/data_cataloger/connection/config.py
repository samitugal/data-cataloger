"""Database connection configuration models with validation.

Provides type-safe configuration for PostgreSQL and MySQL database connections
using Pydantic validation.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    """Database connection configuration with validation.

    Validates connection parameters before attempting database connections.
    Supports PostgreSQL and MySQL databases with optional SSL.

    Attributes:
        db_type: Database type (postgresql or mysql)
        host: Database server hostname
        port: Database server port (1-65535)
        database: Database name
        username: Database username
        password: Database password
        ssl_enabled: Enable SSL connection (default: False)
        connection_timeout: Connection timeout in seconds (default: 10)
    """

    db_type: Literal["postgresql", "mysql"]
    host: str = Field(min_length=1)
    port: int
    database: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    ssl_enabled: bool = False
    connection_timeout: int = Field(default=10, gt=0)

    @field_validator("port")
    @classmethod
    def validate_port_range(cls, v: int) -> int:
        """Validate port is in valid range (1-65535).

        Args:
            v: Port number to validate

        Returns:
            Validated port number

        Raises:
            ValueError: If port is outside valid range
        """
        if v < 1 or v > 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v
