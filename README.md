# Data Cataloger

Automatically document legacy databases using LLM-powered analysis.

## Overview

Data Cataloger helps teams understand large, undocumented databases by using AI to infer table purposes, data sensitivity levels, and usage patterns. Instead of manually documenting hundreds of tables, the tool analyzes schema metadata and relationships to generate comprehensive catalog documentation.

## Key Features

- **Multi-database Support**: Works with PostgreSQL and MySQL databases
- **AI-Powered Analysis**: Uses LLM to infer table purposes and relationships
- **Graph Storage**: Stores catalog data in Neo4j to preserve table relationships
- **Web Visualization**: Interactive interface for browsing and searching catalog data
- **Intelligent Processing**: Analyzes independent tables first to provide context for dependent tables

## Requirements

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL or MySQL database (for cataloging)
- Neo4j database (for catalog storage)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd data-cataloger
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Configure database connections (details TBD)

## Quick Start

```bash
# Run the cataloger (implementation in progress)
uv run data-cataloger
```

## Project Structure

The project follows a modular architecture with five core modules:

- **connection/**: Database connection handling and credential management
- **schema/**: Schema extraction from PostgreSQL and MySQL databases
- **cataloging/**: LLM-powered analysis of table purposes and relationships
- **storage/**: Neo4j graph storage for catalog data
- **web/**: Web interface for catalog visualization and search

## Development

This project uses:
- Python 3.12 (pinned in `.python-version`)
- uv for dependency management
- src layout for clean package structure

## License

TBD
