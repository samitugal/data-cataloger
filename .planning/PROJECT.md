# Automated-Data-Cataloger

## What This Is

A tool that automatically documents undocumented legacy databases using LLM-powered analysis. Users connect to their database, and the system analyzes table relationships (PK-FK), then processes tables from most independent to most dependent, generating rich catalog entries stored in Neo4j as a knowledge graph.

## Core Value

Eliminate manual database documentation effort for large legacy databases (200+ tables) by using AI to infer table purposes, data sensitivity, and usage patterns from schema metadata and relationships.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can connect to PostgreSQL or MySQL/MariaDB with credentials
- [ ] System tests connection and provides success/failure feedback
- [ ] System extracts all tables and their PK-FK relationships
- [ ] System calculates dependency ranking (most independent → most dependent)
- [ ] LLM agent analyzes each table based on metadata and related tables
- [ ] Each table gets: business description, data sensitivity tag, example queries
- [ ] Catalog stored in Neo4j as graph (tables as nodes, relationships as edges)
- [ ] Web UI shows cataloging progress in real-time
- [ ] Web UI visualizes table relationships as they're processed

### Out of Scope

- Oracle/SQL Server support — focus on PostgreSQL and MySQL first
- Column-level descriptions — table-level is sufficient for v1
- Auto-migration of existing documentation — greenfield catalog only
- Multi-database analysis in single session — one database at a time

## Context

**Problem:** Legacy databases with 200+ tables have no documentation. Understanding what tables do requires reverse-engineering from column names, foreign keys, and guesswork. This blocks onboarding and application development.

**Solution approach:**
1. Connect to target database
2. Extract schema metadata (tables, columns, PKs, FKs, indexes)
3. Build dependency graph from FK relationships
4. Process tables topologically (independent first)
5. For each table: LLM agent analyzes metadata + can query related tables for context
6. Store enriched catalog in Neo4j for graph queries
7. Web UI for monitoring and exploration

**Why dependency ordering matters:** When analyzing a dependent table, the LLM already has context about its parent tables. Processing `orders` before `customers` would miss context.

**Dual-purpose descriptions:** Catalog serves both business users ("what does this table mean?") and developers ("how do I query this?"). Descriptions must bridge both needs for future application development.

## Constraints

- **LLM Provider**: OpenAI GPT-4 API
- **Graph Database**: Neo4j for catalog storage
- **Target Databases**: PostgreSQL, MySQL/MariaDB (v1)
- **Interface**: Web application
- **Database Size**: Must handle 200+ tables efficiently

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Neo4j over relational catalog | Graph structure naturally represents table relationships; enables relationship-based queries | — Pending |
| Process independent tables first | Gives LLM context about parent tables when analyzing children | — Pending |
| Table-level not column-level | Reduces scope; table purpose is more valuable than column details for understanding | — Pending |
| Agent-based LLM | May need to reference multiple tables during analysis; tools provide flexibility | — Pending |

---
*Last updated: 2025-02-20 after initialization*
