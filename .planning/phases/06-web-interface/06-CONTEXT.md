# Phase 6: Web Interface - Context

## Phase Dependencies

### From Phase 5: Graph Storage

```python
# Available from storage module
from data_cataloger.storage import Neo4jConfig, Neo4jWriter, GraphRepository

# GraphRepository methods available:
repo.get_table(table_name, database_name) -> CatalogEntry | None
repo.list_tables(database_name) -> list[CatalogEntry]
repo.get_relationships(table_name, database_name) -> list[dict]
repo.get_full_graph(database_name) -> dict[str, list[dict]]
repo.search_by_sensitivity(sensitivity, database_name) -> list[CatalogEntry]
repo.search_by_keyword(keyword, database_name) -> list[CatalogEntry]
```

### From Phase 4: Cataloging

```python
# CatalogEntry domain object
from data_cataloger.cataloging import CatalogEntry

@dataclass(frozen=True)
class CatalogEntry:
    table_name: str
    description: str
    sensitivity: str  # "PII" | "financial" | "public" | "internal"
    example_queries: list[str]
```

### From Phase 2: Connection

```python
# Database configuration
from data_cataloger.connection import DatabaseConfig
```

## Key Files to Reference

| File | Purpose |
|------|---------|
| `src/data_cataloger/storage/repository.py` | GraphRepository implementation |
| `src/data_cataloger/storage/config.py` | Neo4jConfig for connection |
| `src/data_cataloger/cataloging/models.py` | CatalogEntry dataclass |
| `docker-compose.yml` | Neo4j container configuration |

## Existing Patterns to Follow

### Dependency Injection
- Use Protocol for interfaces (see CatalogWriter)
- Constructor injection for dependencies
- Optional parameters with defaults

### Error Handling
- Log warnings for non-critical failures
- Raise ValueError for invalid inputs
- Use try/except with specific exceptions

### Type Safety
- mypy --strict compliance required
- Use Pydantic for API schemas
- Frozen dataclasses for domain objects

### Testing
- Mock external dependencies (Neo4j driver)
- pytest with coverage
- Arrange/Act/Assert pattern

## Configuration

### Neo4j Connection (from docker-compose.yml)
```yaml
NEO4J_URI: bolt://localhost:7687
NEO4J_USER: neo4j
NEO4J_PASSWORD: password
NEO4J_DATABASE: neo4j
```

### Environment Variables Needed
```bash
# Neo4j (existing)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Web server (new)
WEB_HOST=0.0.0.0
WEB_PORT=8000
DATABASE_NAME=production_db  # Target database for queries
```

## Constraints

- Python 3.11+ required
- No React/Vue/Angular - vanilla JS only
- CDN dependencies for frontend
- Must work with existing Neo4j schema
- Mobile-responsive design required

---
*Context established: 2026-02-23*
