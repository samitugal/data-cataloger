# Data Cataloger

AI-powered database documentation and metadata management system.

## Overview

Data Cataloger helps teams understand large, undocumented databases by using AI to infer table purposes, data sensitivity levels, and usage patterns. It stores enriched metadata in a Neo4j knowledge graph, enabling semantic search and relationship exploration.

## Key Features

- **Multi-Database Support**: Catalog multiple PostgreSQL/MySQL databases
- **AI-Powered Analysis**: LLM-generated descriptions, sensitivity classification, example queries
- **Semantic Search**: Vector similarity search using OpenAI embeddings
- **Knowledge Graph**: Neo4j storage with MetadataRepository as central index
- **MCP Integration**: 11 tools for AI assistant integration (Claude, Windsurf)
- **Export/Import**: JSON, YAML, Markdown documentation export
- **Interactive UI**: Real-time cataloging visualization with relationship canvas

## Requirements

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL or MySQL database (for cataloging)
- Neo4j database (for catalog storage)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd data-cataloger
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Configure database connections (details TBD)

## Quick Start

```bash
# Run the cataloger (implementation in progress)
uv run data-cataloger
```

## Project Structure

The project follows a modular architecture with five core modules:

- **connection/**: Database connection handling and credential management
- **schema/**: Schema extraction from PostgreSQL and MySQL databases
- **cataloging/**: LLM-powered analysis of table purposes and relationships
- **storage/**: Neo4j graph storage for catalog data
- **web/**: Web interface for catalog visualization and search

## Graph Structure

Data is stored in Neo4j with a hierarchical structure:

```
(MetadataRepository {name: 'default'})
    │
    └──[:CONTAINS_DATABASE]──> (Database {name, type})
                                    │
                                    └──[:HAS_TABLE]──> (Table {name, description, sensitivity, embedding})
                                    │
                                    └──[:REFERENCES_VIA]──> (Table) [FK relationships]
```

## MCP Server

Data Cataloger includes an MCP (Model Context Protocol) server for AI assistant integration.

### Available Tools (11 total)

| Tool | Description |
|------|-------------|
| `list_databases` | List all cataloged databases (call first!) |
| `list_tables` | List all cataloged tables in a database |
| `get_table` | Get table details with FK relationships |
| `search_tables` | Keyword search in descriptions |
| `filter_by_sensitivity` | Filter by sensitivity (PII, financial, internal, public) |
| `get_relationships` | Get FK relationships for a table |
| `get_graph` | Full relationship graph for visualization |
| `get_neighbors` | Get table with connected neighbors |
| `traverse_path` | Find path between two tables |
| `semantic_search` | Vector similarity search using embeddings |
| `export_catalog` | Export in JSON/YAML/Markdown format |

### Onboarding

When no databases are cataloged, MCP tools return helpful error messages:
```json
{
  "error": true,
  "code": "DATABASE_NOT_FOUND",
  "message": "Database 'xyz' not found in catalog.",
  "available_databases": ["northwind"],
  "hint": "Available: ['northwind']. Add at http://localhost:8000"
}
```

### Configuration

Add to your MCP client config (e.g., Claude Desktop, Windsurf):

**Step 1: Build the Docker image**
```bash
docker build -f Dockerfile.mcp -t data-cataloger-mcp .
```

**Step 2: Add to your MCP client config**

```json
{
  "mcpServers": {
    "data-cataloger": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "NEO4J_URI=bolt://host.docker.internal:7687",
        "-e", "NEO4J_USER=neo4j",
        "-e", "NEO4J_PASSWORD=password",
        "-e", "OPENAI_API_KEY=sk-...",
        "data-cataloger-mcp"
      ]
    }
  }
}
```

> **Note:** Replace `sk-...` with your actual OpenAI API key.

### Running Standalone

```bash
make mcp-server
# Server runs on http://localhost:8001
# SSE endpoint: /sse
# Messages endpoint: /messages/
```

## Development

This project uses:
- Python 3.12 (pinned in `.python-version`)
- uv for dependency management
- src layout for clean package structure

### Makefile Commands

```bash
make install        # Install dependencies
make dev            # Start backend server
make dev-force      # Kill existing & start server
make frontend-dev   # Start frontend server
make docker-up      # Start all services
make test           # Run tests
make lint           # Lint code
make mcp-server     # Start MCP server
```

## License

TBD
