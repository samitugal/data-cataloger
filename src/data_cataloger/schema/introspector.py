"""Schema introspector coordinator for database-agnostic extraction.

Orchestrates database-specific extractors and dependency graph building to
provide complete schema analysis in one call with table processing order.
"""

from dataclasses import dataclass

from data_cataloger.connection.base import DatabaseConnector
from data_cataloger.schema.dependency import DependencyGraph
from data_cataloger.schema.models import TableMetadata
from data_cataloger.schema.mysql import MySQLExtractor
from data_cataloger.schema.postgres import PostgreSQLExtractor


@dataclass
class SchemaAnalysisResult:
    """Complete schema analysis with processing order.

    Attributes:
        tables: List of TableMetadata for all tables in the schema
        processing_order: List of table names in dependency order (independent
            tables first, dependent tables after their dependencies). Empty list
            if circular dependency detected.
        circular_dependencies: List of table names forming a dependency cycle,
            or None if no cycles detected.
    """

    tables: list[TableMetadata]
    processing_order: list[str]
    circular_dependencies: list[str] | None


class SchemaIntrospector:
    """Coordinate schema extraction and dependency analysis.

    Provides a high-level API for extracting complete schema metadata with
    table processing order, abstracting database-specific extraction details.
    Routes to appropriate extractor based on database type and builds dependency
    graph from foreign key relationships.

    Example:
        >>> from data_cataloger.connection.postgres import PostgreSQLConnector
        >>> connector = PostgreSQLConnector(config)
        >>> connector.connect()
        >>> introspector = SchemaIntrospector()
        >>> result = introspector.introspect_schema(connector)
        >>> if result.circular_dependencies:
        ...     print(f"Circular dependency: {result.circular_dependencies}")
        ... else:
        ...     for table in result.processing_order:
        ...         print(f"Process table: {table}")
    """

    def introspect_schema(
        self, connector: DatabaseConnector, schema: str | None = None
    ) -> SchemaAnalysisResult:
        """Extract complete schema metadata with processing order.

        Args:
            connector: Active database connector with open connection
            schema: Schema/database name to extract. If None, uses default:
                - PostgreSQL: 'public'
                - MySQL: database from connector config

        Returns:
            SchemaAnalysisResult with tables metadata, processing order, and
            optional circular dependency information

        Raises:
            ValueError: If connector database type is unsupported
            AttributeError: If connector doesn't have expected config attributes
        """
        # Route to correct extractor based on database type
        # Access connector.config.db_type - this relies on connectors having
        # a config attribute, which both PostgreSQLConnector and MySQLConnector do
        db_type = connector.config.db_type  # type: ignore[attr-defined]

        if db_type == "postgresql":
            extractor: PostgreSQLExtractor | MySQLExtractor = PostgreSQLExtractor()
            effective_schema = schema or "public"
        elif db_type == "mysql":
            extractor = MySQLExtractor()
            # For MySQL, use database name from config if schema not provided
            if schema is None:
                effective_schema = connector.config.database  # type: ignore[attr-defined]
            else:
                effective_schema = schema
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Extract tables
        tables = extractor.get_tables(connector, effective_schema)

        # Build TableMetadata for each table
        tables_metadata: list[TableMetadata] = []
        graph = DependencyGraph()

        for table in tables:
            # Extract metadata for this table
            columns = extractor.get_columns(connector, table, effective_schema)
            primary_keys = extractor.get_primary_keys(
                connector, table, effective_schema
            )
            foreign_keys = extractor.get_foreign_keys(
                connector, table, effective_schema
            )

            # Create TableMetadata
            table_meta = TableMetadata(
                schema_name=effective_schema,
                table_name=table,
                columns=tuple(columns),
                primary_keys=tuple(primary_keys),
                foreign_keys=tuple(foreign_keys),
            )
            tables_metadata.append(table_meta)

            # Extract unique referenced tables from foreign keys
            referenced_tables = list({fk.referenced_table for fk in foreign_keys})

            # Add to dependency graph
            graph.add_table(table, referenced_tables)

        # Get processing order
        processing_order, circular_deps = graph.get_processing_order()

        return SchemaAnalysisResult(
            tables=tables_metadata,
            processing_order=processing_order,
            circular_dependencies=circular_deps,
        )
