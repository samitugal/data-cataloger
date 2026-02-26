"""MCP Server for Data Cataloger.

Provides Model Context Protocol server with tools for accessing
enriched database metadata. Supports SSE transport and maintains
stateful Neo4j connection.

Tools:
    - list_tables: List all cataloged tables
    - get_table: Get detailed table information
    - search_tables: Search tables by keyword
    - filter_by_sensitivity: Filter tables by sensitivity level
    - get_relationships: Get FK relationships for a table
    - get_graph: Get full relationship graph
    - semantic_search: Search tables by semantic similarity
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from neo4j import GraphDatabase
from starlette.applications import Starlette
from starlette.routing import Route

from data_cataloger.embeddings.client import EmbeddingClient
from data_cataloger.storage.config import Neo4jConfig
from data_cataloger.storage.repository import GraphRepository


class MCPServerState:
    """Stateful MCP server maintaining Neo4j connection."""

    def __init__(self) -> None:
        self.repository: GraphRepository | None = None
        self.embedding_client: EmbeddingClient | None = None
        self.driver: Any = None

    def connect(self) -> None:
        """Connect to Neo4j using environment variables."""
        config = Neo4jConfig(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USER", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
        )
        self.driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
        )
        self.repository = GraphRepository(self.driver, config.database)

        if os.getenv("OPENAI_API_KEY"):
            self.embedding_client = EmbeddingClient()

    def disconnect(self) -> None:
        """Disconnect from Neo4j."""
        if self.driver:
            self.driver.close()
            self.driver = None
            self.repository = None


def create_mcp_server() -> Server:
    """Create and configure MCP server with catalog tools."""
    server = Server("data-cataloger")
    state = MCPServerState()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="list_tables",
                description="List all cataloged tables in a database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        }
                    },
                    "required": ["database_name"],
                },
            ),
            Tool(
                name="get_table",
                description="Get detailed information about a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                    },
                    "required": ["table_name", "database_name"],
                },
            ),
            Tool(
                name="search_tables",
                description="Search tables by keyword in descriptions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Search keyword",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                    },
                    "required": ["keyword", "database_name"],
                },
            ),
            Tool(
                name="filter_by_sensitivity",
                description="Filter tables by sensitivity classification",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sensitivity": {
                            "type": "string",
                            "description": (
                                "Sensitivity level (PII, financial, internal, public)"
                            ),
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                    },
                    "required": ["sensitivity", "database_name"],
                },
            ),
            Tool(
                name="get_relationships",
                description="Get foreign key relationships for a table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                    },
                    "required": ["table_name", "database_name"],
                },
            ),
            Tool(
                name="get_graph",
                description="Get the full relationship graph for visualization",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        }
                    },
                    "required": ["database_name"],
                },
            ),
            Tool(
                name="semantic_search",
                description="Search tables by semantic similarity to a query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max results (default: 5)",
                            "default": 5,
                        },
                        "threshold": {
                            "type": "number",
                            "description": "Min similarity score (default: 0.7)",
                            "default": 0.7,
                        },
                    },
                    "required": ["query", "database_name"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        if not state.repository:
            state.connect()

        if not state.repository:
            return [TextContent(type="text", text="Error: Failed to connect to Neo4j")]

        try:
            result = _execute_tool(name, arguments, state)
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

    return server


def _execute_tool(name: str, args: dict[str, Any], state: MCPServerState) -> dict:
    """Execute a tool and return the result."""
    repo = state.repository
    if not repo:
        return {"error": True, "message": "Not connected to database"}

    if name == "list_tables":
        entries = repo.list_tables(args["database_name"])
        return {
            "tables": [
                {
                    "name": e.table_name,
                    "description": e.description,
                    "sensitivity": e.sensitivity,
                }
                for e in entries
            ],
            "count": len(entries),
        }

    elif name == "get_table":
        entry = repo.get_table(args["table_name"], args["database_name"])
        if not entry:
            return {
                "error": True,
                "code": "TABLE_NOT_FOUND",
                "message": f"Table '{args['table_name']}' not found",
            }
        relationships = repo.get_relationships(
            args["table_name"], args["database_name"]
        )
        return {
            "name": entry.table_name,
            "description": entry.description,
            "sensitivity": entry.sensitivity,
            "example_queries": entry.example_queries,
            "foreign_keys": relationships,
        }

    elif name == "search_tables":
        entries = repo.search_by_keyword(args["keyword"], args["database_name"])
        return {
            "tables": [
                {
                    "name": e.table_name,
                    "description": e.description,
                    "sensitivity": e.sensitivity,
                }
                for e in entries
            ],
            "count": len(entries),
            "keyword": args["keyword"],
        }

    elif name == "filter_by_sensitivity":
        entries = repo.search_by_sensitivity(
            args["sensitivity"], args["database_name"]
        )
        return {
            "tables": [
                {
                    "name": e.table_name,
                    "description": e.description,
                    "sensitivity": e.sensitivity,
                }
                for e in entries
            ],
            "count": len(entries),
            "sensitivity": args["sensitivity"],
        }

    elif name == "get_relationships":
        relationships = repo.get_relationships(
            args["table_name"], args["database_name"]
        )
        return {
            "table": args["table_name"],
            "relationships": relationships,
        }

    elif name == "get_graph":
        graph = repo.get_full_graph(args["database_name"])
        return graph

    elif name == "semantic_search":
        if not state.embedding_client:
            return {
                "error": True,
                "code": "EMBEDDINGS_NOT_CONFIGURED",
                "message": "OPENAI_API_KEY not set for semantic search",
            }

        query_embedding = state.embedding_client.embed(args["query"])
        limit = args.get("limit", 5)
        threshold = args.get("threshold", 0.7)

        results = repo.semantic_search(
            query_embedding,
            args["database_name"],
            limit=limit,
            threshold=threshold,
        )

        return {
            "query": args["query"],
            "results": results,
            "count": len(results),
        }

    else:
        return {
            "error": True,
            "code": "UNKNOWN_TOOL",
            "message": f"Unknown tool: {name}",
        }


def create_sse_app() -> Starlette:
    """Create Starlette app with SSE transport for MCP server."""
    server = create_mcp_server()
    sse = SseServerTransport("/messages/")

    @asynccontextmanager
    async def lifespan(app: Starlette):
        yield

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages/", endpoint=sse.handle_post_message, methods=["POST"]),
        ],
        lifespan=lifespan,
    )
