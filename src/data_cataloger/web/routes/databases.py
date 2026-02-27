"""Database listing API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from data_cataloger.storage import GraphRepository
from data_cataloger.web.dependencies import get_graph_repository

router = APIRouter(prefix="/api/databases", tags=["databases"])


class DatabaseInfo(BaseModel):
    """Database information."""

    name: str
    type: str | None
    created_at: str | None
    table_count: int


class DatabaseListResponse(BaseModel):
    """Response for listing databases."""

    databases: list[DatabaseInfo]
    count: int


@router.get("", response_model=DatabaseListResponse)
async def list_databases(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
) -> DatabaseListResponse:
    """List all cataloged databases."""
    databases = repo.list_databases()

    return DatabaseListResponse(
        databases=[
            DatabaseInfo(
                name=db["name"],
                type=db.get("type"),
                created_at=db.get("created_at"),
                table_count=db.get("table_count", 0),
            )
            for db in databases
        ],
        count=len(databases),
    )
