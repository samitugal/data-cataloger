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
                name="get_neighbors",
                description="Get a table and all its directly connected neighbors",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to get neighbors for",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                        "direction": {
                            "type": "string",
                            "description": (
                                "Direction: 'outgoing', 'incoming', or 'both'"
                            ),
                            "default": "both",
                        },
                    },
                    "required": ["table_name", "database_name"],
                },
            ),
            Tool(
                name="traverse_path",
                description="Find path between two tables through relationships",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "from_table": {
                            "type": "string",
                            "description": "Starting table name",
                        },
                        "to_table": {
                            "type": "string",
                            "description": "Target table name",
                        },
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum path length (default: 5)",
                            "default": 5,
                        },
                    },
                    "required": ["from_table", "to_table", "database_name"],
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
            Tool(
                name="export_catalog",
                description="Export catalog in JSON, YAML, or Markdown format",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database_name": {
                            "type": "string",
                            "description": "Name of the database",
                        },
                        "format": {
                            "type": "string",
                            "description": "Format: 'json', 'yaml', or 'markdown'",
                            "default": "json",
                        },
                    },
                    "required": ["database_name"],
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

    elif name == "get_neighbors":
        result = _get_neighbors(
            repo._driver,
            args["table_name"],
            args["database_name"],
            args.get("direction", "both"),
        )
        return result

    elif name == "traverse_path":
        result = _traverse_path(
            repo._driver,
            args["from_table"],
            args["to_table"],
            args["database_name"],
            args.get("max_depth", 5),
        )
        return result

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

    elif name == "export_catalog":
        from data_cataloger.export.exporter import CatalogExporter

        exporter = CatalogExporter(repo)
        export_format = args.get("format", "json")

        if export_format == "json":
            content = exporter.export_json(args["database_name"])
        elif export_format == "yaml":
            content = exporter.export_yaml(args["database_name"])
        elif export_format == "markdown":
            content = exporter.export_markdown(args["database_name"])
        else:
            return {
                "error": True,
                "code": "INVALID_FORMAT",
                "message": f"Invalid format: {export_format}",
            }

        return {
            "format": export_format,
            "content": content,
        }

    else:
        return {
            "error": True,
            "code": "UNKNOWN_TOOL",
            "message": f"Unknown tool: {name}",
        }


def _get_neighbors(
    driver: Any,
    table_name: str,
    database_name: str,
    direction: str = "both",
) -> dict:
    """Get a table and its directly connected neighbors."""
    if direction == "outgoing":
        query = """
        MATCH (t:Table {name: $table_name, database: $database_name})
        OPTIONAL MATCH (t)-[r:REFERENCES_VIA]->(neighbor:Table)
        RETURN t.name AS table_name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               collect(DISTINCT {
                   name: neighbor.name,
                   relationship: 'references',
                   fk_column: r.fk_column,
                   referenced_column: r.referenced_column
               }) AS neighbors
        """
    elif direction == "incoming":
        query = """
        MATCH (t:Table {name: $table_name, database: $database_name})
        OPTIONAL MATCH (neighbor:Table)-[r:REFERENCES_VIA]->(t)
        RETURN t.name AS table_name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               collect(DISTINCT {
                   name: neighbor.name,
                   relationship: 'referenced_by',
                   fk_column: r.fk_column,
                   referenced_column: r.referenced_column
               }) AS neighbors
        """
    else:
        query = """
        MATCH (t:Table {name: $table_name, database: $database_name})
        OPTIONAL MATCH (t)-[r1:REFERENCES_VIA]->(outgoing:Table)
        OPTIONAL MATCH (incoming:Table)-[r2:REFERENCES_VIA]->(t)
        WITH t,
             collect(DISTINCT {
                 name: outgoing.name,
                 relationship: 'references',
                 fk_column: r1.fk_column,
                 referenced_column: r1.referenced_column
             }) AS outgoing_neighbors,
             collect(DISTINCT {
                 name: incoming.name,
                 relationship: 'referenced_by',
                 fk_column: r2.fk_column,
                 referenced_column: r2.referenced_column
             }) AS incoming_neighbors
        RETURN t.name AS table_name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               outgoing_neighbors + incoming_neighbors AS neighbors
        """

    records, _, _ = driver.execute_query(
        query,
        table_name=table_name,
        database_name=database_name,
    )

    if not records:
        return {
            "error": True,
            "code": "TABLE_NOT_FOUND",
            "message": f"Table '{table_name}' not found",
        }

    record = records[0]
    neighbors = [n for n in record["neighbors"] if n.get("name") is not None]

    return {
        "table": record["table_name"],
        "description": record["description"],
        "sensitivity": record["sensitivity"],
        "neighbors": neighbors,
        "neighbor_count": len(neighbors),
    }


def _traverse_path(
    driver: Any,
    from_table: str,
    to_table: str,
    database_name: str,
    max_depth: int = 5,
) -> dict:
    """Find shortest path between two tables."""
    query = """
    MATCH (start:Table {name: $from_table, database: $database_name}),
          (end:Table {name: $to_table, database: $database_name}),
          path = shortestPath((start)-[:REFERENCES_VIA*1..$max_depth]-(end))
    RETURN [node IN nodes(path) | node.name] AS tables,
           [rel IN relationships(path) | {
               fk_column: rel.fk_column,
               referenced_column: rel.referenced_column
           }] AS relationships,
           length(path) AS path_length
    """

    records, _, _ = driver.execute_query(
        query,
        from_table=from_table,
        to_table=to_table,
        database_name=database_name,
        max_depth=max_depth,
    )

    if not records:
        return {
            "from_table": from_table,
            "to_table": to_table,
            "path_exists": False,
            "message": f"No path found between '{from_table}' and '{to_table}'",
        }

    record = records[0]
    return {
        "from_table": from_table,
        "to_table": to_table,
        "path_exists": True,
        "tables": record["tables"],
        "relationships": record["relationships"],
        "path_length": record["path_length"],
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
