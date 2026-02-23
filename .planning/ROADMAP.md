# Roadmap: Automated-Data-Cataloger

## Overview

This roadmap takes a legacy database from undocumented mystery to fully-cataloged knowledge graph. We start by establishing project foundations, then build capabilities to connect to databases, extract schema metadata, analyze tables with LLM agents, store enriched catalog data in Neo4j, and finally provide a web interface for visualization and exploration. Each phase delivers a complete, verifiable capability that moves us closer to the goal: automatically documenting 200+ table databases without manual effort.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Project Setup** - Establish development foundation and tooling
- [ ] **Phase 2: Database Connection** - Enable secure connection to PostgreSQL and MySQL databases
- [ ] **Phase 3: Schema Analysis** - Extract and analyze database metadata and relationships
- [ ] **Phase 4: LLM Cataloging Engine** - Build AI-powered table analysis with context awareness
- [x] **Phase 5: Graph Storage** - Store catalog data in Neo4j as queryable knowledge graph
- [ ] **Phase 6: Web Interface** - Provide real-time progress tracking and relationship visualization

## Phase Details

### Phase 1: Project Setup
**Goal**: Development environment and project foundation are ready for implementation
**Depends on**: Nothing (first phase)
**Requirements**: None (foundational work)
**Success Criteria** (what must be TRUE):
  1. Project repository exists with Python environment and dependency management
  2. Development tooling (linting, formatting, testing framework) is configured and working
  3. CI/CD pipeline runs basic checks on commits
  4. Project structure supports modular development (separate modules for connection, schema, cataloging, storage, web)
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Initialize project structure with uv and src layout (completed 2026-02-21)
- [ ] 01-02-PLAN.md — Configure development tooling and CI/CD pipeline

### Phase 2: Database Connection
**Goal**: Users can connect to target databases and verify connectivity
**Depends on**: Phase 1
**Requirements**: CONN-01, CONN-02, CONN-03, CONN-04, CONN-05
**Success Criteria** (what must be TRUE):
  1. User can provide database credentials through configuration or input
  2. System successfully connects to PostgreSQL databases and reports status
  3. System successfully connects to MySQL/MariaDB databases and reports status
  4. Connection failures display clear error messages (wrong credentials, network issues, etc.)
  5. Database credentials are encrypted or stored securely (not in plain text)
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Configuration and credential management with Pydantic and keyring
- [ ] 02-02-PLAN.md — PostgreSQL and MySQL connectors with factory pattern

### Phase 3: Schema Analysis
**Goal**: System extracts complete schema metadata and calculates table processing order
**Depends on**: Phase 2
**Requirements**: SCHM-01, SCHM-02, SCHM-03, SCHM-04, SCHM-05, SCHM-06
**Success Criteria** (what must be TRUE):
  1. System retrieves all tables from connected database
  2. For each table, system extracts columns with data types, primary keys, and foreign keys
  3. System builds dependency graph from foreign key relationships
  4. System calculates dependency ranking (tables with no FK dependencies rank highest)
  5. System outputs ordered table list from most independent to most dependent
**Plans**: 5 plans

Plans:
- [ ] 03-01-PLAN.md — Schema metadata dataclasses with immutable models
- [ ] 03-02-PLAN.md — PostgreSQL schema extractor using information_schema
- [ ] 03-03-PLAN.md — MySQL schema extractor using INFORMATION_SCHEMA
- [ ] 03-04-PLAN.md — Dependency graph builder with topological sort
- [ ] 03-05-PLAN.md — Schema introspector coordinator for complete analysis

### Phase 4: LLM Cataloging Engine
**Goal**: LLM agent analyzes tables and generates rich catalog entries with context
**Depends on**: Phase 3
**Requirements**: CATL-01, CATL-02, CATL-03, CATL-04, CATL-05, CATL-06, CATL-07
**Success Criteria** (what must be TRUE):
  1. LLM agent receives table metadata (name, columns, data types, relationships) and generates business description
  2. LLM classifies data sensitivity for each table (PII, financial, public, internal)
  3. LLM generates example SQL queries relevant to each table's purpose
  4. When analyzing dependent tables, LLM can reference already-cataloged parent tables for context
  5. System processes tables in dependency order (independent tables first)
  6. Cataloging uses OpenAI GPT-4 API for all LLM operations
**Plans**: 4 plans

Plans:
- [x] 04-01-PLAN.md — Catalog models and state management with Pydantic
- [x] 04-02-PLAN.md — OpenAI client wrapper with retry logic
- [x] 04-03-PLAN.md — Prompt templates and builder for context-aware analysis
- [x] 04-04-PLAN.md — Cataloging agent orchestrator for sequential processing

### Phase 5: Graph Storage
**Goal**: Catalog data persists in Neo4j as queryable knowledge graph
**Depends on**: Phase 4
**Requirements**: GRPH-01, GRPH-02, GRPH-03, GRPH-04, GRPH-05
**Success Criteria** (what must be TRUE):
  1. Neo4j database is configured and accessible from application
  2. Each cataloged table creates a node with properties (name, description, sensitivity classification)
  3. Foreign key relationships create edges between table nodes in the graph
  4. Example queries are stored as properties on table nodes
  5. Application can query Neo4j to retrieve catalog information for any table
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Neo4j config, Docker compose, and Neo4jWriter with MERGE upsert (completed 2026-02-23)
- [x] 05-02-PLAN.md — GraphRepository with read query methods (completed 2026-02-23)
- [x] 05-03-PLAN.md — Pipeline integration, storage public API, and tests (completed 2026-02-23)

### Phase 6: Web Interface
**Goal**: Users can monitor cataloging progress and explore table relationships visually
**Depends on**: Phase 5
**Requirements**: WEBI-01, WEBI-02, WEBI-03, WEBI-04, WEBI-05
**Success Criteria** (what must be TRUE):
  1. Web UI displays complete list of tables from connected database
  2. During cataloging, UI shows real-time progress (which tables are complete, in progress, or pending)
  3. UI renders interactive graph visualization of table relationships
  4. Clicking on a table node displays its catalog details (description, sensitivity, example queries)
  5. Visual indicators distinguish processed tables from pending ones
**Plans**: 5 plans

Plans:
- [ ] 06-01-PLAN.md — FastAPI setup, CORS, static files, health endpoint
- [ ] 06-02-PLAN.md — Table list and detail API endpoints
- [ ] 06-03-PLAN.md — Graph data API for Cytoscape.js
- [ ] 06-04-PLAN.md — Frontend table list and detail views
- [ ] 06-05-PLAN.md — Graph visualization and SSE progress tracking

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Setup | 1/2 | In Progress | - |
| 2. Database Connection | 0/2 | Not started | - |
| 3. Schema Analysis | 4/5 | In Progress|  |
| 4. LLM Cataloging Engine | 4/4 | Complete | 2026-02-23 |
| 5. Graph Storage | 3/3 | Complete | 2026-02-23 |
| 6. Web Interface | 0/5 | Not started | - |

---
*Created: 2025-02-21*
*Last updated: 2026-02-23*
