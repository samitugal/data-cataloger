# Data Cataloger

Automatically document legacy databases using LLM-powered analysis.

## Overview

Data Cataloger helps teams understand large, undocumented databases by using AI to infer table purposes, data sensitivity levels, and usage patterns. Instead of manually documenting hundreds of tables, the tool analyzes schema metadata and relationships to generate comprehensive catalog documentation.

## Key Features

- **Multi-database Support**: Works with PostgreSQL and MySQL databases
- **AI-Powered Analysis**: Uses LLM to infer table purposes and relationships
- **Graph Storage**: Stores catalog data in Neo4j to preserve table relationships
- **Web Visualization**: Interactive interface for browsing and searching catalog data
- **Intelligent Processing**: Analyzes independent tables first to provide context for dependent tables

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

## MCP Server

Data Cataloger includes an MCP (Model Context Protocol) server for AI assistant integration.

### Available Tools

| Tool | Description |
|------|-------------|
| `list_tables` | List all cataloged tables |
| `get_table` | Get table details with FK |
| `search_tables` | Keyword search in descriptions |
| `filter_by_sensitivity` | Filter by sensitivity level |
| `get_relationships` | Get FK relationships |
| `get_graph` | Full relationship graph |
| `get_neighbors` | Get table with connected neighbors |
| `traverse_path` | Find path between tables |
| `semantic_search` | Vector similarity search |
| `export_catalog` | Export in JSON/YAML/Markdown |

### Configuration

Add to your MCP client config (e.g., Claude Desktop, Windsurf):

**For Windsurf:**
```json
{
  "mcpServers": {
    "data-cataloger": {
      "command": "/path/to/data-cataloger/.venv/bin/python",
      "args": ["-m", "data_cataloger.mcp"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

**For Claude Desktop (supports cwd):**
```json
{
  "mcpServers": {
    "data-cataloger": {
      "command": "uv",
      "args": ["run", "python", "-m", "data_cataloger.mcp"],
      "cwd": "/path/to/data-cataloger",
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

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
