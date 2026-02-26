# Technical Debt Report

**Generated:** 2026-02-26

## Summary

| Metric | Value |
|--------|-------|
| **Total Python Files** | 41 |
| **Total Lines of Code** | 4,418 |
| **Test Coverage** | 66% |
| **Tests Passing** | 186/186 |
| **Lint Errors** | 0 |
| **Type Errors (mypy)** | 0 |
| **TODOs/FIXMEs** | 0 |

---

## Coverage Analysis

### Well Covered (>90%)
- `cataloging/client.py` - 100%
- `cataloging/models.py` - 100%
- `cataloging/prompts.py` - 100%
- `connection/credentials.py` - 100%
- `connection/config.py` - 100%
- `schema/models.py` - 100%
- `schema/dependency.py` - 100%
- `storage/repository.py` - 93%
- `storage/writer.py` - 93%
- `web/routes/graph.py` - 100%
- `web/routes/tables.py` - 100%

### Needs More Tests (<50%)
| File | Coverage | Missing |
|------|----------|---------|
| `mcp/server.py` | 0% | Full integration tests needed |
| `mcp/__main__.py` | 0% | Entry point, hard to test |
| `export/exporter.py` | 18% | Export format tests |
| `export/importer.py` | 31% | Import tests |
| `embeddings/client.py` | 38% | OpenAI mock tests |
| `web/routes/cataloging.py` | 39% | Background task tests |
| `web/routes/progress.py` | 52% | SSE event tests |

---

## Code Quality Issues

### Large Files (>300 lines)
| File | Lines | Recommendation |
|------|-------|----------------|
| `mcp/server.py` | 610 | Consider splitting into tools.py + handlers.py |
| `storage/repository.py` | 327 | OK - single responsibility |

### Potential Improvements

1. **MCP Server Refactoring**
   - Split `server.py` into:
     - `tools.py` - Tool definitions
     - `handlers.py` - Tool execution logic
     - `transport.py` - SSE/stdio transport

2. **Test Coverage**
   - Add integration tests for MCP server
   - Add export/import unit tests
   - Mock OpenAI for embedding tests

3. **Error Handling**
   - Add custom exception classes
   - Improve error messages for MCP tools

4. **Documentation**
   - Add API documentation (OpenAPI is auto-generated)
   - Add architecture diagram

---

## Dependencies

### Production (13 packages)
- fastapi, uvicorn, pydantic
- neo4j, openai, mcp
- psycopg, mysql-connector-python
- keyring, tenacity, sse-starlette

### Development (5 packages)
- pytest, pytest-cov
- ruff, mypy, types-PyYAML
- pre-commit, testcontainers

### Security
- No known vulnerabilities
- Credentials handled via keyring (not hardcoded)

---

## Action Items

### High Priority
- [ ] Add MCP server integration tests
- [ ] Add export/import unit tests

### Medium Priority
- [ ] Split mcp/server.py into smaller modules
- [ ] Add custom exception classes
- [ ] Improve SSE progress tracking tests

### Low Priority
- [ ] Add architecture diagram to README
- [ ] Add API usage examples
- [ ] Consider adding OpenTelemetry for observability

---

## Conclusion

The codebase is in **good shape**:
- ✅ Zero lint errors
- ✅ Zero type errors
- ✅ All tests passing
- ✅ 66% coverage (acceptable for MVP)
- ✅ No TODOs or FIXMEs left behind

Main technical debt is in **test coverage** for newer modules (MCP, Export/Import).
