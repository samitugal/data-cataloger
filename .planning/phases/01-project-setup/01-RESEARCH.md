# Phase 1: Project Setup - Research

**Researched:** 2026-02-21
**Domain:** Python project initialization, tooling, and CI/CD
**Confidence:** HIGH

## Summary

Modern Python project setup in 2026 has consolidated around **uv** as the all-in-one tool for dependency management, environment handling, and project initialization. uv (from Astral, creators of Ruff) replaces pip, pip-tools, poetry, pyenv, and virtualenv with a single, extremely fast Rust-based tool. Combined with **Ruff** (linting and formatting) and **pytest** (testing), this stack provides comprehensive project foundation with minimal overhead.

For this data cataloging project with modular requirements (database connection, schema analysis, LLM cataloging, graph storage, web interface), the **src layout** is essential. This structure isolates importable code, prevents accidental imports during development, and supports the clean separation needed for modules like `connection/`, `schema/`, `cataloging/`, `storage/`, and `web/`.

CI/CD should leverage **GitHub Actions** with the official `astral-sh/setup-uv` action for fast, cached dependency installation. Pre-commit hooks using **Ruff** ensure code quality before commits, while automated workflows run full test suites and linting on every push.

**Primary recommendation:** Initialize with `uv init --package` for src layout, configure Ruff for linting/formatting, set up pytest with coverage tracking, and implement GitHub Actions with matrix testing across Python 3.11+.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| uv | Latest (0.5+) | Package management, environment handling, Python version management | 10-100x faster than pip; replaces multiple tools; official Astral tooling; industry standard for 2026 |
| Ruff | Latest (0.15.2+) | Linting and code formatting | 10-100x faster than Flake8/Black; >900 lint rules; 99.9% Black compatibility; unified linting+formatting |
| pytest | Latest (9.x) | Testing framework | Dominant Python test framework; simple syntax; powerful fixtures; 1300+ plugins; auto-discovery |
| mypy | Latest | Type checking | Industry standard static type checker; catches type errors before runtime |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-cov | Latest | Code coverage tracking | Always - ensures test coverage metrics |
| pre-commit | Latest | Git hook framework | Always - automates quality checks before commits |
| coverage | Latest | Coverage reporting | Always - integrates with pytest-cov for detailed reports |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| uv | Poetry 2.3+ | Poetry more mature but slower; use if team has existing Poetry codebase |
| Ruff formatter | Black | Black more established but 100x slower; use if team requires exact Black behavior |
| mypy | Pyright | Pyright faster and better VS Code integration; mypy more widely adopted |

**Installation:**
```bash
# Install uv (macOS/Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project with src layout
uv init --package automated-data-cataloger
cd automated-data-cataloger

# Add dependencies
uv add pytest pytest-cov

# Add dev dependencies
uv add --dev ruff mypy pre-commit
```

## Architecture Patterns

### Recommended Project Structure
```
automated-data-cataloger/
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI/CD
├── src/
│   └── automated_data_cataloger/
│       ├── __init__.py      # Package initialization
│       ├── connection/      # Database connection module
│       │   ├── __init__.py
│       │   └── database.py
│       ├── schema/          # Schema extraction module
│       │   ├── __init__.py
│       │   └── analyzer.py
│       ├── cataloging/      # LLM cataloging module
│       │   ├── __init__.py
│       │   └── agent.py
│       ├── storage/         # Neo4j storage module
│       │   ├── __init__.py
│       │   └── graph.py
│       └── web/             # Web interface module
│           ├── __init__.py
│           └── app.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared pytest fixtures
│   ├── test_connection/
│   ├── test_schema/
│   ├── test_cataloging/
│   ├── test_storage/
│   └── test_web/
├── docs/
│   └── README.md
├── .gitignore               # Python-specific ignores
├── .pre-commit-config.yaml  # Pre-commit hooks
├── .python-version          # Python version pin (e.g., 3.12)
├── pyproject.toml           # Project metadata and tool configs
├── uv.lock                  # Locked dependencies
├── LICENSE
└── README.md
```

### Pattern 1: Src Layout for Packages
**What:** Place all importable code under `src/package_name/` instead of project root.

**When to use:** Always for packages/libraries and applications that will be installed. Essential for projects with modular structure.

**Why:** Prevents accidental imports from development directory, ensures tests run against installed package, avoids packaging misconfiguration.

**Example:**
```python
# src/automated_data_cataloger/__init__.py
"""Automated Data Cataloger - LLM-powered database documentation."""

__version__ = "0.1.0"

# tests/test_connection/test_database.py
# This imports the INSTALLED package, not the local directory
from automated_data_cataloger.connection import database
```
Source: [Python Packaging User Guide - src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

### Pattern 2: pyproject.toml Configuration
**What:** Single configuration file for project metadata, dependencies, and tool settings.

**When to use:** Always for modern Python projects (2026 standard).

**Example:**
```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "automated-data-cataloger"
version = "0.1.0"
description = "Automatically document legacy databases using LLM-powered analysis"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
dependencies = [
    "pytest>=9.0.0",
    "pytest-cov>=6.0.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.15.2",
    "mypy>=1.13.0",
    "pre-commit>=4.0.0",
]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "--cov=src --cov-report=term-missing --cov-report=html"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```
Source: [Python Packaging User Guide - Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

### Pattern 3: Pre-commit Hooks
**What:** Automated code quality checks that run before every commit.

**When to use:** Always - prevents bad code from entering version control.

**Example:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.2
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```
Source: [astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)

### Pattern 4: GitHub Actions CI/CD
**What:** Automated testing, linting, and type checking on every push/PR.

**When to use:** Always - ensures code quality and prevents broken commits.

**Example:**
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "latest"
          enable-cache: true

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --locked --all-extras --dev

      - name: Run ruff check
        run: uv run ruff check .

      - name: Run ruff format
        run: uv run ruff format --check .

      - name: Run mypy
        run: uv run mypy src/

      - name: Run pytest
        run: uv run pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```
Source: [uv Documentation - Using uv in GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/)

### Pattern 5: Modular Package Organization
**What:** Separate functionality into distinct modules with single responsibilities.

**When to use:** Always for projects with multiple concerns (database, web, storage, etc.).

**Example:**
```python
# src/automated_data_cataloger/connection/__init__.py
"""Database connection module."""

from .database import DatabaseConnection, ConnectionConfig

__all__ = ["DatabaseConnection", "ConnectionConfig"]

# src/automated_data_cataloger/connection/database.py
"""Database connection handling for PostgreSQL and MySQL."""

from dataclasses import dataclass
from typing import Protocol

@dataclass
class ConnectionConfig:
    """Database connection configuration."""
    host: str
    port: int
    username: str
    password: str
    database: str
    db_type: str  # "postgresql" or "mysql"

class DatabaseConnection(Protocol):
    """Protocol for database connections."""

    def connect(self) -> None:
        """Establish database connection."""
        ...

    def test_connection(self) -> bool:
        """Test if connection is valid."""
        ...
```
Source: [Python Modules - Official Documentation](https://docs.python.org/3/tutorial/modules.html)

### Anti-Patterns to Avoid
- **Flat layout for packages:** Leads to import issues and packaging problems. Always use src layout for this modular project.
- **Global package installation:** Pollutes environment and causes version conflicts. Always use uv-managed virtual environments.
- **Committing .venv or __pycache__:** Bloats repository and causes merge conflicts. Always gitignore these.
- **No dependency locking:** Causes "works on my machine" issues. Always commit uv.lock.
- **Skipping pre-commit hooks:** Allows bad code into version control. Always run `pre-commit install` after clone.
- **Heavy __init__.py files:** Makes imports slow and circular dependencies likely. Keep __init__.py minimal.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dependency resolution | Custom requirements.txt parser | uv | Handles version conflicts, platform-specific deps, transitive dependencies; 100x faster |
| Code formatting | Custom style guide enforcer | Ruff formatter | 99.9% Black compatible, 100x faster, handles edge cases |
| Import sorting | Manual import organization | Ruff (isort rules) | Consistent ordering, handles conditional imports, PEP 8 compliant |
| Test discovery | Custom test finder | pytest | Auto-discovers tests, handles fixtures, parametrization, plugins |
| Coverage tracking | Manual line counting | pytest-cov | Accurate branch coverage, handles multiprocessing, detailed reports |
| Git hooks | Custom pre-commit scripts | pre-commit framework | Multi-language support, automatic updates, shared across projects |
| CI/CD pipelines | Custom bash scripts | GitHub Actions | Matrix testing, caching, secrets management, ecosystem integration |
| Type checking | Runtime type validation | mypy | Static analysis catches errors before runtime, no performance overhead |

**Key insight:** Python tooling ecosystem has matured significantly. Building custom solutions for these problems means maintaining code that handles Python's import system, virtual environments, platform differences, and edge cases that have taken years to stabilize in production tools.

## Common Pitfalls

### Pitfall 1: Installing Packages Globally
**What goes wrong:** Installing packages with `pip install` outside a virtual environment pollutes the global Python installation, causing version conflicts between projects and potentially breaking system tools.

**Why it happens:** Beginners often skip virtual environment setup to "get started faster."

**How to avoid:**
- Always use `uv` which automatically creates and manages virtual environments per project
- Run `uv init` to create project-specific environment
- Never use `sudo pip install` or global pip outside virtual environments

**Warning signs:**
- `pip list` shows dozens of unrelated packages
- Different projects break when updating dependencies
- ImportError appearing in unrelated projects

Source: [Python Virtual Environment Best Practices 2026](https://purpletutor.com/python-virtual-environment-best-practices/)

### Pitfall 2: Committing Virtual Environments and Cache Files
**What goes wrong:** Committing `.venv/`, `__pycache__/`, `*.pyc`, or `.pytest_cache/` to git bloats repository size, causes merge conflicts, and includes platform-specific binaries that don't work across systems.

**Why it happens:** Not setting up .gitignore before first commit, or using incomplete .gitignore templates.

**How to avoid:**
- Download official Python .gitignore: `curl https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore > .gitignore`
- Ensure .gitignore includes: `.venv/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.mypy_cache/`, `.coverage`, `uv.lock` should be committed but `.venv` must not
- If already committed: `git rm -r --cached .venv __pycache__`

**Warning signs:**
- Repository size growing rapidly
- Merge conflicts in .pyc files or .venv/
- Different developers getting import errors

Source: [Python .gitignore Best Practices](https://www.pythoncentral.io/python-gitignore-clean-repository-management/)

### Pitfall 3: Using Flat Layout Instead of Src Layout
**What goes wrong:** Placing package code in project root (flat layout) causes tests to import from local directory instead of installed package, masking import errors and packaging bugs until deployment.

**Why it happens:** Looks simpler initially, and many old tutorials show flat layout.

**How to avoid:**
- Always use `uv init --package` which creates src layout by default
- Place all importable code under `src/package_name/`
- Tests in top-level `tests/` directory should import from package name, not relative paths

**Warning signs:**
- Tests pass locally but package fails when installed
- Imports work in development but fail in production
- Missing files in built distributions

Source: [Python Packaging - src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)

### Pitfall 4: Not Pinning Python Version
**What goes wrong:** Different team members use different Python versions (3.11 vs 3.12), causing syntax errors, type checking differences, or behavior changes.

**Why it happens:** Assuming "Python 3 is Python 3" or not documenting required version.

**How to avoid:**
- Create `.python-version` file with exact version: `echo "3.12" > .python-version`
- Specify in pyproject.toml: `requires-python = ">=3.11"`
- Use `uv python install` to manage Python versions per project
- Document in README

**Warning signs:**
- CI fails with syntax errors that don't appear locally
- Type hints behave differently for different developers
- Feature works on one machine but not another

Source: [uv Documentation - Python Version Management](https://docs.astral.sh/uv/)

### Pitfall 5: Skipping Pre-commit Hook Installation
**What goes wrong:** Code quality checks only run in CI, meaning developers commit code that fails linting/formatting, then wait minutes for CI to report issues they could have caught in seconds.

**Why it happens:** Forgetting to run `pre-commit install` after cloning repository, or thinking CI checks are sufficient.

**How to avoid:**
- Add pre-commit setup to README: "After cloning, run `pre-commit install`"
- Include verification in onboarding: "Run `pre-commit run --all-files` to verify setup"
- Pre-commit hooks provide instant feedback before commit, CI is the safety net

**Warning signs:**
- Commits show "fix formatting" messages after initial commit
- CI frequently fails on linting when tests pass locally
- Pull requests require multiple rounds for style fixes

Source: [Pre-commit Documentation](https://pre-commit.com/)

### Pitfall 6: Not Committing Lock Files
**What goes wrong:** Without `uv.lock` in version control, different developers and CI get different dependency versions, causing "works on my machine" issues.

**Why it happens:** Misunderstanding that .lock files are "generated" and shouldn't be committed (true for node_modules, false for lockfiles).

**How to avoid:**
- **Always commit uv.lock** to version control
- Run `uv sync --locked` in CI to use exact versions from lockfile
- Update lock with `uv lock --upgrade` when updating dependencies
- Lock file ensures reproducible builds across all environments

**Warning signs:**
- Tests pass locally but fail in CI with dependency errors
- Different developers get different behavior from same code
- Production deployments behave differently than staging

Source: [Python Packaging Best Practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)

### Pitfall 7: Heavy __init__.py Files
**What goes wrong:** Placing substantial code in `__init__.py` slows imports, creates circular dependency risks, and makes module structure unclear.

**Why it happens:** Wanting to expose all module functionality at package level for convenience.

**How to avoid:**
- Keep `__init__.py` minimal - just `__version__` and essential `__all__` exports
- Put actual code in separate modules: `database.py`, `analyzer.py`, etc.
- Use explicit imports: `from .database import DatabaseConnection`
- Let users import from submodules: `from package.connection.database import DatabaseConnection`

**Warning signs:**
- Slow import times
- Circular import errors
- Difficulty understanding module structure

Source: [Structuring Your Project - Hitchhiker's Guide to Python](https://docs.python-guide.org/writing/structure/)

## Code Examples

Verified patterns from official sources:

### Complete Project Initialization
```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project with src layout
uv init --package automated-data-cataloger
cd automated-data-cataloger

# Pin Python version
echo "3.12" > .python-version
uv python install 3.12

# Add runtime dependencies
uv add pytest pytest-cov

# Add development dependencies
uv add --dev ruff mypy pre-commit

# Download Python .gitignore
curl https://raw.githubusercontent.com/github/gitignore/master/Python.gitignore > .gitignore

# Initialize pre-commit
uv run pre-commit install

# Run initial checks
uv run ruff check .
uv run mypy src/
uv run pytest
```
Source: [uv Official Documentation](https://docs.astral.sh/uv/guides/projects/)

### Running Tests with Coverage
```bash
# Run tests with coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html
```
Source: [pytest Documentation](https://docs.pytest.org/)

### Updating Dependencies
```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Update specific package
uv add --upgrade ruff

# Sync environment with lockfile
uv sync --locked
```
Source: [uv Documentation](https://docs.astral.sh/uv/)

### Running Quality Checks Locally
```bash
# Run all pre-commit hooks on all files
uv run pre-commit run --all-files

# Run just Ruff checks
uv run ruff check .

# Run Ruff with auto-fix
uv run ruff check --fix .

# Run Ruff formatter
uv run ruff format .

# Run type checking
uv run mypy src/
```
Source: [Ruff Documentation](https://docs.astral.sh/ruff/)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pip + requirements.txt | uv + pyproject.toml | 2024-2025 | 10-100x faster installs; unified tool; lockfile support; Python version management |
| setup.py for metadata | pyproject.toml [project] | 2020-2022 (PEP 517/518) | Declarative configuration; tool-agnostic; security improvements |
| Black + Flake8 + isort | Ruff (all-in-one) | 2023-2025 | 100x faster; single tool; consistent config; Black compatibility |
| pipenv or poetry | uv | 2024-2026 | Dramatically faster; broader scope (replaces more tools); Rust performance |
| unittest | pytest | 2015-2020 | Simpler syntax; better fixtures; rich ecosystem; auto-discovery |
| Manual git hooks | pre-commit framework | 2018-2023 | Cross-project consistency; automatic updates; multi-language support |

**Deprecated/outdated:**
- **setup.py for configuration:** Still works but pyproject.toml is standard for new projects per PEP 517/518
- **requirements.txt for dependency management:** Lacks dependency resolution and locking; use pyproject.toml + uv.lock
- **pipenv:** Abandoned by maintainers; slow performance; replaced by Poetry and now uv
- **setup.cfg:** Replaced by pyproject.toml for metadata and configuration
- **Flake8 + Black + isort separately:** Ruff replaces all three with single fast tool
- **actions/setup-python alone:** For uv projects, use astral-sh/setup-uv for better caching and speed

## Open Questions

1. **Should we use Python 3.11 or 3.12?**
   - What we know: Both supported by uv and modern tools; 3.12 has performance improvements
   - What's unclear: Whether Neo4j/OpenAI SDKs have any 3.12-specific issues
   - Recommendation: Start with 3.12 (current stable), test in CI matrix with both 3.11 and 3.12, document minimum as 3.11+ for compatibility

2. **Should we enforce 100% test coverage?**
   - What we know: pytest-cov can track and enforce coverage thresholds
   - What's unclear: Whether 100% coverage is practical for LLM integration code
   - Recommendation: Start with 80% coverage requirement, exclude LLM API calls from coverage (use mocks), increase threshold as project matures

3. **Should we use Pyright instead of mypy?**
   - What we know: Pyright is faster and has better IDE integration; mypy more established
   - What's unclear: Whether team prefers speed vs. stability
   - Recommendation: Start with mypy (more common in Python community), can switch to Pyright if type checking becomes slow

## Sources

### Primary (HIGH confidence)
- [uv Official Documentation](https://docs.astral.sh/uv/) - Project initialization, dependency management, GitHub Actions integration
- [Ruff Official Documentation](https://docs.astral.sh/ruff/) - Linting and formatting configuration
- [pytest Official Documentation](https://docs.pytest.org/) - Testing framework and fixtures
- [Python Packaging User Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - Official specification
- [Python Packaging User Guide - src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) - Official layout guidance
- [pre-commit Official Documentation](https://pre-commit.com/) - Hook framework configuration
- [astral-sh/ruff-pre-commit GitHub](https://github.com/astral-sh/ruff-pre-commit) - Official Ruff pre-commit integration
- [Poetry Official Documentation](https://python-poetry.org/docs/) - Alternative dependency manager

### Secondary (MEDIUM confidence)
- [Python Packaging Best Practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/) - uv vs Poetry comparison
- [Python Poetry vs uv Guide](https://devtoolbox.dedyn.io/blog/python-uv-packaging-guide) - Modern packaging tools comparison
- [GitHub Actions Complete CI/CD Guide](https://devtoolbox.dedyn.io/blog/github-actions-cicd-complete-guide) - CI/CD best practices
- [uv GitHub Actions Guide 2025](https://ber2.github.io/posts/2025_github_actions_python/) - Complete workflow examples
- [Python Virtual Environment Best Practices 2026](https://purpletutor.com/python-virtual-environment-best-practices/) - Common pitfalls
- [Python .gitignore Best Practices](https://www.pythoncentral.io/python-gitignore-clean-repository-management/) - Repository hygiene
- [Structuring Your Project - Hitchhiker's Guide](https://docs.python-guide.org/writing/structure/) - Project structure patterns
- [How to Structure Python Projects - Dagster](https://dagster.io/blog/python-project-best-practices) - Modular design principles

### Tertiary (LOW confidence)
- [Medium: Poetry vs UV 2025](https://medium.com/@hitorunajp/poetry-vs-uv-which-python-package-manager-should-you-use-in-2025-4212cb5e0a14) - Community perspectives
- [Medium: Python CI/CD Mastering](https://medium.com/hydroinformatics/the-ultimate-guide-to-python-ci-cd-mastering-github-actions-composite-actions-for-modern-python-0d7730c17b9e) - CI/CD patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation from Astral (uv, Ruff), Python.org (pytest, packaging), verified versions and features
- Architecture: HIGH - Official Python Packaging User Guide, multiple authoritative sources agree on src layout and pyproject.toml patterns
- Pitfalls: MEDIUM-HIGH - Mix of official documentation (virtual envs, .gitignore) and community best practices (pre-commit, coverage)

**Research date:** 2026-02-21
**Valid until:** 2026-04-21 (60 days - Python tooling relatively stable, but uv is fast-moving)

**Notes:**
- uv is rapidly evolving (released 2024, mature by 2026) - version numbers may change quickly but core concepts stable
- Ruff reached maturity and Black compatibility in 2025-2026 - safe for production use
- src layout and pyproject.toml are PEP-standardized - won't change
- GitHub Actions syntax stable - patterns applicable long-term
