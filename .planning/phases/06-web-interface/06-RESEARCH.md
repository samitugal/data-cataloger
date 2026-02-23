# Phase 6: Web Interface - Research

## Overview

Phase 6 delivers a web interface for monitoring cataloging progress and exploring table relationships visually. The interface must display tables, show real-time progress, and render an interactive graph visualization.

## Requirements Analysis

| ID | Requirement | Complexity | Approach |
|----|-------------|------------|----------|
| WEBI-01 | Web UI displays list of tables | Low | REST endpoint + HTML table |
| WEBI-02 | Real-time progress during cataloging | Medium | SSE for unidirectional updates |
| WEBI-03 | Interactive graph visualization | High | Cytoscape.js with Neo4j data |
| WEBI-04 | Table detail view | Low | REST endpoint + detail panel |
| WEBI-05 | Visual indicators for status | Low | CSS classes based on state |

## Technology Decisions

### Backend Framework: FastAPI

**Why FastAPI over Flask:**
- Native async/await support (critical for SSE)
- Built-in OpenAPI documentation
- Pydantic integration (already in project)
- Better performance (15-20K req/s vs 4-5K)
- WebSocket/SSE support without extensions

**Alternatives considered:**
- Flask: Would need flask-sse, gevent for async
- Django: Overkill for API-focused interface

### Real-time Updates: Server-Sent Events (SSE)

**Why SSE over WebSocket:**
- Unidirectional (server → client) is sufficient
- Simpler implementation
- Native browser support (EventSource API)
- Auto-reconnection built-in
- HTTP-based (no protocol upgrade)

**Use case:** Progress updates during cataloging
- Table started processing
- Table completed
- Error notifications

### Graph Visualization: Cytoscape.js

**Why Cytoscape.js:**
- Mature library (10+ years)
- Neo4j-friendly (neovis.js built on it)
- Handles 10K+ nodes efficiently
- Touch/mobile support
- Rich layout algorithms (cola, dagre, cose)
- Extensive styling options

**Alternatives considered:**
- D3.js: Lower-level, more code required
- vis.js: Good but less Neo4j integration
- Sigma.js: WebGL-based, overkill for <500 nodes

### Frontend: Vanilla JS + Tailwind CSS

**Why minimal frontend:**
- No build step required
- Fast initial load
- Sufficient for v1 scope
- Easy to maintain
- CDN-delivered dependencies

**Stack:**
- HTML5 templates
- Tailwind CSS (CDN)
- Cytoscape.js (CDN)
- Vanilla JavaScript (ES6+)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Table List  │  │ Detail View │  │ Graph (Cytoscape)│ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │ HTTP/SSE                     │
└──────────────────────────┼──────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────┐
│                    FastAPI Server                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ /api/tables │  │ /api/graph  │  │ /api/progress   │  │
│  │   (REST)    │  │   (REST)    │  │    (SSE)        │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
│         │                │                   │           │
│         └────────────────┼───────────────────┘           │
│                          │                               │
│              ┌───────────┴───────────┐                   │
│              │   GraphRepository     │                   │
│              └───────────┬───────────┘                   │
└──────────────────────────┼───────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │    Neo4j    │
                    └─────────────┘
```

## API Design

### REST Endpoints

```
GET  /api/tables                    → List all cataloged tables
GET  /api/tables/{name}             → Get single table details
GET  /api/tables/search?q={query}   → Search tables by keyword
GET  /api/tables/sensitivity/{level} → Filter by sensitivity
GET  /api/graph                     → Full graph for visualization
GET  /api/graph/{table}/neighbors   → Table + direct relationships
```

### SSE Endpoint

```
GET  /api/progress                  → SSE stream for cataloging progress

Events:
- cataloging:started    {total_tables: N}
- table:processing      {table_name: "users", index: 1}
- table:completed       {table_name: "users", index: 1}
- table:error           {table_name: "users", error: "..."}
- cataloging:completed  {total_tables: N, duration_seconds: X}
```

### Response Formats

```json
// GET /api/tables
{
  "tables": [
    {
      "name": "users",
      "description": "Customer account information",
      "sensitivity": "PII",
      "example_queries": ["SELECT * FROM users WHERE id = ?"]
    }
  ],
  "total": 42
}

// GET /api/graph
{
  "nodes": [
    {"id": "users", "label": "users", "sensitivity": "PII"}
  ],
  "edges": [
    {"source": "orders", "target": "users", "label": "user_id → id"}
  ]
}
```

## Dependencies

### New Python Packages

```toml
# pyproject.toml additions
"fastapi>=0.115.0",
"uvicorn[standard]>=0.34.0",
"sse-starlette>=2.2.0",
```

### Frontend CDN Dependencies

```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Cytoscape.js -->
<script src="https://unpkg.com/cytoscape@3.30.0/dist/cytoscape.min.js"></script>

<!-- Layout extensions -->
<script src="https://unpkg.com/cytoscape-cola@2.5.1/cytoscape-cola.js"></script>
```

## File Structure

```
src/data_cataloger/web/
├── __init__.py          # Module exports
├── app.py               # FastAPI application factory
├── routes/
│   ├── __init__.py
│   ├── tables.py        # /api/tables endpoints
│   ├── graph.py         # /api/graph endpoints
│   └── progress.py      # /api/progress SSE endpoint
├── schemas.py           # Pydantic response models
├── dependencies.py      # FastAPI dependencies (Neo4j driver)
└── static/
    ├── index.html       # Main page
    ├── css/
    │   └── styles.css   # Custom styles (minimal)
    └── js/
        ├── app.js       # Main application logic
        ├── table-list.js
        ├── table-detail.js
        ├── graph.js     # Cytoscape.js integration
        └── progress.js  # SSE client
```

## Plan Breakdown

### 06-01: FastAPI Setup + Basic Routes
- Install FastAPI, uvicorn, sse-starlette
- Create app factory with CORS
- Health check endpoint
- Static file serving
- Basic HTML shell

### 06-02: Table List + Detail API
- `/api/tables` endpoint using GraphRepository
- `/api/tables/{name}` endpoint
- Search and filter endpoints
- Pydantic response schemas

### 06-03: Graph Data API
- `/api/graph` endpoint for full graph
- Transform GraphRepository output to Cytoscape format
- `/api/graph/{table}/neighbors` for focused view

### 06-04: Frontend Table Views
- Table list component with Tailwind styling
- Detail panel with catalog information
- Search/filter UI
- Responsive layout

### 06-05: Graph Visualization + SSE Progress
- Cytoscape.js integration
- Graph layout and styling
- Node click → detail view
- SSE progress stream
- Progress indicator UI

## Testing Strategy

### Unit Tests
- Route handlers with mocked GraphRepository
- Response schema validation
- SSE event formatting

### Integration Tests
- Full API flow with test Neo4j container
- Static file serving
- CORS headers

### Manual Testing
- Browser compatibility (Chrome, Firefox, Safari)
- Mobile responsiveness
- Graph interaction (zoom, pan, click)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large graph performance | High | Pagination, lazy loading, limit to 500 nodes |
| SSE connection drops | Medium | Auto-reconnect in EventSource, heartbeat |
| Neo4j connection pool | Medium | Dependency injection, connection lifecycle |
| Browser compatibility | Low | Modern browsers only, polyfills if needed |

## Success Metrics

- [ ] All 5 WEBI requirements satisfied
- [ ] Page load < 2 seconds
- [ ] Graph renders 200+ nodes smoothly
- [ ] SSE updates within 100ms of event
- [ ] Mobile-responsive layout

---
*Research completed: 2026-02-23*
