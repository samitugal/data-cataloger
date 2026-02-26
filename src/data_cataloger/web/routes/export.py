"""Export API endpoints for catalog data."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from data_cataloger.export.exporter import CatalogExporter
from data_cataloger.storage.repository import GraphRepository
from data_cataloger.web.dependencies import get_database_name, get_graph_repository

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/json")
async def export_json(
    database_name: Annotated[str, Depends(get_database_name)],
    repository: Annotated[GraphRepository, Depends(get_graph_repository)],
) -> Response:
    """Export catalog as JSON."""
    exporter = CatalogExporter(repository)
    content = exporter.export_json(database_name)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{database_name}_catalog.json"'
            )
        },
    )


@router.get("/yaml")
async def export_yaml(
    database_name: Annotated[str, Depends(get_database_name)],
    repository: Annotated[GraphRepository, Depends(get_graph_repository)],
) -> PlainTextResponse:
    """Export catalog as YAML."""
    exporter = CatalogExporter(repository)
    content = exporter.export_yaml(database_name)
    return PlainTextResponse(
        content=content,
        media_type="text/yaml",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{database_name}_catalog.yaml"'
            )
        },
    )


@router.get("/markdown")
async def export_markdown(
    database_name: Annotated[str, Depends(get_database_name)],
    repository: Annotated[GraphRepository, Depends(get_graph_repository)],
) -> PlainTextResponse:
    """Export catalog as Markdown documentation."""
    exporter = CatalogExporter(repository)
    content = exporter.export_markdown(database_name)
    return PlainTextResponse(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{database_name}_catalog.md"'
        },
    )
