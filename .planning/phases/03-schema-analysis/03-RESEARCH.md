# Phase 3: Schema Analysis - Research

**Researched:** 2026-02-22
**Domain:** Database schema introspection and dependency graph analysis
**Confidence:** HIGH

## Summary

Schema analysis requires extracting metadata from PostgreSQL and MySQL databases using standard `information_schema` views, building a dependency graph from foreign key relationships, and topologically sorting tables to determine processing order. The Python standard library's `graphlib.TopologicalSorter` (available since Python 3.9) provides native cycle detection and dependency resolution, eliminating the need for external graph libraries.

PostgreSQL and MySQL both implement SQL-standard `information_schema` views for portable schema introspection, though performance considerations favor using native system catalogs (pg_catalog for PostgreSQL) for production use. The key challenge is handling edge cases: self-referencing foreign keys (hierarchical tables), composite multi-column foreign keys, and circular dependencies that require cycle detection.

**Primary recommendation:** Use `information_schema` for initial implementation (portable, standard SQL), with dataclasses to model schema metadata, and Python's built-in `graphlib.TopologicalSorter` for dependency ordering with automatic cycle detection.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCHM-01 | System extracts all tables from connected database | `information_schema.tables` query with `table_type='BASE TABLE'` filter |
| SCHM-02 | System extracts columns with data types for each table | `information_schema.columns` query returns column name, data_type, ordinal_position |
| SCHM-03 | System extracts primary key constraints | `information_schema.table_constraints` + `key_column_usage` joined on constraint_type='PRIMARY KEY' |
| SCHM-04 | System extracts foreign key relationships between tables | `information_schema.referential_constraints` + `key_column_usage` (PostgreSQL), `key_column_usage` with REFERENCED_TABLE_NAME filter (MySQL) |
| SCHM-05 | System calculates dependency ranking based on FK relationships | `graphlib.TopologicalSorter` with tables as nodes, FK relationships as edges |
| SCHM-06 | System orders tables from most independent to most dependent | `TopologicalSorter.static_order()` returns tables in dependency order |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| graphlib | stdlib (3.9+) | Topological sort and cycle detection | Built into Python 3.9+, no external deps, Kahn's algorithm |
| psycopg | 3.3.3+ | Execute introspection queries (PostgreSQL) | Already installed in Phase 2, cursor.fetchall() for query results |
| mysql-connector-python | 9.6.0+ | Execute introspection queries (MySQL) | Already installed in Phase 2, cursor.fetchall() for query results |
| dataclasses | stdlib | Model schema metadata (Table, Column, FK) | Standard library, type-safe, immutable with frozen=True |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing.Literal | stdlib | Constrain db_type field values | Type-safe database type discrimination |
| typing.Optional | stdlib | Model nullable foreign keys | Self-referencing FKs may have null parent_id |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| graphlib | NetworkX | NetworkX adds 5MB+ dependency for features we don't need; graphlib sufficient for topological sort |
| information_schema | pg_catalog (PostgreSQL-specific) | pg_catalog faster but not portable; information_schema trades performance for portability |
| dataclasses | Pydantic models | Pydantic adds validation we don't need for read-only metadata; dataclasses simpler |
| Manual graph | SQLAlchemy MetaData.sorted_tables | SQLAlchemy reflection is heavy; we only need FK dependency graph, not full ORM |

**Installation:**
```bash
# No new dependencies - graphlib and dataclasses are stdlib
# Existing connectors (psycopg, mysql-connector-python) already installed
```

## Architecture Patterns

### Recommended Project Structure
```
src/data_cataloger/
├── schema/
│   ├── __init__.py
│   ├── models.py          # TableMetadata, ColumnMetadata, ForeignKeyMetadata dataclasses
│   ├── introspector.py    # SchemaIntrospector with db-specific extractors
│   ├── dependency.py      # DependencyGraph class wrapping graphlib.TopologicalSorter
│   └── postgres.py        # PostgreSQL-specific information_schema queries
│   └── mysql.py           # MySQL-specific information_schema queries
tests/schema/
├── __init__.py
├── test_models.py         # Dataclass instantiation and immutability tests
├── test_introspector.py   # Schema extraction tests (mocked cursors)
├── test_dependency.py     # Graph building and topological sort tests
└── fixtures/
    └── sample_schemas.py  # Mock query results for testing
```

### Pattern 1: Dataclass Schema Models
**What:** Immutable dataclasses representing database schema metadata
**When to use:** Modeling read-only metadata extracted from database

**Example:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ColumnMetadata:
    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    column_default: Optional[str] = None

@dataclass(frozen=True)
class ForeignKeyMetadata:
    constraint_name: str
    column_name: str
    referenced_table: str
    referenced_column: str
    ordinal_position: int  # For composite FKs

@dataclass(frozen=True)
class TableMetadata:
    schema_name: str
    table_name: str
    columns: tuple[ColumnMetadata, ...]
    primary_keys: tuple[str, ...]  # Column names
    foreign_keys: tuple[ForeignKeyMetadata, ...]
```

### Pattern 2: Database-Agnostic Introspector Interface
**What:** Protocol-based interface with database-specific implementations
**When to use:** Support multiple database types with shared interface

**Example:**
```python
from typing import Protocol
from data_cataloger.connection.base import DatabaseConnector

class SchemaExtractor(Protocol):
    def get_tables(self, connector: DatabaseConnector) -> list[str]:
        """Return list of table names in database."""
        ...

    def get_columns(self, connector: DatabaseConnector, table: str) -> list[ColumnMetadata]:
        """Return column metadata for given table."""
        ...

    def get_foreign_keys(self, connector: DatabaseConnector, table: str) -> list[ForeignKeyMetadata]:
        """Return foreign key constraints for given table."""
        ...

class PostgreSQLExtractor:
    """PostgreSQL-specific implementation using information_schema."""

    def get_tables(self, connector: DatabaseConnector) -> list[str]:
        with connector.connection.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            return [row[0] for row in cur.fetchall()]
```

### Pattern 3: Dependency Graph with Cycle Detection
**What:** Wrapper around graphlib.TopologicalSorter with domain-specific API
**When to use:** Building and sorting table dependency graphs

**Example:**
```python
from graphlib import TopologicalSorter, CycleError
from typing import Optional

class DependencyGraph:
    def __init__(self):
        self._sorter = TopologicalSorter()
        self._tables_added = set()

    def add_table(self, table: str, dependencies: list[str]) -> None:
        """Add table with its foreign key dependencies."""
        self._sorter.add(table, *dependencies)
        self._tables_added.add(table)

    def get_processing_order(self) -> tuple[list[str], Optional[list[str]]]:
        """
        Return (ordered_tables, cycle_nodes).
        If cycle detected, ordered_tables is empty and cycle_nodes contains cycle.
        """
        try:
            ordered = list(self._sorter.static_order())
            return (ordered, None)
        except CycleError as e:
            # e.args[1] contains list of nodes forming the cycle
            cycle = e.args[1] if len(e.args) > 1 else []
            return ([], cycle)
```

### Pattern 4: Composite Foreign Key Handling
**What:** Group multi-column FKs by constraint_name, preserve ordinal_position
**When to use:** Processing foreign key query results that may include composite keys

**Example:**
```python
from collections import defaultdict

def group_composite_foreign_keys(fk_rows: list[tuple]) -> list[ForeignKeyMetadata]:
    """
    Group foreign key rows by constraint_name to handle composite FKs.
    Each FK row: (constraint_name, column_name, referenced_table, referenced_column, ordinal_position)
    """
    grouped = defaultdict(list)
    for constraint_name, col_name, ref_table, ref_col, ordinal in fk_rows:
        grouped[constraint_name].append((col_name, ref_table, ref_col, ordinal))

    # For each constraint, create ForeignKeyMetadata objects
    fk_list = []
    for constraint_name, columns in grouped.items():
        # Sort by ordinal_position to maintain column order
        columns.sort(key=lambda x: x[3])  # x[3] is ordinal_position
        for col_name, ref_table, ref_col, ordinal in columns:
            fk_list.append(ForeignKeyMetadata(
                constraint_name=constraint_name,
                column_name=col_name,
                referenced_table=ref_table,
                referenced_column=ref_col,
                ordinal_position=ordinal
            ))
    return fk_list
```

### Anti-Patterns to Avoid
- **Querying schema metadata repeatedly:** Cache TableMetadata after first extraction; schema doesn't change during cataloging session
- **Using NetworkX for simple topological sort:** graphlib is stdlib and sufficient for dependency ordering
- **Ignoring self-referencing FKs:** Hierarchical tables (parent_id -> id) create valid dependencies; don't filter them out
- **Not grouping composite FKs:** Query results return one row per column; group by constraint_name before processing
- **Using sys.objects (SQL Server) patterns:** This project only supports PostgreSQL and MySQL; don't research SQL Server introspection

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Topological sorting | Custom DFS/BFS graph traversal | `graphlib.TopologicalSorter` | Handles cycles, parallel processing support, Kahn's algorithm tested |
| Cycle detection | Manual visited-set tracking | `TopologicalSorter.prepare()` raises `CycleError` | CycleError.args[1] contains actual cycle nodes for reporting |
| Schema reflection | Custom SQL parsers | `information_schema` standard views | SQL-standard portable across PostgreSQL/MySQL, no parsing needed |
| Foreign key discovery | Parsing SHOW CREATE TABLE | `information_schema.referential_constraints` + `key_column_usage` | Handles composite FKs, self-referencing, portable |
| Data type mapping | String matching on type names | Store raw `data_type` string from information_schema | LLM can interpret type names; premature normalization adds complexity |

**Key insight:** Database introspection is a solved problem with SQL-standard views. Custom solutions introduce bugs (missed edge cases: composite FKs, self-references, schema-qualified names). graphlib provides production-tested topological sort since Python 3.9.

## Common Pitfalls

### Pitfall 1: information_schema Performance on Large Databases
**What goes wrong:** information_schema views can be slow on databases with 1000+ tables because they don't use object IDs for joins, causing inefficient execution plans.

**Why it happens:** information_schema is SQL-standard (portable) but doesn't expose internal object IDs. Joins use string matching on schema/table names instead of integer ID comparisons.

**How to avoid:**
- For PostgreSQL production use, migrate to `pg_catalog` queries if performance issues observed (measure first)
- For MySQL, information_schema is generally acceptable; InnoDB tables have indexed metadata
- Start with information_schema; optimize only if profiling shows schema extraction >5 seconds

**Warning signs:** Schema extraction takes >10 seconds on databases with <500 tables, query execution plans show full table scans on information_schema views

### Pitfall 2: Missing Self-Referencing Foreign Keys in Dependency Graph
**What goes wrong:** Hierarchical tables (e.g., `categories.parent_id -> categories.id`) create self-dependencies. If not added to graph, topological sort may return incorrect order or miss circular hierarchies.

**Why it happens:** Naive FK extraction filters `table_name != referenced_table`, assuming FKs only reference other tables.

**How to avoid:**
- Include self-referencing FKs in dependency graph
- For self-references, add table to graph with itself as dependency: `sorter.add("categories", "categories")`
- graphlib correctly handles self-loops by placing table in earliest valid position

**Warning signs:** Employee/organization/category tables processed before their dependencies, cataloging fails to reference parent records

### Pitfall 3: Composite Foreign Keys Treated as Separate Constraints
**What goes wrong:** Multi-column FK (e.g., `FOREIGN KEY (dept_id, emp_id) REFERENCES ...`) returns 2+ rows in information_schema. If each row processed independently, dependency graph has duplicate edges and incorrect metadata.

**Why it happens:** information_schema.key_column_usage returns one row per column in constraint, not one row per constraint.

**How to avoid:**
- Group FK rows by `constraint_name` before processing
- Use `ordinal_position` or `position_in_unique_constraint` to maintain column order
- Create single ForeignKeyMetadata per constraint, storing all columns

**Warning signs:** Same constraint_name appears multiple times in foreign_keys list, dependency graph has duplicate edges for same table pair

### Pitfall 4: Circular Dependencies Crash Topological Sort
**What goes wrong:** If tables A and B both reference each other (rare but possible with deferred constraints), topological sort raises CycleError and crashes application.

**Why it happens:** DAG assumption violated; cycle exists in FK relationships. Database allows this via deferred constraint checking.

**How to avoid:**
- Catch `graphlib.CycleError` exception
- Extract cycle nodes from `e.args[1]` (list of table names forming cycle)
- Log cycle as warning, provide fallback ordering (alphabetical, or user-specified)
- Document that circular dependencies require manual processing order

**Warning signs:** CycleError raised during dependency graph preparation, error message contains table names in circular reference

### Pitfall 5: Ignoring Schema Qualification
**What goes wrong:** PostgreSQL supports multiple schemas (public, staging, reporting). Querying information_schema without schema filter may return tables from all schemas, including system schemas (pg_catalog, information_schema itself).

**Why it happens:** Default information_schema queries don't filter by `table_schema`, returning all visible tables.

**How to avoid:**
- Always filter by `table_schema = 'public'` or user-specified schema
- For PostgreSQL, exclude system schemas: `table_schema NOT IN ('pg_catalog', 'information_schema')`
- Store schema_name in TableMetadata for qualified references

**Warning signs:** Introspection returns 100+ tables on small database, table names include pg_* or information_schema tables

### Pitfall 6: Nullable Columns Not Marked in ColumnMetadata
**What goes wrong:** `is_nullable` column in information_schema returns 'YES'/'NO' strings, not boolean. Direct assignment to bool field converts non-empty strings to True, making all columns appear nullable.

**Why it happens:** SQL-standard information_schema uses string values for booleans ('YES', 'NO').

**How to avoid:**
- Convert to bool: `is_nullable = (row['is_nullable'] == 'YES')`
- Consistent for both PostgreSQL and MySQL information_schema

**Warning signs:** All columns show is_nullable=True, including primary key columns

## Code Examples

Verified patterns from official sources:

### PostgreSQL: Get All Tables
```python
# Source: PostgreSQL information_schema standard
# https://www.postgresql.org/docs/current/infoschema-tables.html

def get_tables_postgresql(connector: DatabaseConnector, schema: str = 'public') -> list[str]:
    """Extract all base tables from PostgreSQL database."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    with connector.connection.cursor() as cur:
        cur.execute(query, (schema,))
        return [row[0] for row in cur.fetchall()]
```

### PostgreSQL: Get Columns with Data Types
```python
# Source: PostgreSQL information_schema.columns view
# https://www.postgresql.org/docs/current/infoschema-columns.html

def get_columns_postgresql(connector: DatabaseConnector, table: str, schema: str = 'public') -> list[ColumnMetadata]:
    """Extract column metadata for given table."""
    query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            ordinal_position,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name = %s
        ORDER BY ordinal_position
    """
    with connector.connection.cursor() as cur:
        cur.execute(query, (schema, table))
        return [
            ColumnMetadata(
                name=row[0],
                data_type=row[1],
                is_nullable=(row[2] == 'YES'),
                ordinal_position=row[3],
                column_default=row[4]
            )
            for row in cur.fetchall()
        ]
```

### PostgreSQL: Get Primary Keys
```python
# Source: PostgreSQL information_schema key_column_usage + table_constraints
# https://www.postgresql.org/docs/current/infoschema-table-constraints.html

def get_primary_keys_postgresql(connector: DatabaseConnector, table: str, schema: str = 'public') -> list[str]:
    """Extract primary key column names for given table."""
    query = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.constraint_schema = kcu.constraint_schema
        WHERE tc.table_schema = %s
          AND tc.table_name = %s
          AND tc.constraint_type = 'PRIMARY KEY'
        ORDER BY kcu.ordinal_position
    """
    with connector.connection.cursor() as cur:
        cur.execute(query, (schema, table))
        return [row[0] for row in cur.fetchall()]
```

### PostgreSQL: Get Foreign Keys
```python
# Source: PostgreSQL information_schema referential_constraints + key_column_usage
# https://www.postgresql.org/docs/current/infoschema-referential-constraints.html

def get_foreign_keys_postgresql(connector: DatabaseConnector, table: str, schema: str = 'public') -> list[ForeignKeyMetadata]:
    """Extract foreign key constraints for given table."""
    query = """
        SELECT
            kcu.constraint_name,
            kcu.column_name,
            ccu.table_name AS referenced_table,
            ccu.column_name AS referenced_column,
            kcu.ordinal_position
        FROM information_schema.key_column_usage kcu
        JOIN information_schema.referential_constraints rc
          ON kcu.constraint_name = rc.constraint_name
         AND kcu.constraint_schema = rc.constraint_schema
        JOIN information_schema.key_column_usage ccu
          ON rc.unique_constraint_name = ccu.constraint_name
         AND rc.unique_constraint_schema = ccu.constraint_schema
         AND kcu.ordinal_position = ccu.ordinal_position
        WHERE kcu.table_schema = %s
          AND kcu.table_name = %s
        ORDER BY kcu.constraint_name, kcu.ordinal_position
    """
    with connector.connection.cursor() as cur:
        cur.execute(query, (schema, table))
        return [
            ForeignKeyMetadata(
                constraint_name=row[0],
                column_name=row[1],
                referenced_table=row[2],
                referenced_column=row[3],
                ordinal_position=row[4]
            )
            for row in cur.fetchall()
        ]
```

### MySQL: Get Foreign Keys
```python
# Source: MySQL information_schema.key_column_usage
# https://dev.mysql.com/doc/mysql-infoschema-excerpt/5.7/en/information-schema-key-column-usage-table.html

def get_foreign_keys_mysql(connector: DatabaseConnector, table: str, schema: str) -> list[ForeignKeyMetadata]:
    """Extract foreign key constraints for given table."""
    query = """
        SELECT
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
          AND TABLE_NAME = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
    """
    with connector.connection.cursor() as cur:
        cur.execute(query, (schema, table))
        return [
            ForeignKeyMetadata(
                constraint_name=row[0],
                column_name=row[1],
                referenced_table=row[2],
                referenced_column=row[3],
                ordinal_position=row[4]
            )
            for row in cur.fetchall()
        ]
```

### Dependency Graph Building
```python
# Source: Python graphlib documentation
# https://docs.python.org/3/library/graphlib.html

from graphlib import TopologicalSorter, CycleError
from typing import Optional

def build_dependency_graph(tables_metadata: list[TableMetadata]) -> tuple[list[str], Optional[list[str]]]:
    """
    Build dependency graph and return topologically sorted table order.
    Returns: (ordered_tables, cycle_nodes)
    If cycle detected: ordered_tables=[], cycle_nodes=[table names in cycle]
    """
    sorter = TopologicalSorter()

    # Add all tables with their dependencies
    for table in tables_metadata:
        # Extract unique referenced tables from foreign keys
        dependencies = {fk.referenced_table for fk in table.foreign_keys}
        sorter.add(table.table_name, *dependencies)

    # Attempt topological sort
    try:
        ordered = list(sorter.static_order())
        return (ordered, None)
    except CycleError as e:
        # Extract cycle nodes from exception
        cycle = e.args[1] if len(e.args) > 1 else []
        return ([], cycle)
```

### Handling Self-Referencing Tables
```python
# Source: Database hierarchy patterns
# https://medium.com/@priyanshupardhi/design-tree-based-hierarchy-structure-in-database-using-self-referencing-foreign-key-9a0b84a4a801

def is_self_referencing(table_metadata: TableMetadata) -> bool:
    """Check if table has self-referencing foreign keys (hierarchical structure)."""
    return any(
        fk.referenced_table == table_metadata.table_name
        for fk in table_metadata.foreign_keys
    )

# Self-referencing tables are valid and should be included in dependency graph
# graphlib handles self-loops correctly:
sorter.add("categories", "categories")  # Valid: table depends on itself
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NetworkX for topological sort | Python graphlib (stdlib) | Python 3.9 (Oct 2020) | No external dependencies, faster for simple graphs |
| SQLAlchemy Inspector for schema introspection | Direct information_schema queries | N/A - both valid | SQLAlchemy adds 5MB dependency; direct queries lighter for read-only use |
| Custom cycle detection | graphlib.CycleError exception | Python 3.9 | Built-in cycle detection with node details |
| Pydantic models for metadata | @dataclass(frozen=True) | N/A - both valid | Dataclasses simpler for read-only data, no validation overhead |
| pg_catalog queries (PostgreSQL) | information_schema (portable) | SQL:1992 standard | Portability vs performance tradeoff; information_schema slower but works on both PostgreSQL/MySQL |

**Deprecated/outdated:**
- **topsort library (PyPI):** External topological sort library obsoleted by graphlib in Python 3.9
- **psycopg2:** psycopg (psycopg3) is the current adapter; psycopg2 in maintenance mode
- **is_connected() method (MySQL):** Deprecated in mysql-connector-python 9.3.0+; use `.connected` property instead (already used in Phase 2)

## Open Questions

1. **Should we support views in addition to base tables?**
   - What we know: information_schema.tables distinguishes `table_type IN ('BASE TABLE', 'VIEW')`
   - What's unclear: Are views in scope for cataloging? LLM analysis on views may be less useful
   - Recommendation: Start with BASE TABLE only; add views in v2 if user requests

2. **How to handle materialized views (PostgreSQL-specific)?**
   - What we know: PostgreSQL has materialized views (table_type = 'MATERIALIZED VIEW'), MySQL doesn't
   - What's unclear: Do they need separate dependency tracking? They can have indexes but not FKs
   - Recommendation: Treat as BASE TABLE for now; likely no FK dependencies to track

3. **Should we expose schema name as user configuration?**
   - What we know: PostgreSQL commonly uses multiple schemas; MySQL typically uses single schema per database
   - What's unclear: Does user need to specify schema, or default to 'public' (PostgreSQL) / database name (MySQL)?
   - Recommendation: Default to 'public' for PostgreSQL, connection's database name for MySQL; expose as optional config in v2

4. **How to order tables when circular dependencies exist?**
   - What we know: graphlib.CycleError raised, contains cycle nodes in e.args[1]
   - What's unclear: What fallback ordering should we use? Alphabetical? Let user specify?
   - Recommendation: Log cycle as warning, fall back to alphabetical order, document that circular FKs may affect cataloging quality

## Sources

### Primary (HIGH confidence)
- [Python graphlib documentation](https://docs.python.org/3/library/graphlib.html) - TopologicalSorter, CycleError, static_order() method
- [PostgreSQL information_schema.key_column_usage](https://www.postgresql.org/docs/current/infoschema-key-column-usage.html) - Foreign key column metadata
- [PostgreSQL information_schema.referential_constraints](https://www.postgresql.org/docs/current/infoschema-referential-constraints.html) - FK constraint definitions
- [MySQL information_schema.key_column_usage](https://dev.mysql.com/doc/mysql-infoschema-excerpt/5.7/en/information-schema-key-column-usage-table.html) - MySQL FK metadata structure
- [Psycopg 3 documentation](https://www.psycopg.org/psycopg3/docs/) - Cursor usage, query execution

### Secondary (MEDIUM confidence)
- [PostgreSQL introspection blog](https://jarnaldich.me/blog/2021/08/30/postgres-introspection.html) - pg_catalog vs information_schema patterns
- [SQLAlchemy reflection documentation](https://docs.sqlalchemy.org/en/20/core/reflection.html) - Inspector methods (get_table_names, get_columns, get_foreign_keys)
- [List PostgreSQL primary keys](https://dataedo.com/kb/query/postgresql/list-all-primary-keys-and-their-columns) - SQL query patterns for PK extraction
- [List MySQL foreign keys](https://dataedo.com/kb/query/mysql/list-foreign-keys) - SQL query patterns for FK extraction
- [Topological sorting with graphlib (GeeksforGeeks)](https://www.geeksforgeeks.org/python/topological-sorting-using-graphlib-python-module/) - Usage examples
- [Database dependency resolution (Medium)](https://medium.com/@muhammadbutt1099/how-to-resolve-dependencies-of-relational-databases-tables-44c77895117a) - Kahn's algorithm explanation

### Tertiary (LOW confidence - general knowledge)
- [schemasorter PyPI](https://pypi.org/project/schemasorter/) - Existing tool for SQL DDL topological sorting (validates our approach)
- [Self-referencing foreign keys (Medium)](https://medium.com/@priyanshupardhi/design-tree-based-hierarchy-structure-in-database-using-self-referencing-foreign-key-9a0b84a4a801) - Hierarchical table patterns
- [The case against INFORMATION_SCHEMA views](https://sqlblog.org/2011/11/03/the-case-against-information_schema-views) - Performance considerations (SQL Server focus but principles apply)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - graphlib is stdlib since Python 3.9, information_schema is SQL standard, both verified in official docs
- Architecture: HIGH - Dataclass patterns standard in Python 3.7+, Protocol-based design used in Phase 2
- Pitfalls: MEDIUM-HIGH - Common issues documented in multiple sources, edge cases verified in official docs
- SQL queries: HIGH - All queries verified against PostgreSQL and MySQL official documentation

**Research date:** 2026-02-22
**Valid until:** 2026-04-22 (60 days - stable domain: SQL standards don't change rapidly, graphlib API stable since 3.9)
