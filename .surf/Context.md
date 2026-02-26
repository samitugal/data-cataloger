# Data Cataloger - Project Context

## Project Overview

Data Cataloger is an AI-powered database cataloging system that automatically analyzes database schemas and generates rich metadata using LLM (GPT-4o). It stores the catalog in Neo4j graph database and provides a web interface for visualization.

## Current Status

- **Phase 1-6**: Complete ✅
- **Phase 7**: Frontend Application - Planning Complete, Implementation Pending

## Tech Stack

### Backend
- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database**: Neo4j (graph), PostgreSQL (source)
- **LLM**: OpenAI GPT-4o
- **Package Manager**: uv

### Frontend (Planned)
- **Framework**: React 18 + TypeScript 5
- **Build**: Vite
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: Zustand
- **Graph**: Cytoscape.js
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
| 01 | Project Setup | Pending |
| 02 | Core Infrastructure | Pending |
| 03 | Shared Components | Pending |
| 04 | Graph Feature | Pending |
| 05 | Tables Feature | Pending |
| 06 | Catalog Feature | Pending |
| 07 | Polish & Testing | Pending |
| 08 | Docker Integration | Pending |

## Key Decisions

1. **Feature-based structure** - Self-contained feature modules
2. **Zustand for state** - Simple, TypeScript-friendly
3. **SSE for real-time** - Server-Sent Events for live updates
4. **Cytoscape.js** - Mature graph visualization library

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

## Last Updated

2026-02-26 - Phase 7 Frontend Planning Complete
