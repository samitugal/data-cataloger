"""Catalog importer for restoring from exported data.

Imports catalog data from JSON/YAML format and writes to Neo4j.
"""

import json
from typing import Any

import yaml

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.storage.writer import Neo4jWriter


class CatalogImporter:
    """Import catalog data from various formats."""

    def __init__(self, writer: Neo4jWriter) -> None:
        """Initialize importer with writer.

        Args:
            writer: Neo4jWriter instance for writing catalog data
        """
        self._writer = writer

    def import_json(self, json_data: str) -> dict[str, Any]:
        """Import catalog from JSON string.

        Args:
            json_data: JSON string of catalog data

        Returns:
            Import summary with counts
        """
        data = json.loads(json_data)
        return self._import_data(data)

    def import_yaml(self, yaml_data: str) -> dict[str, Any]:
        """Import catalog from YAML string.

        Args:
            yaml_data: YAML string of catalog data

        Returns:
            Import summary with counts
        """
        data = yaml.safe_load(yaml_data)
        return self._import_data(data)

    def import_file(self, file_path: str) -> dict[str, Any]:
        """Import catalog from file (auto-detect format).

        Args:
            file_path: Path to JSON or YAML file

        Returns:
            Import summary with counts

        Raises:
            ValueError: If file format is not supported
        """
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if file_path.endswith(".json"):
            return self.import_json(content)
        elif file_path.endswith((".yaml", ".yml")):
            return self.import_yaml(content)
        else:
            raise ValueError(f"Unsupported file format: {file_path}")

    def _import_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Import catalog data structure.

        Args:
            data: Dictionary with catalog data

        Returns:
            Import summary
        """
        database_name = data.get("database", "imported")
        tables = data.get("tables", [])

        imported_tables = 0
        errors: list[str] = []

        for table_data in tables:
            try:
                entry = CatalogEntry(
                    table_name=table_data["name"],
                    description=table_data.get("description", ""),
                    sensitivity=table_data.get("sensitivity", "internal"),
                    example_queries=list(table_data.get("example_queries", [])),
                )

                self._writer.write_entry(entry, database_name)
                imported_tables += 1

            except Exception as e:
                errors.append(f"Failed to import {table_data.get('name')}: {e}")

        return {
            "success": len(errors) == 0,
            "database": database_name,
            "imported_tables": imported_tables,
            "errors": errors,
        }
