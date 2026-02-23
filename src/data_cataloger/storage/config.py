"""Neo4j graph database connection configuration.

Provides type-safe configuration for Neo4j database connections using
Pydantic validation with sensible defaults for local Docker deployment.
"""

from pydantic import BaseModel, Field


class Neo4jConfig(BaseModel):
    """Neo4j connection configuration with validation.

    Provides connection parameters for Neo4j graph database with defaults
    optimized for local Docker deployment via docker-compose.yml.

    Attributes:
        uri: Neo4j connection URI using bolt:// protocol (default: bolt://localhost:7687)
        username: Database username (default: neo4j)
        password: Database password (default: password)
        database: Target database name (default: neo4j). Always specify this parameter
            to avoid Neo4j driver bugs with database selection.
    """

    uri: str = Field(default="bolt://localhost:7687", min_length=1)
    username: str = Field(default="neo4j", min_length=1)
    password: str = Field(default="password", min_length=1)
    database: str = Field(default="neo4j", min_length=1)
