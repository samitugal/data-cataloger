# Phase 5: Graph Storage - Research

**Researched:** 2026-02-23
**Domain:** Neo4j graph database integration for catalog persistence
**Confidence:** HIGH

## Summary

Neo4j graph storage integration for catalog persistence requires the official `neo4j` Python driver (version 6.1.0, released January 2026), Docker-based Neo4j deployment via docker-compose, and a repository pattern for query abstraction. The phase transforms relational catalog data (tables, foreign keys, descriptions, sensitivity) into a property graph where tables become nodes, foreign keys become labeled edges, and catalog properties are stored on nodes.

Key technical decisions are locked by CONTEXT.md: flat properties on table nodes, labeled edges with FK metadata (type REFERENCES_VIA), database parent nodes with HAS_TABLE edges for grouping, and upsert strategy using MERGE to prevent duplicates on re-catalog. The pipeline writes to Neo4j after each table (real-time progress, partial results survive failures), continues on write failure (don't halt LLM pipeline), and uses dependency injection for testability.

The standard approach uses `driver.execute_query()` for simple operations, managed transactions (`execute_read`/`execute_write`) for complex logic, MERGE for upsert patterns, and constraints/indexes for performance. Common pitfalls include breaking MERGE into node-first then relationship-second to avoid duplicates, always specifying database name to avoid extra round-trips, and never using session.run() in production (routes all queries to cluster leader).

**Primary recommendation:** Use `neo4j==6.1.0` with direct Cypher queries, Docker compose Neo4j 5.26 LTS for stability, repository pattern returning existing domain objects (CatalogEntry/TableInfo), testcontainers for integration tests, and strict MERGE patterns (match/create nodes first, then relationships).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Graph model design:**
- Flat properties on table nodes: description, sensitivity classification, example queries stored directly as node properties
- Labeled edges with FK metadata: edge type REFERENCES_VIA with properties for FK column name, referenced column, and constraint name
- Database parent node: a Database node (name, type) with HAS_TABLE edges to each table node — natural grouping, supports future multi-DB
- Upsert strategy on re-catalog: match existing nodes by table name + database, update properties. No duplicate nodes.

**Neo4j connectivity:**
- Docker container via docker-compose.yml for Neo4j setup — bolt:// protocol connection
- Extend existing Pydantic config model with Neo4j fields (uri, username, password) — environment variables with defaults for local Docker
- Connection health check on startup: verify Neo4j is reachable before cataloging, fail fast with clear error message
- Official `neo4j` Python driver — direct Cypher queries, no OGM abstraction

**Pipeline integration:**
- Write to Neo4j after each table is cataloged (not batch) — real-time progress, partial results survive failures
- On write failure: log warning and continue cataloging — don't halt the LLM pipeline over a storage failure. User can re-run for failed tables.
- Integrated callback pattern: CatalogingAgent accepts a storage writer via dependency injection. After each table is cataloged, it calls the Neo4j writer. Testable, clean.
- Stub nodes for uncataloged referenced tables: create edges to any referenced table even if not yet cataloged. Stub node (name only) gets enriched when that table is cataloged later via upsert.

**Query patterns:**
- Repository pattern: GraphRepository class with clean methods for Phase 6 UI consumption
- Core + search queries: get_table, list_tables, get_relationships (direct FKs), get_full_graph (all nodes+edges), search_by_sensitivity, search_by_keyword (across descriptions)
- Domain object return types: return CatalogEntry/TableInfo types consistent with existing codebase, not graph-specific DTOs
- Direct relationships only: get_relationships returns immediate FK connections. No multi-hop traversal in v1.

### Claude's Discretion

- Docker compose configuration details (ports, volumes, environment)
- Cypher query optimization and indexing strategy
- Neo4j transaction management approach
- Test infrastructure for Neo4j integration tests (testcontainers vs mock)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GRPH-01 | System stores catalog data in Neo4j graph database | Neo4j Python driver 6.1.0, docker-compose deployment, GraphDatabase.driver() connection pattern |
| GRPH-02 | Each table is represented as a node with properties (name, description, sensitivity) | Node creation with MERGE, properties stored as node attributes, Table label |
| GRPH-03 | FK relationships are represented as edges between table nodes | Relationship creation with MERGE, labeled edges (REFERENCES_VIA), FK metadata as edge properties |
| GRPH-04 | Example queries are stored as properties on table nodes | Array property support in Neo4j, store as list[str] on node |
| GRPH-05 | System can query Neo4j to retrieve catalog information | Repository pattern with execute_query(), MATCH queries for retrieval, return domain objects |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| neo4j | 6.1.0 | Official Neo4j Python driver | Released Jan 2026, official driver, supports Neo4j 4.4/5.x/2026.x, includes Rust extension for 3-10x speedup, well-documented |
| neo4j (Docker) | 5.26 LTS | Neo4j database server | Long-term support version, stable for production, Community Edition sufficient for single-node deployment |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| testcontainers[neo4j] | 4.10+ | Neo4j container for integration tests | Testing Neo4j integration without mocking, ephemeral clean database per test |
| pydantic-settings | 2.13.1+ | Config management with Neo4j credentials | Already in project, extend existing DatabaseConfig for Neo4j URI/auth |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Neo4j 5.26 LTS | Neo4j 2026.01 | LTS: stability, long support. 2026: latest features, faster updates. Use LTS for production v1. |
| Direct Cypher | neomodel OGM | Direct Cypher: full control, explicit, matches user decision. OGM: abstraction overhead, learning curve, hides graph operations. |
| testcontainers | Mock driver | testcontainers: real integration, catches Cypher bugs. Mock: fast, unit-level. Use testcontainers for GraphRepository tests, mock for CatalogingAgent tests. |

**Installation:**

```bash
# Add to pyproject.toml dependencies
neo4j>=6.1.0

# Add to dev dependency-groups
testcontainers[neo4j]>=4.10.0
```

## Architecture Patterns

### Recommended Project Structure

```
src/data_cataloger/
├── storage/
│   ├── __init__.py          # Export GraphRepository, Neo4jWriter
│   ├── repository.py        # GraphRepository (read queries)
│   ├── writer.py            # Neo4jWriter (write operations, catalog persistence)
│   ├── config.py            # Extend DatabaseConfig with Neo4j fields
│   └── models.py            # Optional: TableNode, DatabaseNode DTOs if needed
tests/storage/
├── test_repository.py       # Integration tests with testcontainers
├── test_writer.py           # Integration tests for write operations
└── conftest.py              # Neo4j testcontainer fixture
```

### Pattern 1: Driver Lifecycle Management

**What:** Initialize Neo4j driver once, verify connectivity on startup, use context manager for automatic cleanup.

**When to use:** Application initialization, before cataloging operations.

**Example:**

```python
# Source: https://neo4j.com/docs/python-manual/current/
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

# Initialize driver (singleton pattern)
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    # Verify connectivity immediately after creation
    driver.verify_connectivity()

    # Use driver for operations
    records, summary, keys = driver.execute_query(
        "MATCH (n) RETURN n LIMIT 1",
        database_="neo4j"
    )
```

### Pattern 2: MERGE Upsert for Nodes

**What:** Create or update nodes without duplicates using MERGE with ON CREATE/ON MATCH.

**When to use:** Writing catalog entries that may already exist (re-catalog scenario).

**Example:**

```python
# Source: https://neo4j.com/docs/cypher-manual/current/clauses/merge/
# Pattern: MERGE node first, then set properties conditionally

query = """
MERGE (t:Table {name: $table_name, database: $database})
ON CREATE SET
    t.description = $description,
    t.sensitivity = $sensitivity,
    t.example_queries = $example_queries,
    t.created_at = timestamp()
ON MATCH SET
    t.description = $description,
    t.sensitivity = $sensitivity,
    t.example_queries = $example_queries,
    t.updated_at = timestamp()
RETURN t
"""

driver.execute_query(
    query,
    table_name="users",
    database="mydb",
    description="User account information",
    sensitivity="PII",
    example_queries=["SELECT * FROM users WHERE id = 1"],
    database_="neo4j"
)
```

### Pattern 3: MERGE Relationships (Node-First Pattern)

**What:** MERGE nodes separately before MERGE relationships to avoid duplicate nodes.

**When to use:** Creating foreign key edges between table nodes.

**Example:**

```python
# Source: https://neo4j.com/developer/kb/understanding-how-merge-works/
# Anti-pattern: MERGE full pattern (creates duplicate nodes if partial match)
# MERGE (a:Table {name: "orders"})-[:REFERENCES_VIA]->(b:Table {name: "users"})

# Best practice: MERGE nodes first, then relationship
query = """
MERGE (source:Table {name: $source_table, database: $database})
MERGE (target:Table {name: $target_table, database: $database})
MERGE (source)-[r:REFERENCES_VIA {
    fk_column: $fk_column,
    referenced_column: $referenced_column,
    constraint_name: $constraint_name
}]->(target)
RETURN r
"""

driver.execute_query(
    query,
    source_table="orders",
    target_table="users",
    database="mydb",
    fk_column="user_id",
    referenced_column="id",
    constraint_name="fk_orders_user",
    database_="neo4j"
)
```

### Pattern 4: Repository Pattern with Domain Objects

**What:** Encapsulate Neo4j queries in repository class, return existing domain objects (CatalogEntry), hide Cypher from consumers.

**When to use:** Phase 6 Web Interface needs to query catalog data.

**Example:**

```python
# Source: Project pattern from cataloging/models.py
from dataclasses import dataclass
from neo4j import Driver
from data_cataloger.cataloging.models import CatalogEntry

class GraphRepository:
    """Read-only repository for querying catalog graph."""

    def __init__(self, driver: Driver, database: str = "neo4j") -> None:
        self._driver = driver
        self._database = database

    def get_table(self, table_name: str, database: str) -> CatalogEntry | None:
        """Retrieve catalog entry for a specific table."""
        query = """
        MATCH (t:Table {name: $table_name, database: $database})
        RETURN t.name AS name, t.description AS description,
               t.sensitivity AS sensitivity, t.example_queries AS example_queries
        """
        records, _, _ = self._driver.execute_query(
            query,
            table_name=table_name,
            database=database,
            database_=self._database
        )

        if not records:
            return None

        record = records[0]
        return CatalogEntry(
            table_name=record["name"],
            description=record["description"],
            sensitivity=record["sensitivity"],
            example_queries=record["example_queries"]
        )

    def list_tables(self, database: str) -> list[CatalogEntry]:
        """List all cataloged tables in a database."""
        query = """
        MATCH (t:Table {database: $database})
        RETURN t.name AS name, t.description AS description,
               t.sensitivity AS sensitivity, t.example_queries AS example_queries
        ORDER BY t.name
        """
        records, _, _ = self._driver.execute_query(
            query,
            database=database,
            database_=self._database
        )

        return [
            CatalogEntry(
                table_name=r["name"],
                description=r["description"],
                sensitivity=r["sensitivity"],
                example_queries=r["example_queries"]
            )
            for r in records
        ]

    def get_relationships(self, table_name: str, database: str) -> list[dict[str, str]]:
        """Get direct foreign key relationships for a table."""
        query = """
        MATCH (source:Table {name: $table_name, database: $database})
              -[r:REFERENCES_VIA]->(target:Table)
        RETURN target.name AS referenced_table,
               r.fk_column AS fk_column,
               r.referenced_column AS referenced_column,
               r.constraint_name AS constraint_name
        """
        records, _, _ = self._driver.execute_query(
            query,
            table_name=table_name,
            database=database,
            database_=self._database
        )

        return [dict(record) for record in records]
```

### Pattern 5: Dependency Injection for Testing

**What:** CatalogingAgent accepts optional storage writer, allowing test mocks and production Neo4jWriter.

**When to use:** Integration between cataloging engine (Phase 4) and graph storage (Phase 5).

**Example:**

```python
# Source: Project pattern from cataloging/agent.py
from typing import Protocol
from data_cataloger.cataloging.models import CatalogEntry

class CatalogWriter(Protocol):
    """Protocol for catalog storage backends."""
    def write_entry(self, entry: CatalogEntry, database: str) -> None:
        """Persist a catalog entry."""
        ...

class CatalogingAgent:
    def __init__(
        self,
        client: OpenAIClient | None = None,
        writer: CatalogWriter | None = None
    ) -> None:
        self._client = client or OpenAIClient()
        self._writer = writer

    def catalog_database(self, schema: SchemaAnalysisResult) -> dict[str, CatalogEntry]:
        """Catalog all tables in schema."""
        catalog = {}

        for table_name in schema.processing_order:
            entry = self._catalog_table(table, parent_context)
            catalog[table_name] = entry

            # Write to storage if writer provided
            if self._writer:
                try:
                    self._writer.write_entry(entry, schema.database_name)
                except Exception as e:
                    # Log warning, continue cataloging
                    print(f"Warning: Failed to write {table_name} to storage: {e}")

        return catalog

# Production usage
from data_cataloger.storage.writer import Neo4jWriter

writer = Neo4jWriter(driver, database="neo4j")
agent = CatalogingAgent(writer=writer)

# Test usage
agent = CatalogingAgent(writer=None)  # No storage writes
```

### Pattern 6: Testcontainers Fixture

**What:** Pytest fixture that spins up ephemeral Neo4j container for integration tests.

**When to use:** Testing GraphRepository and Neo4jWriter with real Neo4j.

**Example:**

```python
# Source: https://testcontainers.com/modules/neo4j/
# tests/storage/conftest.py
import pytest
from neo4j import GraphDatabase
from testcontainers.neo4j import Neo4jContainer

@pytest.fixture(scope="function")
def neo4j_container():
    """Provide Neo4j testcontainer for integration tests."""
    with Neo4jContainer("neo4j:5.26") as container:
        # Container automatically starts and provides connection details
        uri = container.get_connection_url()
        auth = ("neo4j", container.password)

        with GraphDatabase.driver(uri, auth=auth) as driver:
            driver.verify_connectivity()
            yield driver

        # Container automatically stops and cleans up

# tests/storage/test_repository.py
def test_get_table(neo4j_container):
    """Test retrieving catalog entry from Neo4j."""
    # Arrange: Create test data
    neo4j_container.execute_query(
        """
        CREATE (t:Table {
            name: 'users',
            database: 'test_db',
            description: 'User accounts',
            sensitivity: 'PII',
            example_queries: ['SELECT * FROM users']
        })
        """,
        database_="neo4j"
    )

    # Act
    repo = GraphRepository(neo4j_container, database="neo4j")
    entry = repo.get_table("users", "test_db")

    # Assert
    assert entry is not None
    assert entry.table_name == "users"
    assert entry.sensitivity == "PII"
```

### Anti-Patterns to Avoid

- **Using session.run() for queries:** Routes all queries to cluster leader, ignores read replicas, loses transaction retry capability. Use `execute_query()` or managed transactions instead.
- **MERGE full patterns (nodes + relationships):** Creates duplicate nodes if partial match exists. Always MERGE nodes first, then relationships.
- **Not specifying database name:** Forces extra round-trip to discover default database. Always use `database_` parameter.
- **Returning Result objects from functions:** Result objects are consumable streams. Materialize to list/dict before returning.
- **MERGE for known-new data:** Use CREATE for new nodes (faster). Reserve MERGE for upsert scenarios.
- **Manual driver connection management:** Use context manager (`with GraphDatabase.driver()`) to ensure cleanup.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph database client | Custom Bolt protocol implementation | `neo4j` Python driver 6.1.0 | Handles connection pooling, cluster routing, transaction retry, Cypher parameterization, security. Edge cases: transient failures, cluster topology changes, authentication, connection limits. |
| Cypher query builder | String concatenation, template library | Direct Cypher with parameterization | Cypher is declarative and readable. Query builders add abstraction overhead, hide graph operations, don't prevent Cypher errors. Parameters prevent injection, driver handles escaping. |
| OGM layer | Custom object-graph mapper | Repository pattern with domain objects | User decided "direct Cypher queries, no OGM abstraction". OGM adds complexity, magic, learning curve. Repository pattern provides abstraction without hiding Cypher. |
| Upsert logic | Check if exists, then CREATE or UPDATE | MERGE with ON CREATE/ON MATCH | MERGE is atomic, handles race conditions, optimized by Neo4j. Custom logic has TOCTOU bugs, multiple round-trips, slower. |
| Test Neo4j setup | Manual Docker commands, shared test database | testcontainers library | Testcontainers manages lifecycle, provides clean database per test, prevents test pollution, handles ports automatically. Manual setup: brittle, shared state, cleanup errors. |

**Key insight:** Neo4j provides battle-tested tools for every aspect of graph database integration. Graph databases have subtle failure modes (cluster partitions, transaction conflicts, stale reads) that custom solutions won't handle correctly. Use official driver, direct Cypher, and testcontainers for robust implementation.

## Common Pitfalls

### Pitfall 1: MERGE Pattern Duplication

**What goes wrong:** Using `MERGE (a:Table {name: "orders"})-[:REFERENCES_VIA]->(b:Table {name: "users"})` creates duplicate nodes when one node exists but relationship doesn't.

**Why it happens:** MERGE tries to match the full pattern. If it finds orders node but no relationship, it creates both the relationship AND a new users node (duplicate).

**How to avoid:** Always MERGE nodes first using unique properties, then MERGE relationships using bound variables.

**Warning signs:** Duplicate table nodes in graph, multiple nodes with same name, relationship queries return unexpected counts.

**Correct pattern:**

```cypher
MERGE (source:Table {name: $source_table, database: $database})
MERGE (target:Table {name: $target_table, database: $database})
MERGE (source)-[r:REFERENCES_VIA]->(target)
```

### Pitfall 2: Missing Database Parameter

**What goes wrong:** Omitting `database_` parameter in `execute_query()` or `database` in session creation causes extra round-trip to server to discover default database, slowing queries.

**Why it happens:** Driver doesn't cache default database discovery, queries it every time.

**How to avoid:** Always specify database explicitly: `driver.execute_query(query, database_="neo4j")`.

**Warning signs:** Slow query performance, extra network calls in logs, latency on simple queries.

### Pitfall 3: Not Verifying Connectivity on Startup

**What goes wrong:** Application starts successfully but fails later when trying to execute queries because Neo4j is unreachable, wrong credentials, or network issues.

**Why it happens:** Driver creation succeeds even if Neo4j is down (lazy connection). Errors only surface when queries execute.

**How to avoid:** Call `driver.verify_connectivity()` immediately after creating driver. Fail fast with clear error message.

**Warning signs:** Application starts but catalog operations fail silently, confusing error messages during query execution.

**Correct pattern:**

```python
try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
except Exception as e:
    raise RuntimeError(f"Cannot connect to Neo4j at {URI}: {e}")
```

### Pitfall 4: Materializing Result Sets Too Late

**What goes wrong:** Returning `Result` objects from repository methods causes "Result consumed" errors when caller tries to iterate.

**Why it happens:** Result objects are consumable streams. Once iterated, they're exhausted. Cannot iterate twice.

**How to avoid:** Convert results to list/dict before returning from repository methods.

**Warning signs:** "Result consumed" exceptions, empty result sets on second iteration.

**Correct pattern:**

```python
# BAD: Returns consumable Result
def list_tables(self) -> Result:
    records, _, _ = self._driver.execute_query("MATCH (t:Table) RETURN t")
    return records  # Result object

# GOOD: Materializes to list
def list_tables(self) -> list[CatalogEntry]:
    records, _, _ = self._driver.execute_query("MATCH (t:Table) RETURN t")
    return [self._to_catalog_entry(r) for r in records]  # List
```

### Pitfall 5: Using MERGE Instead of CREATE for Known-New Data

**What goes wrong:** Using MERGE for initial catalog creation (known-new data) wastes performance on existence checks.

**Why it happens:** MERGE checks if pattern exists before creating. For known-new data (first catalog run), check is unnecessary overhead.

**How to avoid:** Use CREATE for initial bulk load, MERGE for upsert/re-catalog scenarios. OR always use MERGE but document that initial run is slower.

**Warning signs:** Slow initial catalog creation, performance improves on subsequent runs.

**Decision:** Use MERGE consistently for upsert strategy (user decision). Accept slower initial run for simpler code.

### Pitfall 6: Ignoring Write Failures in Pipeline

**What goes wrong:** Write failure to Neo4j halts entire cataloging pipeline, losing LLM-generated catalog data for remaining tables.

**Why it happens:** Not catching exceptions around writer calls, letting errors propagate.

**How to avoid:** Wrap `writer.write_entry()` in try-except, log warning, continue processing. User decision: "On write failure: log warning and continue cataloging."

**Warning signs:** Partial catalogs never complete, LLM API costs wasted on retries, no catalog data persisted.

**Correct pattern:**

```python
for table in tables:
    entry = self._catalog_table(table)

    if self._writer:
        try:
            self._writer.write_entry(entry, database_name)
        except Exception as e:
            logger.warning(f"Failed to write {table.table_name} to Neo4j: {e}")
            # Continue processing remaining tables
```

### Pitfall 7: Neo4j Connection in Tight Loops

**What goes wrong:** Creating new driver instance for each table write causes connection overhead, exhausts connection pool.

**Why it happens:** Driver initialization in write method instead of constructor.

**How to avoid:** Initialize driver once (singleton pattern or dependency injection), reuse across all writes.

**Warning signs:** Connection pool exhaustion errors, slow write performance, "Too many connections" errors.

## Code Examples

Verified patterns from official sources.

### Database Node with HAS_TABLE Edges

```cypher
-- Source: User decision (CONTEXT.md) + Neo4j patterns
-- Create or update database node and connect table node

-- Step 1: MERGE database node
MERGE (db:Database {name: $database_name, type: $database_type})
ON CREATE SET db.created_at = timestamp()

-- Step 2: MERGE table node
MERGE (t:Table {name: $table_name, database: $database_name})
ON CREATE SET
    t.description = $description,
    t.sensitivity = $sensitivity,
    t.example_queries = $example_queries,
    t.created_at = timestamp()
ON MATCH SET
    t.description = $description,
    t.sensitivity = $sensitivity,
    t.example_queries = $example_queries,
    t.updated_at = timestamp()

-- Step 3: MERGE relationship
MERGE (db)-[:HAS_TABLE]->(t)

RETURN db, t
```

### Stub Node for Uncataloged Referenced Tables

```cypher
-- Source: User decision (CONTEXT.md)
-- Create FK edge even if referenced table not yet cataloged
-- Stub node gets enriched later via upsert

-- Source table exists (already cataloged)
MERGE (source:Table {name: $source_table, database: $database})

-- Target might not exist yet (create stub with name only)
MERGE (target:Table {name: $target_table, database: $database})
-- No ON CREATE SET description (stub node, will be enriched later)

-- Create FK edge
MERGE (source)-[r:REFERENCES_VIA {
    fk_column: $fk_column,
    referenced_column: $referenced_column,
    constraint_name: $constraint_name
}]->(target)

RETURN r
```

### Search by Sensitivity

```cypher
-- Source: User decision (query patterns) + Neo4j MATCH syntax
-- Repository method: search_by_sensitivity(sensitivity: str)

MATCH (t:Table {database: $database})
WHERE t.sensitivity = $sensitivity
RETURN t.name AS name,
       t.description AS description,
       t.sensitivity AS sensitivity,
       t.example_queries AS example_queries
ORDER BY t.name
```

### Search by Keyword in Descriptions

```cypher
-- Source: User decision (query patterns) + Neo4j text search
-- Repository method: search_by_keyword(keyword: str)

MATCH (t:Table {database: $database})
WHERE toLower(t.description) CONTAINS toLower($keyword)
RETURN t.name AS name,
       t.description AS description,
       t.sensitivity AS sensitivity,
       t.example_queries AS example_queries
ORDER BY t.name
```

### Get Full Graph (All Nodes + Edges)

```cypher
-- Source: User decision (query patterns)
-- Repository method: get_full_graph(database: str)

-- Get all table nodes
MATCH (t:Table {database: $database})
WITH collect({
    name: t.name,
    description: t.description,
    sensitivity: t.sensitivity
}) AS nodes

-- Get all relationships
MATCH (source:Table {database: $database})
      -[r:REFERENCES_VIA]->(target:Table)
WITH nodes, collect({
    source: source.name,
    target: target.name,
    fk_column: r.fk_column,
    referenced_column: r.referenced_column
}) AS edges

RETURN nodes, edges
```

### Transaction Pattern with Error Handling

```python
# Source: https://neo4j.com/docs/python-manual/current/transactions/
from neo4j import Driver
from neo4j.exceptions import Neo4jError

def write_catalog_entry(driver: Driver, entry: CatalogEntry, database_name: str) -> None:
    """Write catalog entry with proper error handling."""
    query = """
    MERGE (t:Table {name: $table_name, database: $database})
    ON CREATE SET
        t.description = $description,
        t.sensitivity = $sensitivity,
        t.example_queries = $example_queries
    ON MATCH SET
        t.description = $description,
        t.sensitivity = $sensitivity,
        t.example_queries = $example_queries
    RETURN t
    """

    try:
        driver.execute_query(
            query,
            table_name=entry.table_name,
            database=database_name,
            description=entry.description,
            sensitivity=entry.sensitivity,
            example_queries=entry.example_queries,
            database_="neo4j"
        )
    except Neo4jError as e:
        # Check if retryable (transient failure)
        if e.is_retryable():
            raise  # Let driver retry automatically
        else:
            # Permanent error, log and propagate
            raise RuntimeError(f"Failed to write {entry.table_name}: {e.message}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| neo4j-driver package | neo4j package | Version 6.0.0 (2024) | neo4j-driver deprecated, use neo4j instead. Same API, different package name. |
| session.run() auto-commit | driver.execute_query() | Driver 5.x (2023) | execute_query() simplifies common case, automatic retry, better routing. Use execute_query() for single queries. |
| Base image debian:bullseye | Base image debian:trixie | Neo4j 2026.01 (Jan 2026) | Newer Debian version, security updates. Specify tag explicitly if bullseye required. |
| Manual Cypher parameter handling | Parameterized queries required | Always | Driver handles escaping, prevents injection. NEVER concatenate strings for Cypher. |
| Python 3.8-3.9 support | Python 3.10+ required | Neo4j driver 6.0+ (2024) | Driver requires Python 3.10+. Project already uses Python 3.11 (pyproject.toml). |

**Deprecated/outdated:**
- `neo4j-driver` package: Replaced by `neo4j` package. Last update 5.28.3. Use `neo4j` instead.
- `session.run()` for production: Still works but routes all queries to leader, no retry. Use `execute_query()` or managed transactions.
- `driver.session()` without context manager: Causes connection leaks. Always use `with driver.session()` or `execute_query()`.

## Open Questions

1. **Index Strategy for Large Catalogs**
   - What we know: Neo4j supports range indexes on properties, constraints create indexes automatically, indexes speed reads but slow writes
   - What's unclear: At what catalog size (number of tables) do we need indexes on Table.name? Will Phase 6 search queries be slow without full-text indexes on descriptions?
   - Recommendation: Start without indexes (simpler). Add range index on (Table.name, Table.database) composite if Phase 6 UI shows slow search. Add full-text index on Table.description if keyword search is slow. Measure first, optimize later.

2. **Concurrent Write Safety**
   - What we know: MERGE is atomic, handles race conditions, user decided "write after each table"
   - What's unclear: If multiple catalog runs happen simultaneously (different databases), will they conflict? Neo4j supports concurrent writes at node level.
   - Recommendation: No conflict expected (different database nodes, different table nodes). Test with concurrent cataloging in Phase 6 if needed. Accept risk for v1.

3. **Cypher Query Performance Monitoring**
   - What we know: Neo4j provides PROFILE and EXPLAIN for query analysis, driver returns summary with timing
   - What's unclear: Should we log query times? Alert on slow queries? What's acceptable latency for Phase 6 UI queries?
   - Recommendation: Log query times in development. Establish baseline (< 100ms for get_table, < 500ms for list_tables). Add monitoring if Phase 6 shows performance issues.

4. **Neo4j Authentication in Production**
   - What we know: User decided environment variables with defaults for local Docker, docker-compose uses NEO4J_AUTH
   - What's unclear: Production deployment beyond local? Cloud Neo4j Aura? Different auth schemes (LDAP, SSO)?
   - Recommendation: v1 uses basic auth (username/password) via environment variables. Document production deployment in Phase 6 or defer to v2.

## Sources

### Primary (HIGH confidence)

- [Neo4j Python Driver Manual](https://neo4j.com/docs/python-manual/current/) - Connection, transactions, execute_query patterns
- [Neo4j Python Driver API 6.1](https://neo4j.com/docs/api/python-driver/current/) - Full API reference, verify_connectivity, Driver methods
- [Neo4j PyPI Package](https://pypi.org/project/neo4j/) - Version 6.1.0, release date Jan 12 2026, Python 3.10+ requirement
- [Neo4j Docker Compose Deployment](https://neo4j.com/docs/operations-manual/current/docker/docker-compose-standalone/) - docker-compose.yml, NEO4J_AUTH, ports 7474/7687
- [Neo4j MERGE Clause Documentation](https://neo4j.com/docs/cypher-manual/current/clauses/merge/) - MERGE syntax, ON CREATE/ON MATCH, upsert patterns
- [Neo4j Understanding MERGE](https://neo4j.com/developer/kb/understanding-how-merge-works/) - Node-first pattern, avoiding duplicates
- [Neo4j Relational to Graph Modeling](https://neo4j.com/docs/getting-started/data-modeling/relational-to-graph-modeling/) - Tables to nodes, foreign keys to relationships
- [Neo4j Constraints Documentation](https://neo4j.com/docs/cypher-manual/current/constraints/) - Unique constraints, relationship between constraints and indexes
- [Neo4j Driver Best Practices](https://neo4j.com/developer-blog/neo4j-driver-best-practices/) - execute_query vs session.run, routing, common mistakes
- [Neo4j Transaction Patterns](https://neo4j.com/docs/python-manual/current/transactions/) - execute_read, execute_write, auto-commit vs managed transactions
- [Neo4j Performance Recommendations](https://neo4j.com/docs/python-manual/current/performance/) - Specify database, lazy loading, Rust extension, batch patterns

### Secondary (MEDIUM confidence)

- [Neo4j Docker Hub](https://hub.docker.com/_/neo4j) - Version tags 2026.01.4, 5.26 LTS, community vs enterprise, base images
- [Testcontainers Neo4j Module](https://testcontainers.com/modules/neo4j/) - Neo4jContainer usage, Python examples
- [Testcontainers Python PyPI](https://pypi.org/project/testcontainers/) - Version 4.10+, released Jan 31 2026
- [Neo4j GitHub Python Driver](https://github.com/neo4j/neo4j-python-driver) - Official repository, issues, release notes
- [Neo4j MATCH Clause Documentation](https://neo4j.com/docs/cypher-manual/current/clauses/match/) - Relationship patterns, graph traversal
- [Neo4j Connection Documentation](https://neo4j.com/docs/python-manual/current/connect/) - URI schemes, authentication, verify_connectivity

### Tertiary (LOW confidence)

None - All findings verified with official documentation or multiple authoritative sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Neo4j 6.1.0 verified on PyPI (Jan 2026), official docs current, driver widely adopted
- Architecture: HIGH - Patterns from official Neo4j docs, verified with Cypher manual, matches project conventions (repository pattern, dependency injection, existing model reuse)
- Pitfalls: HIGH - Documented in official best practices guide, Neo4j KB articles, community patterns verified across multiple sources
- Docker setup: HIGH - Official operations manual, docker-compose examples verified, LTS version confirmed
- Testing: MEDIUM-HIGH - Testcontainers documented for Python, examples available, no project-specific integration yet

**Research date:** 2026-02-23
**Valid until:** 60 days (Neo4j stable, driver versioned, graph patterns established)
