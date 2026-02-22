---
phase: 03-schema-analysis
plan: 04
subsystem: schema
tags: [dependency-graph, topological-sort, graphlib, cycle-detection]
completed: 2026-02-22

dependencies:
  requires:
    - 03-01 (TableMetadata models for dependency extraction)
  provides:
    - DependencyGraph class with add_table() and get_processing_order() methods
    - Topological sort for table processing order
    - Circular dependency detection with cycle node reporting
  affects:
    - schema.introspector (will use DependencyGraph to order table analysis)
    - cataloging agents (will process tables in dependency order)

tech_stack:
  added:
    - graphlib.TopologicalSorter (Python 3.9+ stdlib)
    - graphlib.CycleError for cycle detection
  patterns:
    - Wrapper class pattern for domain-specific API over stdlib
    - Self-reference filtering for hierarchical table support
    - Tuple return (ordered_tables, cycle_nodes) for error signaling

key_files:
  created:
    - src/data_cataloger/schema/dependency.py (71 lines, DependencyGraph class)
    - tests/schema/test_dependency.py (143 lines, 8 comprehensive tests)
  modified: []

decisions:
  - key: Filter self-references instead of passing to TopologicalSorter
    rationale: graphlib treats self-references as cycles, but hierarchical tables (e.g., categories.parent_id) are valid and processable independently
    alternatives: [Custom cycle detection, NetworkX library, Warn on self-reference]
    impact: Enables correct handling of hierarchical structures; tables like categories/org_units can be analyzed

  - key: Return tuple (ordered_tables, cycle_nodes) instead of raising exception
    rationale: Caller needs both success path (ordered list) and error path (cycle nodes) without exception handling
    alternatives: [Raise custom exception, Return Optional[list], Separate methods]
    impact: Simpler API for callers; explicit handling of both cases in single pattern

  - key: Use static_order() not prepare() method
    rationale: static_order() returns complete ordered list immediately; prepare() is for incremental consumption
    alternatives: [prepare() + ready() iteration, Manual DFS]
    impact: Simpler implementation; complete order available at once for batch processing

metrics:
  duration_minutes: 2
  tasks_completed: 2
  tests_written: 8
  coverage_percent: 100
  lines_of_code: 214
---

# Phase 03 Plan 04: Dependency Graph Builder Summary

**Topological sort wrapper using graphlib with self-reference filtering for hierarchical table support**

## What Was Built

Implemented DependencyGraph class wrapping Python's stdlib graphlib.TopologicalSorter to calculate table processing order based on foreign key dependencies. The class filters self-referencing foreign keys (hierarchical structures) to avoid false cycle detection, while properly detecting true circular dependencies between distinct tables.

**Key features:**
- `add_table(table, dependencies)`: Registers table with FK dependencies, auto-filtering self-references
- `get_processing_order()`: Returns `(ordered_tables, cycle_nodes)` tuple - ordered list on success, cycle nodes on circular dependency
- Handles edge cases: empty graphs, single tables, parallel independent tables, multi-level dependencies
- 100% test coverage with 8 comprehensive scenarios

## Tasks Completed

### Task 1: Create dependency graph class
**Commit:** 114ec26 (combined with Task 2)
**Files:** src/data_cataloger/schema/dependency.py

Created DependencyGraph class following 03-RESEARCH.md Pattern 3:
- Wraps graphlib.TopologicalSorter with domain-specific API
- `__init__()`: Initializes empty TopologicalSorter and tracks added tables
- `add_table()`: Adds table with dependencies, filters self-references (critical for hierarchical tables)
- `get_processing_order()`: Calls `static_order()`, catches CycleError, returns tuple
- Full type annotations with mypy --strict compliance
- Comprehensive docstrings with examples

**Auto-fix applied (Rule 1 - Bug):**
- **Found during:** Task 2 test execution
- **Issue:** graphlib.TopologicalSorter treats self-references (e.g., `categories` depends on `categories`) as cycles, causing CycleError for hierarchical tables
- **Fix:** Added `filtered_deps = [dep for dep in dependencies if dep != table]` to filter self-references before adding to sorter
- **Rationale:** Hierarchical tables with parent_id FK to same table are valid structures, not dependency cycles
- **Files modified:** src/data_cataloger/schema/dependency.py (lines 42-43)
- **Commit:** 114ec26 (included in Task 2 commit)

### Task 2: Write dependency graph tests
**Commit:** 114ec26
**Files:** tests/schema/test_dependency.py

Created 8 comprehensive tests covering all dependency scenarios:

1. **test_simple_dependency_chain**: Linear A → B → C ordering
2. **test_parallel_independent_tables**: Multiple roots (users, products) before dependent (orders)
3. **test_self_referencing_table**: Hierarchical categories table not treated as cycle
4. **test_circular_dependency_detected**: True cycle A ↔ B returns empty order + cycle nodes
5. **test_complex_graph**: Multi-level dependencies (users → posts → comments → likes)
6. **test_empty_graph**: Edge case returns ([], None)
7. **test_single_table_no_dependencies**: Single table returns ([table], None)
8. **test_multiple_roots**: Multiple independent root tables before dependents

All tests verify:
- Correct ordering (parents before children)
- Cycle detection accuracy (cycle vs. no cycle)
- Return value structure (tuple of lists)

Coverage: 100% on dependency.py (16/16 statements)

## Verification Results

All verification steps passed:

```bash
✓ uv run pytest tests/schema/test_dependency.py -v               # 8 tests passed
✓ uv run pytest --cov=src/data_cataloger/schema/dependency       # 100% coverage (16/16 statements)
✓ uv run mypy --strict src/data_cataloger/schema/dependency.py   # No issues found
✓ uv run ruff check src/data_cataloger/schema/                   # All checks passed
```

## Success Criteria Verification

- [x] DependencyGraph class exists with add_table() and get_processing_order() methods
- [x] Uses graphlib.TopologicalSorter from Python stdlib (no external dependencies)
- [x] CycleError exception caught and converted to ([], cycle_nodes) return
- [x] Self-referencing tables handled correctly (filtered, not treated as cycles)
- [x] Tests pass with 8 tests covering simple, complex, parallel, self-referencing, and circular cases
- [x] Code coverage 100% on dependency.py (16/16 statements)
- [x] mypy --strict passes on dependency.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed self-reference cycle detection**
- **Found during:** Task 2 (test_self_referencing_table test failure)
- **Issue:** Python's `graphlib.TopologicalSorter` treats self-references as cycles. Test `test_self_referencing_table()` failed with `CycleError` when adding `categories` table with dependency on itself.
- **Fix:** Modified `add_table()` method to filter out self-references before passing to TopologicalSorter: `filtered_deps = [dep for dep in dependencies if dep != table]`
- **Files modified:** src/data_cataloger/schema/dependency.py (line 42-43)
- **Commit:** 114ec26
- **Rationale:** Per plan requirement "Self-referencing tables are handled correctly (not treated as cycles)" - hierarchical tables like categories (parent_id FK to same table) are valid structures that can be processed independently

## Next Steps

Next plan (03-05) will integrate DependencyGraph with schema extractors (PostgreSQL/MySQL) to build complete TableMetadata graphs and calculate processing order for the cataloging phase.

## Self-Check: PASSED

**Files created:**
- src/data_cataloger/schema/dependency.py exists ✓
- tests/schema/test_dependency.py exists ✓

**Commits exist:**
- 114ec26 (Combined Task 1 + Task 2 with self-reference fix) ✓

**Coverage verification:**
- dependency.py: 16/16 statements (100%) ✓
- All 8 tests passing ✓
- mypy --strict passes ✓

All deliverables verified and present.
