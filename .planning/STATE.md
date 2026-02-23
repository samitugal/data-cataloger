# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-02-20)

**Core value:** Eliminate manual database documentation effort for large legacy databases (200+ tables) by using AI to infer table purposes, data sensitivity, and usage patterns from schema metadata and relationships.
**Current focus:** Phase 6: Web Interface

## Current Position

Phase: 6 of 6 (Web Interface)
Plan: 0 of TBD
Status: Not Started
Last activity: 2026-02-23 — Completed Phase 5 (Graph Storage)

Progress: [████████░░] 83%

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: 4 minutes
- Total execution time: 1 hour

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-project-setup | 2 | 7 min | 3.5 min |
| 02-database-connection | 2 | 14 min | 7 min |
| 03-schema-analysis | 5 | 13 min | 2.6 min |
| 04-llm-cataloging-engine | 4 | 20 min | 5 min |
| 05-graph-storage | 3 | 12 min | 4 min |

**Recent Trend:**
- Last 5 plans: 04-03 (7 min), 04-04 (4 min), 05-01 (2 min), 05-02 (2 min), 05-03 (8 min)
- Trend: Phase 5 completed - full Neo4j storage integration

*Updated after each plan completion*
| Phase 02 P02 | 7 | 3 tasks | 7 files |
| Phase 03 P01 | 2 | 2 tasks | 3 files |
| Phase 03 P04 | 2 | 2 tasks | 2 files |
| Phase 03 P03 | 3 | 2 tasks | 2 files |
| Phase 03 P02 | 3 | 2 tasks | 5 files |
| Phase 03 P05 | 3 | 3 tasks | 2 files |
| Phase 04 P01 | 2 | 3 tasks | 2 files |
| Phase 04 P02 | 7 | 4 tasks | 5 files |
| Phase 04 P03 | 7 | 3 tasks | 2 files |
| Phase 04 P04 | 4 | 4 tasks | 3 files |
| Phase 05 P02 | 2 | 1 tasks | 1 files |
| Phase 05 P03 | 8 | 3 tasks | 8 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Neo4j for catalog storage (graph structure for relationships)
- Process independent tables first (provides LLM context for dependent tables)
- Table-level not column-level analysis (reduces v1 scope)
- Agent-based LLM approach (flexibility for multi-table references)
- Use uv instead of pip/poetry (modern tooling, fast resolution) - 01-01
- src layout over flat layout (prevents import issues) - 01-01
- Five-module architecture for separation of concerns - 01-01
- Use Ruff instead of Black + Flake8 + isort (modern unified tooling) - 01-02
- Enable strict mypy type checking from the start (disallow_untyped_defs=true) - 01-02
- Matrix testing for Python 3.11 and 3.12 (ensure broad compatibility) - 01-02
- Use astral-sh/setup-uv action for fast CI dependency installation - 01-02
- Configure mypy with --ignore-missing-imports for gradual typing adoption - 01-02
- Use Pydantic for configuration validation (type-safe with clear errors) - 02-01
- Use OS keyring for password storage (secure, no plain text) - 02-01
- Support environment variables with keyring fallback (flexible credential sourcing) - 02-01
- [Phase 02-02]: Use typing.Protocol for connector interface (structural subtyping)
- [Phase 02-02]: Install psycopg-binary for embedded libpq (no system deps)
- [Phase 02-02]: Add pytest pythonpath configuration for uv run imports
- [Phase 03-01]: Use frozen dataclasses instead of Pydantic for schema models (read-only metadata)
- [Phase 03-01]: Store raw data_type strings without normalization (LLM interprets types)
- [Phase 03-01]: Use tuple instead of list for collections (enforces immutability)
- [Phase 03-01]: Support composite foreign keys with ordinal_position field
- [Phase 03-02]: Add connection property to DatabaseConnector protocol for schema extraction
- [Phase 03-04]: Filter self-references in dependency graph (hierarchical tables not cycles)
- [Phase 03-04]: Return tuple (ordered_tables, cycle_nodes) for both success and error paths
- [Phase 03-04]: Use static_order() not prepare() for complete batch ordering
- [Phase 03-03]: Use CONSTRAINT_NAME='PRIMARY' for MySQL PK identification (not constraint_type)
- [Phase 03-03]: Filter FKs with REFERENCED_TABLE_NAME IS NOT NULL (critical for correctness)
- [Phase 03-03]: Use database name as schema parameter in MySQL (not 'public')
- [Phase 03-05]: Access connector.config with type ignore for database routing (clean API)
- [Phase 03-05]: Use set comprehension for unique referenced tables (deduplicates FK references)
- [Phase 03-05]: Default schema varies by database type (public for PostgreSQL, database name for MySQL)
- [Phase 04-01]: Use Literal types instead of Enum for OpenAI strict mode compatibility
- [Phase 04-01]: Separate Pydantic model (TableCatalog) from storage dataclass (CatalogEntry)
- [Phase 04-01]: CatalogState filters self-references and missing parents in get_parent_context
- [Phase 04-02]: Use OpenAI structured outputs with parse() method instead of create() with function calling
- [Phase 04-02]: Retry only on RateLimitError (not all exceptions) for predictable error handling
- [Phase 04-02]: Set retry to 6 attempts with 1-60s exponential backoff based on OpenAI recommendations
- [Phase 04-02]: Use type ignore for messages parameter (OpenAI types too restrictive for practical use)
- [Phase 04-02]: Raise ValueError on None response from OpenAI (defensive error handling)
- [Phase 04-03]: Separate system prompt from user prompts (consistent agent behavior)
- [Phase 04-03]: Include parent context in user prompts (dependency-aware analysis)
- [Phase 04-03]: Conditional prompt sections for PK, FK, parent context (reduce bloat)
- [Phase 04-04]: Process tables in dependency order from SchemaIntrospector (enables parent context)
- [Phase 04-04]: Reject circular dependencies with clear error (can't establish processing order)
- [Phase 04-04]: Use CatalogState for context accumulation (already-cataloged tables inform later analysis)
- [Phase 04-04]: Use assertion for Pydantic type narrowing (mypy strict compliance)
- [Phase 04-04]: Export only public API (agent, models) not implementation details (client, prompts)
- [Phase 05-02]: Return CatalogEntry domain objects not graph-specific DTOs (consistent with existing codebase)
- [Phase 05-02]: Filter stub nodes by checking description IS NOT NULL (uncataloged FK references excluded)
- [Phase 05-02]: Use two separate queries for get_full_graph (simpler than complex Cypher WITH/collect)
- [Phase 05-02]: Materialize Neo4j Result objects to lists before returning (prevents "Result consumed" errors)
- [Phase 05-03]: Use Protocol for CatalogWriter (structural subtyping, no inheritance required)
- [Phase 05-03]: Write failures log warning and continue cataloging (pipeline resilience)
- [Phase 05-03]: Derive database_name from first table's schema_name if not provided
- [Phase 05-03]: Export only 3 classes from storage module (clean public API)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-23
Stopped at: Completed Phase 5 (Graph Storage) - Ready for Phase 6
Resume file: .planning/phases/05-graph-storage/05-03-SUMMARY.md
