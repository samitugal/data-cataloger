"""Pydantic schemas for API responses."""

from pydantic import BaseModel, Field


class TableResponse(BaseModel):
    """Single table catalog entry response."""

    name: str = Field(description="Table name")
    description: str = Field(description="Business description")
    sensitivity: str = Field(description="Data sensitivity classification")
    example_queries: list[str] = Field(description="Example SQL queries")


class TableListResponse(BaseModel):
    """List of tables response."""

    tables: list[TableResponse] = Field(description="List of catalog entries")
    total: int = Field(description="Total number of tables")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(description="Error message")


class GraphNode(BaseModel):
    """Graph node for Cytoscape.js."""

    id: str = Field(description="Unique node identifier (table name)")
    label: str = Field(description="Display label")
    sensitivity: str = Field(description="Data sensitivity classification")


class GraphEdge(BaseModel):
    """Graph edge for Cytoscape.js."""

    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    label: str = Field(description="Edge label (FK column → referenced column)")


class GraphResponse(BaseModel):
    """Full graph response for Cytoscape.js."""

    nodes: list[GraphNode] = Field(description="Graph nodes")
    edges: list[GraphEdge] = Field(description="Graph edges")
