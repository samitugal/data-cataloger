---
phase: 01-project-setup
plan: 02
subsystem: tooling
tags: [ruff, pytest, mypy, pre-commit, ci-cd, github-actions]

dependency-graph:
  requires: [01-01]
  provides: [quality-checks, testing-framework, ci-pipeline]
  affects: [development-workflow]

tech-stack:
  added:
    - ruff (linter/formatter)
    - pytest (testing framework)
    - pytest-cov (coverage tracking)
    - mypy (type checker)
    - pre-commit (git hook manager)
  patterns:
    - Pre-commit hooks for local quality gates
    - GitHub Actions matrix testing (Python 3.11, 3.12)
    - Strict type checking with disallow_untyped_defs
    - Coverage reporting to Codecov

key-files:
  created:
    - .pre-commit-config.yaml: Pre-commit hook configuration
    - .github/workflows/ci.yml: GitHub Actions CI/CD workflow
    - tests/conftest.py: Shared pytest fixtures
  modified:
    - pyproject.toml: Added tool configurations for Ruff, pytest, mypy
    - uv.lock: Updated dependencies

decisions:
  - Use Ruff instead of Black + Flake8 + isort (modern unified tooling)
  - Enable strict mypy type checking from the start (disallow_untyped_defs=true)
  - Matrix testing for Python 3.11 and 3.12 (ensure broad compatibility)
  - Use astral-sh/setup-uv action for fast CI dependency installation
  - Configure mypy with --ignore-missing-imports for gradual typing adoption

metrics:
  duration: 4 minutes
  tasks_completed: 3
  files_created: 3
  files_modified: 3
  commits: 3
  completed: 2026-02-21T06:51:44Z
---

# Phase 01 Plan 02: Development Tooling & CI/CD Summary

**One-liner:** Configured Ruff, pytest, mypy with pre-commit hooks and GitHub Actions CI/CD running quality checks on every commit and push.

## Tasks Completed

### Task 1: Configure Ruff, pytest, and mypy in pyproject.toml
**Commit:** 4202d10
**Status:** Complete

- Added pytest (9.0.2) and pytest-cov (7.0.0) as runtime dependencies
- Added ruff (0.15.2), mypy (1.19.1), and pre-commit (4.5.1) as dev dependencies
- Configured Ruff for Python 3.11 with line length 88 and standard linting rules (E, F, I, N, W, UP)
- Configured pytest to run tests from tests/ directory with coverage tracking enabled
- Configured mypy for strict type checking with disallow_untyped_defs=true
- All tools verified working: `uv run ruff check .`, `uv run mypy --version`, `uv run pytest --version`

**Files modified:**
- pyproject.toml (added [tool.ruff], [tool.pytest.ini_options], [tool.mypy] sections)
- uv.lock (updated with new dependencies)

### Task 2: Set up pre-commit hooks
**Commit:** ac94c48
**Status:** Complete

- Created .pre-commit-config.yaml with four repos configured:
  - astral-sh/ruff-pre-commit (v0.15.2): ruff-check with --fix, ruff-format
  - pre-commit/mirrors-mypy (v1.13.0): mypy with --ignore-missing-imports
  - pre-commit/pre-commit-hooks (v5.0.0): trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files
- Installed pre-commit hooks in git repository (.git/hooks/pre-commit created)
- Successfully ran pre-commit on all files (auto-fixed trailing whitespace in .gitignore)
- Git commits now trigger automated quality checks

**Files created:**
- .pre-commit-config.yaml

**Files modified:**
- .gitignore (trailing whitespace auto-fixed by pre-commit)

### Task 3: Create GitHub Actions CI/CD workflow and basic test structure
**Commit:** 69c079c
**Status:** Complete

- Created .github/workflows/ci.yml with comprehensive CI pipeline
- Workflow triggers on push to main and pull requests
- Matrix testing covers Python 3.11 and 3.12 for broad compatibility
- Uses astral-sh/setup-uv@v7 for fast cached dependency installation
- CI steps: checkout, install uv, set up Python, install dependencies, run ruff check, run ruff format --check, run mypy, run pytest with coverage, upload coverage to Codecov (Python 3.12 only)
- Created tests/conftest.py with example fixture structure
- Added type annotation (dict[str, str]) to sample_fixture for mypy compliance

**Files created:**
- .github/workflows/ci.yml
- tests/conftest.py

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added return type annotation to sample_fixture**
- **Found during:** Task 3 commit (pre-commit hook caught mypy error)
- **Issue:** Function `sample_fixture()` in tests/conftest.py was missing return type annotation, violating mypy's disallow_untyped_defs rule
- **Fix:** Added `-> dict[str, str]` return type annotation to the fixture
- **Files modified:** tests/conftest.py
- **Commit:** 69c079c (included in task 3 commit)
- **Reason:** Auto-fixed per Deviation Rule 1 (bug - code doesn't meet type checking requirements)

**2. [Rule 2 - Critical functionality] Changed mypy additional_dependencies from types-all to empty array**
- **Found during:** Task 2 (pre-commit run failed with types-all dependency resolution error)
- **Issue:** types-all package has yanked versions and missing dependencies (types-pkg-resources), causing pre-commit installation to fail
- **Fix:** Removed types-all from additional_dependencies and added --ignore-missing-imports flag to mypy args
- **Files modified:** .pre-commit-config.yaml
- **Commit:** ac94c48 (included in task 2 commit)
- **Reason:** Auto-fixed per Deviation Rule 3 (blocking issue - prevented completing task 2)
- **Impact:** Enables gradual typing adoption without breaking on missing stub files

## Verification Results

All verification steps passed:

1. **Local tool verification:**
   - `uv run ruff check .` → All checks passed
   - `uv run ruff format --check .` → 7 files already formatted
   - `uv run mypy src/` → Success: no issues found in 6 source files
   - `uv run pytest` → No tests collected (expected - infrastructure setup only)

2. **Pre-commit integration:**
   - Pre-commit hooks installed at .git/hooks/pre-commit
   - `uv run pre-commit run --all-files` → All hooks passed
   - Git commit triggers hooks automatically (verified during task 2 and 3 commits)

3. **GitHub Actions workflow:**
   - YAML syntax validated successfully
   - Workflow ready to run on next push to GitHub

4. **Coverage tracking:**
   - Coverage configured in pytest
   - HTML coverage reports generated to htmlcov/
   - XML coverage reports generated for Codecov integration

## Success Criteria Met

- [x] All development tools (Ruff, pytest, mypy, pre-commit) are installed and configured
- [x] pyproject.toml contains complete tool configurations
- [x] Pre-commit hooks run automatically on git commit
- [x] GitHub Actions workflow validates code on every push
- [x] Matrix testing covers Python 3.11 and 3.12
- [x] Coverage tracking is enabled and generates reports
- [x] All quality checks can be run locally with uv run commands

## Key Decisions

1. **Ruff over Black + Flake8 + isort:** Modern unified tooling reduces configuration complexity and improves performance
2. **Strict mypy from the start:** disallow_untyped_defs=true enforces type annotations on all functions, preventing type debt
3. **Matrix testing:** Testing on both Python 3.11 and 3.12 ensures compatibility across supported versions
4. **astral-sh/setup-uv in CI:** Leverages uv's speed and caching for fast CI runs
5. **Gradual typing with --ignore-missing-imports:** Allows development to proceed without blocking on missing type stubs for third-party libraries

## Impact on Project

**Immediate:**
- All code changes now validated locally via pre-commit hooks before commit
- Type safety enforced from the start (prevents accumulation of untyped code)
- Automated formatting ensures consistent code style

**Future:**
- CI pipeline ready to catch issues before merge
- Coverage tracking will highlight untested code paths
- Matrix testing prevents Python version compatibility issues

**Development workflow:**
- Developers run `uv run ruff check .` for linting
- Developers run `uv run ruff format .` for auto-formatting
- Developers run `uv run mypy src/` for type checking
- Developers run `uv run pytest` for testing with coverage
- Pre-commit hooks catch issues automatically on commit
- GitHub Actions validates all changes on push/PR

## Next Steps

Following ROADMAP.md, next plan is 01-03 (Environment Configuration).

Suggested focus areas:
- Environment variable management (.env file structure)
- Configuration for database connections (PostgreSQL, MySQL metadata access)
- Neo4j connection configuration
- LLM provider API configuration (OpenAI, Anthropic, etc.)

## Self-Check: PASSED

**Files exist:**
- FOUND: pyproject.toml
- FOUND: .pre-commit-config.yaml
- FOUND: .github/workflows/ci.yml
- FOUND: tests/conftest.py

**Commits exist:**
- FOUND: 4202d10
- FOUND: ac94c48
- FOUND: 69c079c

All claimed files and commits verified successfully.
