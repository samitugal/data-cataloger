"""Catalog exporter for various output formats.

Provides export functionality for catalog data:
- JSON: Machine-readable, suitable for backup/restore
- YAML: Human-readable configuration format
- Markdown: Documentation generation
"""

import json
from datetime import UTC, datetime
from typing import Any

import yaml

from data_cataloger.storage.repository import GraphRepository


class CatalogExporter:
    """Export catalog data to various formats."""

    def __init__(self, repository: GraphRepository) -> None:
        """Initialize exporter with repository.

        Args:
            repository: GraphRepository instance for querying catalog data
        """
        self._repo = repository

    def export_json(self, database_name: str, pretty: bool = True) -> str:
        """Export catalog to JSON format.

        Args:
            database_name: Database to export
            pretty: Pretty print with indentation (default: True)

        Returns:
            JSON string of catalog data
        """
        data = self._build_export_data(database_name)
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)

    def export_yaml(self, database_name: str) -> str:
        """Export catalog to YAML format.

        Args:
            database_name: Database to export

        Returns:
            YAML string of catalog data
        """
        data = self._build_export_data(database_name)
        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    def export_markdown(self, database_name: str) -> str:
        """Export catalog to Markdown documentation.

        Args:
            database_name: Database to export

        Returns:
            Markdown string with full documentation
        """
        tables = self._repo.list_tables(database_name)
        graph = self._repo.get_full_graph(database_name)

        lines = [
            f"# Database Catalog: {database_name}",
            "",
            f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "## Overview",
            "",
            f"- **Total Tables:** {len(tables)}",
            f"- **Total Relationships:** {len(graph.get('edges', []))}",
            "",
            "### Sensitivity Distribution",
            "",
        ]

        sensitivity_counts: dict[str, int] = {}
        for table in tables:
            sens = table.sensitivity
            sensitivity_counts[sens] = sensitivity_counts.get(sens, 0) + 1

        for sens, count in sorted(sensitivity_counts.items()):
            lines.append(f"- **{sens}:** {count} tables")

        lines.extend(["", "---", "", "## Tables", ""])

        for table in sorted(tables, key=lambda t: t.table_name):
            relationships = self._repo.get_relationships(
                table.table_name, database_name
            )

            lines.extend([
                f"### {table.table_name}",
                "",
                f"**Sensitivity:** `{table.sensitivity}`",
                "",
                f"{table.description}",
                "",
            ])

            if relationships:
                lines.append("**Foreign Keys:**")
                lines.append("")
                for rel in relationships:
                    lines.append(
                        f"- `{rel['fk_column']}` → "
                        f"`{rel['referenced_table']}.{rel['referenced_column']}`"
                    )
                lines.append("")

            if table.example_queries:
                lines.append("**Example Queries:**")
                lines.append("")
                lines.append("```sql")
                for query in table.example_queries[:3]:
                    lines.append(query)
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

        lines.extend([
            "## Relationship Graph",
            "",
            "```mermaid",
            "graph LR",
        ])

        for edge in graph.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                lines.append(f"    {source} --> {target}")

        lines.extend(["```", ""])

        return "\n".join(lines)

    def _build_export_data(self, database_name: str) -> dict[str, Any]:
        """Build export data structure.

        Args:
            database_name: Database to export

        Returns:
            Dictionary with catalog data
        """
        tables = self._repo.list_tables(database_name)
        graph = self._repo.get_full_graph(database_name)

        table_data = []
        for table in tables:
            relationships = self._repo.get_relationships(
                table.table_name, database_name
            )
            table_data.append({
                "name": table.table_name,
                "description": table.description,
                "sensitivity": table.sensitivity,
                "example_queries": list(table.example_queries),
                "foreign_keys": relationships,
            })

        return {
            "version": "1.0",
            "exported_at": datetime.now(UTC).isoformat(),
            "database": database_name,
            "tables": table_data,
            "relationships": graph.get("edges", []),
            "metadata": {
                "table_count": len(tables),
                "relationship_count": len(graph.get("edges", [])),
            },
        }
