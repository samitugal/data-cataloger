# Data Cataloger - Project Context

## Project Overview

Data Cataloger is an AI-powered database cataloging system that automatically analyzes database schemas and generates rich metadata using LLM (GPT-4o). It stores the catalog in Neo4j graph database and provides a web interface for visualization.

## Current Status

- **Phase 1-6**: Complete ✅
- **Phase 7**: Frontend Application - ✅ Complete
- **Phase 8**: UI/UX Revamp - ✅ Complete
- **Phase 9**: MCP Server - ✅ Complete
- **Phase 10**: Semantic Search - ✅ Complete
- **Phase 11**: Export/Import - ✅ Complete
- **Phase 12**: Dynamic Database Discovery - ✅ Complete

## Tech Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database**: Neo4j (graph), PostgreSQL (source)
- **LLM**: OpenAI GPT-4o
- **Package Manager**: uv

### Frontend
- **Framework**: React 18 + TypeScript 5
- **Build**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **Graph**: Custom SVG Canvas (RelationshipCanvas)
- **Data Fetching**: TanStack Query

## Key Features

1. **Schema Introspection** - Analyzes PostgreSQL/MySQL schemas
2. **LLM Cataloging** - Generates descriptions, sensitivity labels, example queries
3. **Graph Storage** - Stores relationships in Neo4j
4. **Web UI** - Visualizes catalog with interactive graph
5. **Real-time Updates** - SSE for live cataloging progress

## Project Structure

```
data-cataloger/
├── src/data_cataloger/
│   ├── cataloging/      # LLM-powered cataloging
│   ├── connection/      # Database connectors
│   ├── schema/          # Schema introspection
│   ├── storage/         # Neo4j writer
│   └── web/             # FastAPI application
├── frontend/            # React frontend (Phase 7)
├── docker/              # Docker init scripts
├── .planning/           # Planning documents
│   └── phases/
│       ├── 01-06/       # Completed phases
│       └── 07-frontend/ # Current phase
└── docker-compose.yml   # Full stack deployment
```

## Running the Project

```bash
# Start all services
docker compose up -d

# Access points
- Web UI: http://localhost:8000
- Neo4j Browser: http://localhost:7474
- API Docs: http://localhost:8000/docs
```

## Phase 7 Plans

| Plan | Description | Status |
|------|-------------|--------|
| 01 | Project Setup | ✅ Complete |
| 02 | Core Infrastructure | ✅ Complete |
| 03 | Shared Components | ✅ Complete |
| 04 | Graph Feature | ✅ Complete |
| 05 | Tables Feature | ✅ Complete |
| 06 | Catalog Feature | ✅ Complete |
| 07 | Build & Fix | ✅ Complete |
| 08 | Docker Integration | ✅ Complete |

## Phase 8 - UI/UX Revamp

| Feature | Description | Status |
|---------|-------------|--------|
| Card-based Layout | Tables as interactive cards | ✅ Complete |
| Scattered Canvas | Random positioning with jitter | ✅ Complete |
| Interactive Edges | Neo4j-style relationship lines | ✅ Complete |
| Orthogonal Routing | 90-degree edge paths | ✅ Complete |
| Edge Animation | Pop-in effect after cards | ✅ Complete |
| Timer Fix | Stop on cataloging complete | ✅ Complete |
| Dynamic Popups | Text-based popup sizing | ✅ Complete |

## Key Components

| Component | Description |
|-----------|-------------|
| `RelationshipCanvas` | Full-page canvas with scattered cards and SVG edges |
| `InteractiveEdge` | Orthogonal edge with hover tooltip and animation |
| `LiveTableCard` | Table card with sensitivity badge and FK preview |
| `CatalogStep` | Wizard step with dashboard and real-time updates |

## Key Decisions

1. **Feature-based structure** - Self-contained feature modules
2. **Zustand for state** - Simple, TypeScript-friendly
3. **SSE for real-time** - Server-Sent Events for live updates
4. **Custom SVG Canvas** - Replaced Cytoscape.js with custom implementation
5. **Orthogonal edges** - 90-degree routing around cards

## Environment Variables

```env
# Backend
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
DATABASE_NAME=northwind
OPENAI_API_KEY=sk-...

# Frontend
VITE_API_URL=http://localhost:8000
```

## Makefile Commands

```bash
make install          # Python dependencies
make dev              # Backend server
make frontend-dev     # Frontend server
make docker-up        # Start all services
make test             # Run tests
make lint             # Lint code
```

## Phase 9 & 10 - MCP Server & Semantic Search

### MCP Server (Phase 9)
- stdio transport for Windsurf/Claude Desktop
- Docker image for portable deployment
- Stateful Neo4j connection

### MCP Tools (11 total)
| Tool | Description |
|------|-------------|
| `list_databases` | List all cataloged databases (call first!) |
| `list_tables` | List all cataloged tables |
| `get_table` | Get table details with FK |
| `search_tables` | Keyword search |
| `filter_by_sensitivity` | Filter by sensitivity |
| `get_relationships` | Get FK relationships |
| `get_graph` | Full relationship graph |
| `get_neighbors` | Get table with connected neighbors |
| `traverse_path` | Find path between tables |
| `semantic_search` | Vector similarity search |
| `export_catalog` | Export in JSON/YAML/Markdown |

### MCP Onboarding
- `list_databases` tool shows available databases
- Tools return helpful errors if database not found
- Error includes available databases and setup URL

### Semantic Search (Phase 10)
- OpenAI `text-embedding-3-small` (1536 dim)
- Neo4j vector index with cosine similarity
- Embeddings generated during cataloging

## Phase 11 - Export/Import

| Feature | Status |
|---------|--------|
| JSON Export | ✅ Complete |
| YAML Export | ✅ Complete |
| Markdown Documentation | ✅ Complete |
| JSON/YAML Import | ✅ Complete |
| API Endpoints | ✅ Complete |
| MCP Tool | ✅ Complete |

## Phase 12 - Dynamic Database Discovery

| Feature | Status |
|---------|--------|
| Database Discovery Endpoint | ✅ Complete |
| Frontend Database Selection UI | ✅ Complete |
| "All Databases" Cataloging | ✅ Complete |
| SSE Parameter Fix (database_name) | ✅ Complete |
| Real-time Table Rendering | ✅ Complete |

## Graph Structure

```
(MetadataRepository {name: 'default'})
    │
    └──[:CONTAINS_DATABASE]──> (Database {name, type})
                                    │
                                    └──[:HAS_TABLE]──> (Table)
                                    │
                                    └──[:REFERENCES_VIA]──> (Table)
```

### Node Properties

| Node | Properties |
|------|------------|
| MetadataRepository | name, created_at |
| Database | name, type, created_at |
| Table | name, database, description, sensitivity, example_queries, embedding, created_at, updated_at |

### Relationships

| Relationship | Description |
|--------------|-------------|
| CONTAINS_DATABASE | MetadataRepository → Database |
| HAS_TABLE | Database → Table |
| REFERENCES_VIA | Table → Table (FK with fk_column, referenced_column, constraint_name) |

## Code Quality

| Metric | Value |
|--------|-------|
| Total Files | 41 |
| Lines of Code | 4,418 |
| Test Coverage | 66% |
| Tests Passing | 186/186 |
| Lint Errors | 0 |
| Type Errors | 0 |

## Last Updated

2026-02-27 - Phase 12: Dynamic Database Discovery + SSE fixes
