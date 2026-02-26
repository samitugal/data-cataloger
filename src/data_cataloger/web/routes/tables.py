"""Table API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from data_cataloger.storage import GraphRepository
from data_cataloger.web.dependencies import get_database_name, get_graph_repository
from data_cataloger.web.schemas import TableListResponse, TableResponse

router = APIRouter(prefix="/api/tables", tags=["tables"])


@router.get("", response_model=TableListResponse)
async def list_tables(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
) -> TableListResponse:
    """List all cataloged tables."""
    entries = repo.list_tables(database_name)
    tables = [
        TableResponse(
            name=e.table_name,
            description=e.description,
            sensitivity=e.sensitivity,
            example_queries=list(e.example_queries),
        )
        for e in entries
    ]
    return TableListResponse(tables=tables, total=len(tables))


@router.get("/search", response_model=TableListResponse)
async def search_tables(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
    q: Annotated[str, Query(min_length=1, description="Search keyword")],
) -> TableListResponse:
    """Search tables by keyword in descriptions."""
    entries = repo.search_by_keyword(q, database_name)
    tables = [
        TableResponse(
            name=e.table_name,
            description=e.description,
            sensitivity=e.sensitivity,
            example_queries=list(e.example_queries),
        )
        for e in entries
    ]
    return TableListResponse(tables=tables, total=len(tables))


@router.get("/sensitivity/{level}", response_model=TableListResponse)
async def filter_by_sensitivity(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
    level: str,
) -> TableListResponse:
    """Filter tables by sensitivity level."""
    entries = repo.search_by_sensitivity(level, database_name)
    tables = [
        TableResponse(
            name=e.table_name,
            description=e.description,
            sensitivity=e.sensitivity,
            example_queries=list(e.example_queries),
        )
        for e in entries
    ]
    return TableListResponse(tables=tables, total=len(tables))


@router.get("/{name}", response_model=TableResponse)
async def get_table(
    name: str,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
) -> TableResponse:
    """Get single table details."""
    entry = repo.get_table(name, database_name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Table '{name}' not found")
    return TableResponse(
        name=entry.table_name,
        description=entry.description,
        sensitivity=entry.sensitivity,
        example_queries=list(entry.example_queries),
    )
