"""Cataloging API endpoint for starting real-time database cataloging."""

import logging
import time
from typing import Annotated, Any, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from data_cataloger.cataloging.agent import CatalogingAgent
from data_cataloger.connection.config import DatabaseConfig
from data_cataloger.connection.postgres import PostgreSQLConnector
from data_cataloger.embeddings.client import EmbeddingClient
from data_cataloger.schema.introspector import SchemaIntrospector
from data_cataloger.storage.writer import Neo4jWriter
from data_cataloger.web.dependencies import get_database_name, get_neo4j_driver
from data_cataloger.web.routes.progress import (
    complete_cataloging,
    emit_table_event,
    init_cataloging,
    reset_cataloging,
)

router = APIRouter(prefix="/api/cataloging", tags=["cataloging"])


class ConnectionRequest(BaseModel):
    """Request to connect and discover databases."""

    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = "postgres"
    db_type: Literal["postgresql", "mysql"] = "postgresql"


class DatabaseListResponse(BaseModel):
    """Response with available databases."""

    databases: list[str]
    count: int


class CatalogingRequest(BaseModel):
    """Request to start cataloging a database."""

    host: str = "localhost"
    port: int = 5432
    database: str = "northwind"
    username: str = "postgres"
    password: str = "postgres"
    db_type: Literal["postgresql", "mysql"] = "postgresql"


class CatalogingResponse(BaseModel):
    """Response after starting cataloging."""

    status: str
    message: str
    total_tables: int = 0


logger = logging.getLogger(__name__)


def run_cataloging(
    config: DatabaseConfig,
    neo4j_driver: Any,
    database_name: str,
) -> None:
    """Background task to run cataloging with event emission."""
    start_time = time.time()
    logger.info(f"Starting cataloging for database: {database_name}")

    try:
        # Connect to source database
        connector = PostgreSQLConnector(config)
        connector.connect()

        if not connector.test_connection():
            raise Exception("Failed to connect to database")

        # Introspect schema
        introspector = SchemaIntrospector()
        schema_result = introspector.introspect_schema(connector, schema="public")

        # Initialize progress tracking
        init_cataloging(database_name, len(schema_result.tables))

        # Create Neo4j writer
        writer = Neo4jWriter(neo4j_driver, "neo4j")

        # Create embedding client for semantic search
        embedding_client = EmbeddingClient()

        # Create agent with writer and embedding client
        agent = CatalogingAgent(writer=writer, embedding_client=embedding_client)

        # Build table metadata lookup
        tables_by_name = {t.table_name: t for t in schema_result.tables}

        # Process tables one by one with event emission
        from data_cataloger.cataloging.models import CatalogState

        state = CatalogState()

        for table_name in schema_result.processing_order:
            table_meta = tables_by_name[table_name]

            # Get parent context
            parent_context = state.get_parent_context(table_meta)

            # Catalog this table
            entry = agent._catalog_table(table_meta, parent_context)

            # Add to state
            state.add_entry(entry)

            # Write to Neo4j
            agent._write_to_storage(entry, table_meta, database_name, config.db_type)

            # Emit SSE event with full table data
            foreign_keys = [
                {
                    "column": fk.column_name,
                    "references_table": fk.referenced_table,
                    "references_column": fk.referenced_column,
                }
                for fk in table_meta.foreign_keys
            ]

            emit_table_event(
                database_name=database_name,
                table_name=entry.table_name,
                description=entry.description,
                sensitivity=entry.sensitivity,
                example_queries=list(entry.example_queries),
                schema_name=table_meta.schema_name,
                foreign_keys=foreign_keys,
            )

        connector.close()

        duration = time.time() - start_time
        complete_cataloging(database_name, duration)

    except Exception as e:
        complete_cataloging(database_name, time.time() - start_time)
        raise e


@router.post("/start", response_model=CatalogingResponse)
async def start_cataloging(
    request: CatalogingRequest,
    background_tasks: BackgroundTasks,
    neo4j_driver: Annotated[Any, Depends(get_neo4j_driver)],
) -> CatalogingResponse:
    """Start cataloging a database in the background."""
    # Use database name from request
    database_name = request.database

    # Reset any previous state
    reset_cataloging(database_name)

    # Create database config
    config = DatabaseConfig(
        db_type=request.db_type,
        host=request.host,
        port=request.port,
        database=request.database,
        username=request.username,
        password=request.password,
    )

    # Quick validation - try to connect
    try:
        connector = PostgreSQLConnector(config)
        connector.connect()

        if not connector.test_connection():
            raise HTTPException(status_code=400, detail="Cannot connect to database")

        # Get table count
        introspector = SchemaIntrospector()
        schema_result = introspector.introspect_schema(connector, schema="public")
        total_tables = len(schema_result.tables)

        connector.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database connection failed: {e}")

    # Start background cataloging
    background_tasks.add_task(
        run_cataloging,
        config,
        neo4j_driver,
        database_name,
    )

    return CatalogingResponse(
        status="started",
        message=f"Cataloging started for {total_tables} tables",
        total_tables=total_tables,
    )


@router.post("/reset")
async def reset_catalog(
    database_name: Annotated[str, Depends(get_database_name)],
) -> dict[str, str]:
    """Reset cataloging state."""
    reset_cataloging(database_name)
    return {"status": "reset", "message": "Cataloging state cleared"}


@router.post("/discover", response_model=DatabaseListResponse)
async def discover_databases(
    request: ConnectionRequest,
) -> DatabaseListResponse:
    """Discover available databases on a PostgreSQL/MySQL server."""
    # System databases to exclude
    system_dbs = {
        "postgres",
        "template0",
        "template1",
        "information_schema",
        "mysql",
        "sys",
        "performance_schema",
    }

    try:
        # Connect to default database to list others
        config = DatabaseConfig(
            db_type=request.db_type,
            host=request.host,
            port=request.port,
            database="postgres" if request.db_type == "postgresql" else "mysql",
            username=request.username,
            password=request.password,
        )

        connector = PostgreSQLConnector(config)
        connector.connect()

        if not connector.test_connection():
            raise HTTPException(status_code=400, detail="Cannot connect to server")

        # Query available databases
        if request.db_type == "postgresql":
            query = "SELECT datname FROM pg_database WHERE datistemplate = false"
        else:
            query = "SHOW DATABASES"

        cursor = connector.conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connector.close()

        # Filter out system databases
        databases = [row[0] for row in rows if row[0] not in system_dbs]
        databases.sort()

        return DatabaseListResponse(databases=databases, count=len(databases))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to discover databases: {e}"
        )
