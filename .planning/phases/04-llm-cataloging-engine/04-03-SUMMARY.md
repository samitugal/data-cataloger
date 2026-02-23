---
phase: 04-llm-cataloging-engine
plan: 03
subsystem: cataloging
tags: [prompts, llm, context-aware]
dependency_graph:
  requires: [schema-models, catalog-models]
  provides: [prompt-templates, context-builder]
  affects: [cataloging-agent]
tech_stack:
  added: []
  patterns: [system-user-prompt-separation, context-aware-prompts]
key_files:
  created:
    - src/data_cataloger/cataloging/prompts.py
    - tests/cataloging/test_prompts.py
  modified: []
decisions:
  - title: System vs User Prompt Separation
    rationale: Separates agent behavior (system) from table-specific data (user) for consistency
    alternatives: Single combined prompt (less maintainable)
  - title: Include Parent Context in User Prompt
    rationale: Enables LLM to leverage already-cataloged table descriptions for better analysis
    alternatives: Catalog tables independently (misses relationship context)
  - title: Line-continuation for Long String Literals
    rationale: Keep code under 88 char line limit while preserving multiline string readability
    alternatives: Ignore line length (fails ruff), break string across lines (hurts readability)
metrics:
  duration_minutes: 7
  completed_date: 2026-02-23
---

# Phase 04 Plan 03: Prompt Templates and Builder Summary

**One-liner:** Context-aware prompt builder generates LLM-ready prompts with table metadata (columns, PKs, FKs) and parent table descriptions for dependency-aware cataloging

## What Was Built

### Core Implementation

1. **SYSTEM_PROMPT constant** (src/data_cataloger/cataloging/prompts.py)
   - Defines agent role as database documentation expert
   - Documents all 4 sensitivity classifications (PII, financial, public, internal)
   - Specifies expected outputs (description, sensitivity, example queries)
   - Instructs agent to consider foreign key relationships
   - Mentions parent table context usage

2. **build_user_prompt function** (src/data_cataloger/cataloging/prompts.py)
   - Accepts TableMetadata and list[CatalogEntry] parameters
   - Generates structured prompt with table name and columns
   - Includes data types and NOT NULL indicators
   - Conditionally includes Primary Key section (only when PKs exist)
   - Conditionally includes Foreign Keys section (only when FKs exist)
   - Conditionally includes Referenced Tables Context (only when parent_context non-empty)
   - Returns complete prompt string ready for LLM consumption

### Testing

Created comprehensive test suite (9 tests, 100% coverage):
- test_system_prompt_exists: Validates all sensitivity types documented
- test_build_user_prompt_basic_table: Verifies table name and columns included
- test_build_user_prompt_with_primary_key: PK section when present
- test_build_user_prompt_with_foreign_keys: All FK relationships listed
- test_build_user_prompt_with_parent_context: Parent descriptions included
- test_build_user_prompt_nullable_columns: NOT NULL indicator correct
- test_build_user_prompt_composite_foreign_key: Composite FKs all listed
- test_build_user_prompt_empty_parent_context: No context section when empty
- test_build_user_prompt_multiple_parent_context: Multiple parents included

### Verification

All quality checks passed:
- mypy --strict: No type errors
- ruff check: No violations
- pytest: 9/9 tests pass, 100% coverage
- Manual verification: Generated prompt includes all metadata elements
- Prompt readability confirmed with realistic 7-column table example

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added py.typed marker**
- **Found during:** Task 1 verification
- **Issue:** mypy --strict failed with "module is installed, but missing library stubs or py.typed marker"
- **Fix:** Created src/data_cataloger/cataloging/py.typed (empty marker file)
- **Files modified:** src/data_cataloger/cataloging/py.typed (created)
- **Commit:** Included in 517383b (Task 1 commit)

**2. [Rule 3 - Blocking Issue] Created minimal CatalogEntry stub**
- **Found during:** Task 1 start
- **Issue:** Plan 04-03 requires CatalogEntry from plan 04-01, but 04-01 hadn't been executed yet. Plan lists depends_on: [] but actually needs CatalogEntry model.
- **Fix:** Created minimal models.py with CatalogEntry dataclass to unblock prompt development. This was later replaced by full implementation from plan 04-01.
- **Files modified:** src/data_cataloger/cataloging/models.py (temporary stub, later replaced)
- **Commit:** Not committed separately (replaced by 04-01 execution)
- **Note:** Upon execution start, discovered plans 04-01 and 04-02 had already been executed prior to this session. The stub was unnecessary but harmless.

**3. [Rule 2 - Code Quality] Fixed line length violation**
- **Found during:** Task 1 commit
- **Issue:** Pre-commit hook failed on "SYSTEM_PROMPT = """You are a database documentation expert. Analyze table metadata and generate:" (96 > 88 chars)
- **Fix:** Added line continuation backslash to break long line while preserving string literal
- **Files modified:** src/data_cataloger/cataloging/prompts.py
- **Commit:** Fixed before commit, included in 517383b

**4. [Rule 2 - Code Quality] Ruff format auto-reformatting**
- **Found during:** Task 1 and Task 2 commits
- **Issue:** Pre-commit ruff-format hook reformatted files automatically
- **Fix:** Re-staged reformatted files and committed again
- **Files modified:** prompts.py and test_prompts.py
- **Commit:** Reformatted versions included in final commits

## Technical Decisions

### 1. System vs User Prompt Separation
**Decision:** Separate SYSTEM_PROMPT (agent behavior) from user prompts (table data)

**Rationale:**
- System prompt remains constant across all table analyses
- User prompt varies per table with specific metadata
- Follows OpenAI best practices for consistent agent behavior
- Makes prompt maintenance easier (update agent instructions once)

**Implementation:** SYSTEM_PROMPT constant + build_user_prompt function

### 2. Conditional Prompt Sections
**Decision:** Include PK, FK, and parent context sections only when data exists

**Rationale:**
- Reduces prompt bloat for simple tables (no PKs or FKs)
- Avoids confusing LLM with empty sections
- Makes prompts cleaner and more focused

**Implementation:** if table.primary_keys, if table.foreign_keys, if parent_context checks

### 3. Parent Context Format
**Decision:** List parent tables with descriptions in simple bullet format

**Example:**
```
Referenced Tables Context:
- users: User account information
- products: Product catalog
```

**Rationale:**
- Concise format easy for LLM to parse
- Provides enough context to understand table relationships
- Avoids overwhelming LLM with full parent metadata

## Integration Points

### Consumes
- **TableMetadata** (from data_cataloger.schema.models): Source of table structure
- **CatalogEntry** (from data_cataloger.cataloging.models): Parent table descriptions

### Provides
- **SYSTEM_PROMPT**: Agent behavior definition for LLM calls
- **build_user_prompt**: Function to generate table-specific prompts

### Used By (Next Plan)
- Plan 04-04 (Cataloging Agent): Will use SYSTEM_PROMPT and build_user_prompt to call OpenAI API

## Testing Coverage

| File | Statements | Coverage |
|------|-----------|----------|
| prompts.py | 20 | 100% |

**Test Quality:**
- All code paths covered (conditional sections tested individually)
- Edge cases validated (empty lists, nullable columns, composite FKs)
- Integration verified with realistic multi-column table example

## Files Changed

**Created:**
- src/data_cataloger/cataloging/prompts.py (77 lines)
- tests/cataloging/test_prompts.py (343 lines)

**Modified:**
- None

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 517383b | feat | Create prompt templates and builder |
| f8f73b4 | test | Add comprehensive prompt builder tests |

## Next Steps

Ready for Plan 04-04 (Cataloging Agent):
1. Import SYSTEM_PROMPT and build_user_prompt
2. Integrate with CatalogClient (from Plan 04-02)
3. Use CatalogState to get parent context for each table
4. Call LLM with generated prompts to produce catalog entries

## Self-Check: PASSED

Verified all deliverables:
- ✓ src/data_cataloger/cataloging/prompts.py exists
- ✓ tests/cataloging/test_prompts.py exists
- ✓ Commit 517383b exists (Task 1)
- ✓ Commit f8f73b4 exists (Task 2)
- ✓ SYSTEM_PROMPT constant exported
- ✓ build_user_prompt function exported
- ✓ All tests pass (9/9)
- ✓ 100% test coverage achieved
- ✓ mypy --strict passes
- ✓ ruff check passes
