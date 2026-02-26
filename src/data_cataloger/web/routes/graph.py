"""Graph API endpoints for Cytoscape.js visualization."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from data_cataloger.storage import GraphRepository
from data_cataloger.web.dependencies import get_database_name, get_graph_repository
from data_cataloger.web.schemas import GraphEdge, GraphNode, GraphResponse

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("", response_model=GraphResponse)
async def get_full_graph(
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
) -> GraphResponse:
    """Get full graph for visualization."""
    graph_data = repo.get_full_graph(database_name)

    nodes = [
        GraphNode(
            id=node["name"],
            label=node["name"],
            sensitivity=node.get("sensitivity", "internal"),
        )
        for node in graph_data["nodes"]
    ]

    edges = [
        GraphEdge(
            source=edge["source"],
            target=edge["target"],
            label=f"{edge.get('fk_column', '')} → {edge.get('referenced_column', '')}",
        )
        for edge in graph_data["edges"]
    ]

    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/{table}/neighbors", response_model=GraphResponse)
async def get_table_neighbors(
    table: str,
    repo: Annotated[GraphRepository, Depends(get_graph_repository)],
    database_name: Annotated[str, Depends(get_database_name)],
) -> GraphResponse:
    """Get table with its direct relationships (neighbors)."""
    # Get the table itself
    entry = repo.get_table(table, database_name)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Table '{table}' not found")

    # Get relationships
    relationships = repo.get_relationships(table, database_name)

    # Build nodes: center table + all referenced tables
    nodes = [
        GraphNode(
            id=entry.table_name,
            label=entry.table_name,
            sensitivity=entry.sensitivity,
        )
    ]

    # Add referenced tables as nodes
    seen_tables = {entry.table_name}
    for rel in relationships:
        ref_table = rel["referenced_table"]
        if ref_table not in seen_tables:
            # Try to get the referenced table's details
            ref_entry = repo.get_table(ref_table, database_name)
            nodes.append(
                GraphNode(
                    id=ref_table,
                    label=ref_table,
                    sensitivity=ref_entry.sensitivity if ref_entry else "internal",
                )
            )
            seen_tables.add(ref_table)

    # Build edges
    edges = [
        GraphEdge(
            source=table,
            target=rel["referenced_table"],
            label=f"{rel.get('fk_column', '')} → {rel.get('referenced_column', '')}",
        )
        for rel in relationships
    ]

    return GraphResponse(nodes=nodes, edges=edges)
