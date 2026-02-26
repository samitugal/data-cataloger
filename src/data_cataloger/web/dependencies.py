"""FastAPI dependencies for Neo4j connection and repository access."""

import os
from collections.abc import Generator
from functools import lru_cache

from neo4j import Driver, GraphDatabase

from data_cataloger.storage import GraphRepository, Neo4jConfig


@lru_cache
def get_neo4j_config() -> Neo4jConfig:
    """Get Neo4j configuration from environment variables."""
    return Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
    )


def get_neo4j_driver() -> Driver:
    """Create Neo4j driver from config."""
    config = get_neo4j_config()
    return GraphDatabase.driver(config.uri, auth=(config.username, config.password))


def get_graph_repository() -> Generator[GraphRepository, None, None]:
    """Dependency that provides GraphRepository with managed driver lifecycle."""
    driver = get_neo4j_driver()
    config = get_neo4j_config()
    try:
        yield GraphRepository(driver, config.database)
    finally:
        driver.close()


def get_database_name() -> str:
    """Get target database name for queries."""
    return os.getenv("DATABASE_NAME", "production_db")
