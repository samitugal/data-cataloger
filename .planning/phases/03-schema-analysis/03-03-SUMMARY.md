---
phase: 03-schema-analysis
plan: 03
subsystem: schema
tags: [mysql, information_schema, schema-extraction, uppercase-columns]
completed: 2026-02-22

dependencies:
  requires:
    - ColumnMetadata dataclass (from 03-01)
    - ForeignKeyMetadata dataclass (from 03-01)
    - DatabaseConnector protocol (from Phase 2)
  provides:
    - MySQLExtractor class with 4 extraction methods
  affects:
    - schema.introspector (will use MySQLExtractor for MySQL databases)
    - dependency graph builder (will process MySQL schema metadata)

tech_stack:
  added:
    - MySQL INFORMATION_SCHEMA views for metadata extraction
  patterns:
    - Uppercase column names in MySQL INFORMATION_SCHEMA (TABLE_NAME not table_name)
    - CONSTRAINT_NAME='PRIMARY' for primary key identification
    - REFERENCED_TABLE_NAME IS NOT NULL filter for FK extraction
    - Database name as schema parameter (MySQL doesn't use 'public')

key_files:
  created:
    - src/data_cataloger/schema/mysql.py (165 lines, MySQLExtractor class)
    - tests/schema/test_mysql.py (295 lines, 12 tests)
  modified: []

decisions:
  - key: Use CONSTRAINT_NAME='PRIMARY' instead of constraint_type
    rationale: MySQL INFORMATION_SCHEMA uses literal 'PRIMARY' as constraint name for PKs
    alternatives: [JOIN with table_constraints table like PostgreSQL]
    impact: Simpler query, MySQL-specific pattern

  - key: Filter foreign keys with REFERENCED_TABLE_NAME IS NOT NULL
    rationale: MySQL KEY_COLUMN_USAGE contains PKs, unique constraints, and FKs - NULL check distinguishes them
    alternatives: [Join with referential_constraints table]
    impact: Critical correctness fix - without this filter, PKs appear as FKs

  - key: Use database name as schema parameter
    rationale: MySQL uses database name instead of PostgreSQL-style schema namespaces
    alternatives: [Default to connector.config.database]
    impact: Caller must provide database name explicitly

metrics:
  duration_minutes: 3
  tasks_completed: 2
  tests_written: 12
  coverage_percent: 100
  lines_of_code: 460
---

# Phase 03 Plan 03: MySQL Schema Extractor Summary

**MySQL/MariaDB schema metadata extraction using INFORMATION_SCHEMA with uppercase column names and FK filtering**

## What Was Built

Implemented MySQLExtractor class that queries MySQL INFORMATION_SCHEMA views to extract complete schema metadata for MySQL and MariaDB databases:

1. **get_tables()**: Extracts base table names using TABLE_NAME filter with BASE TABLE type
2. **get_columns()**: Extracts column metadata with IS_NULLABLE conversion ('YES'/'NO' → boolean)
3. **get_primary_keys()**: Extracts primary key columns using CONSTRAINT_NAME='PRIMARY' filter
4. **get_foreign_keys()**: Extracts foreign key metadata with REFERENCED_TABLE_NAME IS NOT NULL filter

All methods use parameterized queries (%s placeholders) to prevent SQL injection and follow MySQL-specific INFORMATION_SCHEMA patterns (uppercase column names, different PK/FK identification).

## Tasks Completed

### Task 1: Create MySQL schema extractor
**Commit:** ce0a6d5
**Files:** src/data_cataloger/schema/mysql.py

Created MySQLExtractor class following 03-RESEARCH.md MySQL patterns:
- 4 extraction methods (get_tables, get_columns, get_primary_keys, get_foreign_keys)
- All SQL queries use uppercase INFORMATION_SCHEMA column names (TABLE_NAME, COLUMN_NAME, etc.)
- get_columns() converts IS_NULLABLE string 'YES'/'NO' to boolean True/False
- get_primary_keys() uses MySQL-specific CONSTRAINT_NAME='PRIMARY' filter
- get_foreign_keys() uses REFERENCED_TABLE_NAME IS NOT NULL to distinguish FKs from PKs
- All methods accept schema parameter (database name in MySQL)
- Comprehensive docstrings with MySQL-specific notes
- mypy --strict passes with no errors

### Task 2: Write MySQL extractor tests
**Commit:** 052d3fe
**Files:** tests/schema/test_mysql.py

Created comprehensive test suite with 12 tests using mocked database cursors:
- test_get_tables: Verifies table extraction and BASE TABLE filter
- test_get_tables_filters_schema: Verifies schema parameter usage
- test_get_columns: Verifies ColumnMetadata object creation
- test_get_columns_nullable_conversion: Verifies 'YES'/'NO' → boolean conversion
- test_get_columns_query_parameters: Verifies uppercase column names in SQL
- test_get_primary_keys: Verifies PK extraction with CONSTRAINT_NAME='PRIMARY'
- test_get_primary_keys_composite: Verifies composite PK order preservation
- test_get_primary_keys_none: Verifies empty list when no PK exists
- test_get_foreign_keys: Verifies ForeignKeyMetadata object creation
- test_get_foreign_keys_filters_null_references: Verifies REFERENCED_TABLE_NAME IS NOT NULL filter
- test_get_foreign_keys_composite: Verifies composite FK handling with ordinal positions
- test_get_foreign_keys_self_referencing: Verifies hierarchical table FKs

All tests use unittest.mock.MagicMock for cursors - no real database needed.
Coverage: 100% on mysql.py (23/23 statements, 0 missed).

## Verification Results

All verification steps passed successfully:

```bash
✓ uv run pytest tests/schema/test_mysql.py -v              # 12 tests passed
✓ uv run pytest --cov=src/data_cataloger/schema/mysql     # 100% coverage
✓ uv run mypy --strict src/data_cataloger/schema/mysql.py # No issues found
✓ uv run ruff check src/data_cataloger/schema/            # All checks passed
```

Coverage: 100% on mysql.py (23 statements, 0 missed)

## Success Criteria Verification

- [x] MySQLExtractor class exists with 4 methods (get_tables, get_columns, get_primary_keys, get_foreign_keys)
- [x] All methods accept DatabaseConnector and schema parameters
- [x] SQL queries use INFORMATION_SCHEMA with uppercase column names
- [x] get_foreign_keys filters REFERENCED_TABLE_NAME IS NOT NULL
- [x] is_nullable conversion works identically to PostgreSQL ('YES' → True, 'NO' → False)
- [x] Tests pass with 12 tests covering all methods and MySQL-specific patterns
- [x] Code coverage 100% on mysql.py (23/23 statements)
- [x] mypy --strict passes on mysql.py

## Deviations from Plan

None - plan executed exactly as written.

## Key Implementation Details

**MySQL vs PostgreSQL differences:**
1. Column names: MySQL uses UPPERCASE (TABLE_NAME) vs PostgreSQL lowercase (table_name)
2. Primary keys: MySQL uses `CONSTRAINT_NAME = 'PRIMARY'` vs PostgreSQL `constraint_type = 'PRIMARY KEY'`
3. Foreign keys: MySQL has all FK data in KEY_COLUMN_USAGE (no joins needed) vs PostgreSQL requires 3-table join
4. Schema: MySQL uses database name vs PostgreSQL uses schema namespace ('public')

**Critical FK filter:**
The `REFERENCED_TABLE_NAME IS NOT NULL` filter in get_foreign_keys() is essential. MySQL's KEY_COLUMN_USAGE view contains primary keys, unique constraints, AND foreign keys. Without the NULL check, primary keys would incorrectly appear as foreign keys. This was explicitly documented in the research and plan.

## Next Steps

Next plan (03-04) will implement the dependency graph builder that uses topological sort to order tables by their FK dependencies. It will work with both PostgreSQL and MySQL extractors to create a processing order for LLM cataloging.

## Self-Check: PASSED

**Files created:**
- src/data_cataloger/schema/mysql.py exists ✓
- tests/schema/test_mysql.py exists ✓

**Commits exist:**
- ce0a6d5 (Task 1: MySQL schema extractor) ✓
- 052d3fe (Task 2: MySQL extractor tests) ✓

All deliverables verified and present.
