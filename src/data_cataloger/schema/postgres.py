"""PostgreSQL schema extractor using information_schema views.

Provides methods to extract tables, columns, primary keys, and foreign keys
from PostgreSQL databases using standard information_schema views.
"""

from data_cataloger.connection.base import DatabaseConnector
from data_cataloger.schema.models import ColumnMetadata, ForeignKeyMetadata


class PostgreSQLExtractor:
    """PostgreSQL schema extractor using information_schema views.

    Extracts schema metadata from PostgreSQL databases by querying the
    information_schema views. All queries use parameterized placeholders
    to prevent SQL injection.

    Example:
        >>> from data_cataloger.connection.postgres import PostgreSQLConnector
        >>> connector = PostgreSQLConnector(config)
        >>> connector.connect()
        >>> extractor = PostgreSQLExtractor()
        >>> tables = extractor.get_tables(connector)
        >>> columns = extractor.get_columns(connector, 'users')
    """

    def get_tables(
        self, connector: DatabaseConnector, schema: str = "public"
    ) -> list[str]:
        """Extract all base tables from PostgreSQL database.

        Args:
            connector: Active database connection
            schema: Schema name to query (default: 'public')

        Returns:
            List of table names sorted alphabetically

        Note:
            Filters to BASE TABLE only, excluding views and system tables
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema,))
            return [row[0] for row in cur.fetchall()]

    def get_columns(
        self, connector: DatabaseConnector, table: str, schema: str = "public"
    ) -> list[ColumnMetadata]:
        """Extract column metadata for given table.

        Args:
            connector: Active database connection
            table: Table name to query
            schema: Schema name (default: 'public')

        Returns:
            List of ColumnMetadata objects ordered by ordinal_position

        Note:
            Converts is_nullable string ('YES'/'NO') to boolean
        """
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                ordinal_position,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            ORDER BY ordinal_position
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema, table))
            return [
                ColumnMetadata(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=(row[2] == "YES"),
                    ordinal_position=row[3],
                    column_default=row[4],
                )
                for row in cur.fetchall()
            ]

    def get_primary_keys(
        self, connector: DatabaseConnector, table: str, schema: str = "public"
    ) -> list[str]:
        """Extract primary key column names for given table.

        Args:
            connector: Active database connection
            table: Table name to query
            schema: Schema name (default: 'public')

        Returns:
            List of column names forming the primary key, ordered by
            ordinal_position. Empty list if table has no primary key.

        Note:
            For composite primary keys, maintains column order via
            ordinal_position sort
        """
        query = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.constraint_schema = kcu.constraint_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema, table))
            return [row[0] for row in cur.fetchall()]

    def get_foreign_keys(
        self, connector: DatabaseConnector, table: str, schema: str = "public"
    ) -> list[ForeignKeyMetadata]:
        """Extract foreign key constraints for given table.

        Args:
            connector: Active database connection
            table: Table name to query
            schema: Schema name (default: 'public')

        Returns:
            List of ForeignKeyMetadata objects. For composite foreign keys,
            multiple objects share the same constraint_name but different
            column_name and ordinal_position values. Includes self-referencing
            foreign keys (hierarchical tables).

        Note:
            Ordered by constraint_name and ordinal_position to properly
            group composite foreign keys
        """
        query = """
            SELECT
                kcu.constraint_name,
                kcu.column_name,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column,
                kcu.ordinal_position
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc
              ON kcu.constraint_name = rc.constraint_name
             AND kcu.constraint_schema = rc.constraint_schema
            JOIN information_schema.key_column_usage ccu
              ON rc.unique_constraint_name = ccu.constraint_name
             AND rc.unique_constraint_schema = ccu.constraint_schema
             AND kcu.ordinal_position = ccu.ordinal_position
            WHERE kcu.table_schema = %s
              AND kcu.table_name = %s
            ORDER BY kcu.constraint_name, kcu.ordinal_position
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema, table))
            return [
                ForeignKeyMetadata(
                    constraint_name=row[0],
                    column_name=row[1],
                    referenced_table=row[2],
                    referenced_column=row[3],
                    ordinal_position=row[4],
                )
                for row in cur.fetchall()
            ]
