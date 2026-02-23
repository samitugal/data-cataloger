# Requirements: Automated-Data-Cataloger

**Defined:** 2025-02-20
**Core Value:** Automatically document undocumented legacy databases using LLM-powered analysis

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Database Connection

- [x] **CONN-01**: User can enter database connection credentials (host, port, username, password, database name)
- [x] **CONN-02**: System supports PostgreSQL database connections
- [x] **CONN-03**: System supports MySQL/MariaDB database connections
- [x] **CONN-04**: System tests connection and displays success or failure feedback
- [x] **CONN-05**: System securely handles database credentials (not stored in plain text)

### Schema Analysis

- [x] **SCHM-01**: System extracts all tables from connected database
- [x] **SCHM-02**: System extracts columns with data types for each table
- [x] **SCHM-03**: System extracts primary key constraints
- [x] **SCHM-04**: System extracts foreign key relationships between tables
- [x] **SCHM-05**: System calculates dependency ranking based on FK relationships
- [x] **SCHM-06**: System orders tables from most independent to most dependent

### LLM Cataloging

- [x] **CATL-01**: LLM agent analyzes each table based on metadata (name, columns, relationships)
- [x] **CATL-02**: LLM generates business description for each table (what it represents, business process)
- [x] **CATL-03**: LLM classifies data sensitivity for each table (PII, financial, public, internal)
- [x] **CATL-04**: LLM generates example SQL queries for each table
- [x] **CATL-05**: LLM agent can reference already-cataloged tables for context during analysis
- [x] **CATL-06**: System processes tables in dependency order (independent first)
- [x] **CATL-07**: System uses OpenAI GPT-4 API for LLM analysis

### Graph Storage

- [ ] **GRPH-01**: System stores catalog data in Neo4j graph database
- [ ] **GRPH-02**: Each table is represented as a node with properties (name, description, sensitivity)
- [ ] **GRPH-03**: FK relationships are represented as edges between table nodes
- [ ] **GRPH-04**: Example queries are stored as properties on table nodes
- [ ] **GRPH-05**: System can query Neo4j to retrieve catalog information

### Web Interface

- [ ] **WEBI-01**: Web UI displays list of tables in the database
- [ ] **WEBI-02**: Web UI shows real-time progress during cataloging process
- [ ] **WEBI-03**: Web UI visualizes table relationships as a graph
- [ ] **WEBI-04**: Web UI displays catalog details for each table (description, sensitivity, queries)
- [ ] **WEBI-05**: Web UI indicates which tables have been processed vs pending

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Database Support

- **EXTD-01**: Support for Oracle databases
- **EXTD-02**: Support for SQL Server databases
- **EXTD-03**: Support for multiple database connections in single session

### Advanced Analysis

- **ADVN-01**: Column-level descriptions and sensitivity classification
- **ADVN-02**: Data lineage tracking across tables
- **ADVN-03**: Automatic data quality assessment
- **ADVN-04**: Schema change detection and re-cataloging

### Collaboration

- **COLB-01**: User can edit/override LLM-generated descriptions
- **COLB-02**: Export catalog to documentation formats (Markdown, PDF)
- **COLB-03**: API access to catalog data

## Out of Scope

| Feature | Reason |
|---------|--------|
| Column-level descriptions | Table-level sufficient for v1; reduces complexity |
| Oracle/SQL Server support | Focus on PostgreSQL and MySQL first |
| Multi-database sessions | One database at a time simplifies flow |
| Data migration tools | Cataloging only, not data movement |
| Query execution from UI | Read-only catalog, not a query tool |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CONN-01 | Phase 2 | Complete |
| CONN-02 | Phase 2 | Complete |
| CONN-03 | Phase 2 | Complete |
| CONN-04 | Phase 2 | Complete |
| CONN-05 | Phase 2 | Complete |
| SCHM-01 | Phase 3 | Complete |
| SCHM-02 | Phase 3 | Complete |
| SCHM-03 | Phase 3 | Complete |
| SCHM-04 | Phase 3 | Complete |
| SCHM-05 | Phase 3 | Complete |
| SCHM-06 | Phase 3 | Complete |
| CATL-01 | Phase 4 | Complete |
| CATL-02 | Phase 4 | Complete |
| CATL-03 | Phase 4 | Complete |
| CATL-04 | Phase 4 | Complete |
| CATL-05 | Phase 4 | Complete |
| CATL-06 | Phase 4 | Complete |
| CATL-07 | Phase 4 | Complete |
| GRPH-01 | Phase 5 | Pending |
| GRPH-02 | Phase 5 | Pending |
| GRPH-03 | Phase 5 | Pending |
| GRPH-04 | Phase 5 | Pending |
| GRPH-05 | Phase 5 | Pending |
| WEBI-01 | Phase 6 | Pending |
| WEBI-02 | Phase 6 | Pending |
| WEBI-03 | Phase 6 | Pending |
| WEBI-04 | Phase 6 | Pending |
| WEBI-05 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2025-02-20*
*Last updated: 2025-02-21 after roadmap creation*
