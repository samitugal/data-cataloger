# Phase 9: MCP Server Implementation

## Objective

Add Model Context Protocol (MCP) server support to Data Cataloger, allowing AI assistants (Claude, etc.) to access enriched database metadata through standardized tools.

## Overview

MCP (Model Context Protocol) is a standard that connects AI systems with external tools and data sources. By implementing an MCP server, users can query their database catalog directly from AI assistants.

## Proposed Tools

### 1. Connection Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `connect_database` | Connect to a database | host, port, database, username, password, db_type |
| `disconnect_database` | Disconnect from database | - |
| `get_connection_status` | Check connection status | - |

### 2. Catalog Query Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_tables` | List all cataloged tables | database_name |
| `get_table` | Get table details | table_name, database_name |
| `search_tables` | Search tables by keyword | keyword, database_name |
| `filter_by_sensitivity` | Filter tables by sensitivity | sensitivity, database_name |

### 3. Relationship Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_relationships` | Get FK relationships for a table | table_name, database_name |
| `get_graph` | Get full relationship graph | database_name |

### 4. Cataloging Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `start_cataloging` | Start cataloging process | database_name |
| `get_cataloging_status` | Get cataloging progress | - |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   AI Assistant                       │
│              (Claude, GPT, etc.)                     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼ MCP Protocol (stdio/SSE)
┌─────────────────────────────────────────────────────┐
│                   MCP Server                         │
│              (data-cataloger-mcp)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Tools     │  │  Resources  │  │   Prompts   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Existing Backend                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Repository  │  │  Cataloging │  │  Connection │ │
│  │  (Neo4j)    │  │   Engine    │  │   Manager   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Transport | **SSE** | Web-based, browser/IDE compatible |
| Scope | **Read-only** | Only query existing metadata |
| State | **Stateful** | Maintain Neo4j connection |
| Auth | Environment variables | Neo4j credentials via env |

## Implementation Approach

- Use `mcp` Python SDK with SSE transport
- Stateful server maintains Neo4j connection
- Read-only tools for catalog queries
- Semantic search integration (Phase 10)

## File Structure (Proposed)

```
src/data_cataloger/
├── mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server setup
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── connection.py  # Connection tools
│   │   ├── catalog.py     # Catalog query tools
│   │   └── relationships.py # Relationship tools
│   └── resources/
│       └── __init__.py    # MCP resources (optional)
```

## Dependencies

- `mcp` - Official MCP Python SDK
- Existing: `neo4j`, `pydantic`, etc.

## Questions to Clarify

1. **Transport**: stdio (for CLI) or SSE (for web)?
2. **Authentication**: Should tools require auth?
3. **Scope**: Read-only or include cataloging?
4. **Resources**: Should we expose tables as MCP resources?
5. **State**: Stateful (maintain connection) or stateless?

## Timeline

| Step | Description | Estimate |
|------|-------------|----------|
| 1 | Setup MCP server skeleton | 15 min |
| 2 | Implement catalog query tools | 20 min |
| 3 | Implement relationship tools | 15 min |
| 4 | Implement connection tools | 20 min |
| 5 | Testing & documentation | 15 min |
| **Total** | | **~85 min** |

## Success Criteria

- [ ] MCP server starts without errors
- [ ] Tools are discoverable by AI assistants
- [ ] `list_tables` returns cataloged tables
- [ ] `get_table` returns table details with description
- [ ] `search_tables` finds tables by keyword
- [ ] `get_relationships` returns FK relationships
