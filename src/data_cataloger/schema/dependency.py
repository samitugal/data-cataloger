"""Dependency graph for table processing order calculation.

This module provides a wrapper around Python's graphlib.TopologicalSorter
to calculate optimal table processing order based on foreign key dependencies.
"""

from graphlib import CycleError, TopologicalSorter


class DependencyGraph:
    """Table dependency graph with topological sorting.

    Builds a directed graph of table dependencies based on foreign key
    relationships and calculates processing order using topological sort.
    Independent tables (no foreign keys) appear first, followed by tables
    that depend on them.

    Handles self-referencing tables correctly (not treated as cycles).
    Detects circular dependencies and reports the tables forming the cycle.
    """

    def __init__(self) -> None:
        """Initialize empty dependency graph."""
        self._sorter: TopologicalSorter[str] = TopologicalSorter()
        self._tables_added: set[str] = set()

    def add_table(self, table: str, dependencies: list[str]) -> None:
        """Add table with its foreign key dependencies.

        Args:
            table: Name of the table to add
            dependencies: List of table names this table references via foreign keys.
                         Can be empty for independent tables.
                         Can include the same table name for self-referencing tables
                         (e.g., hierarchical structures).

        Example:
            graph.add_table("users", [])  # Independent table
            graph.add_table("orders", ["users"])  # Depends on users
            graph.add_table("categories", ["categories"])  # Self-referencing

        Note:
            Self-references are automatically filtered out before adding to the graph,
            as they don't represent true dependency cycles (hierarchical tables can
            always be processed independently).
        """
        # Filter out self-references - they're not true dependency cycles
        # (e.g., categories table with parent_id FK to itself can still be processed)
        filtered_deps = [dep for dep in dependencies if dep != table]
        self._sorter.add(table, *filtered_deps)
        self._tables_added.add(table)

    def get_processing_order(self) -> tuple[list[str], list[str] | None]:
        """Return table processing order.

        Returns:
            Tuple of (ordered_tables, cycle_nodes):
            - If successful: ordered_tables contains topologically sorted table names,
              cycle_nodes is None
            - If cycle detected: ordered_tables is empty list, cycle_nodes contains
              list of tables forming the cycle

        Example:
            ordered, cycle = graph.get_processing_order()
            if cycle:
                print(f"Circular dependency detected: {cycle}")
            else:
                print(f"Process tables in order: {ordered}")
        """
        try:
            ordered = list(self._sorter.static_order())
            return (ordered, None)
        except CycleError as e:
            # e.args[1] contains list of nodes forming the cycle
            cycle = e.args[1] if len(e.args) > 1 else []
            return ([], cycle)
