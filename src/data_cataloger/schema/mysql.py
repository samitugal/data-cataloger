"""MySQL/MariaDB schema extractor using INFORMATION_SCHEMA views.

Provides extraction methods for tables, columns, primary keys, and foreign keys
from MySQL and MariaDB databases using INFORMATION_SCHEMA system views.
"""

from data_cataloger.connection.base import DatabaseConnector
from data_cataloger.schema.models import ColumnMetadata, ForeignKeyMetadata


class MySQLExtractor:
    """MySQL/MariaDB schema extractor using INFORMATION_SCHEMA views.

    Extracts schema metadata from MySQL and MariaDB databases by querying
    INFORMATION_SCHEMA system views. Supports composite primary keys and
    foreign keys with proper ordinal position handling.

    Note: MySQL INFORMATION_SCHEMA column names are UPPERCASE (e.g., TABLE_NAME
    not table_name). Schema parameter represents the database name in MySQL
    (MySQL doesn't use PostgreSQL-style 'public' schema).
    """

    def get_tables(self, connector: DatabaseConnector, schema: str) -> list[str]:
        """Extract all base tables from MySQL database.

        Args:
            connector: Active database connector with open connection
            schema: Database name (MySQL uses database name as schema)

        Returns:
            List of table names, alphabetically sorted

        Note:
            Filters to BASE TABLE only, excluding views and system tables.
        """
        query = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = %s
              AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema,))
            return [row[0] for row in cur.fetchall()]

    def get_columns(
        self, connector: DatabaseConnector, table: str, schema: str
    ) -> list[ColumnMetadata]:
        """Extract column metadata for given table.

        Args:
            connector: Active database connector with open connection
            table: Table name to extract columns from
            schema: Database name (MySQL uses database name as schema)

        Returns:
            List of ColumnMetadata objects, ordered by ordinal_position

        Note:
            is_nullable string 'YES'/'NO' is converted to boolean True/False.
        """
        query = """
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                ORDINAL_POSITION,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
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
        self, connector: DatabaseConnector, table: str, schema: str
    ) -> list[str]:
        """Extract primary key column names for given table.

        Args:
            connector: Active database connector with open connection
            table: Table name to extract primary keys from
            schema: Database name (MySQL uses database name as schema)

        Returns:
            List of column names forming the primary key, in ordinal order.
            Empty list if table has no primary key.

        Note:
            MySQL uses CONSTRAINT_NAME = 'PRIMARY' to identify primary keys
            (not constraint_type='PRIMARY KEY' like PostgreSQL).
        """
        query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
              AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """
        with connector.connection.cursor() as cur:
            cur.execute(query, (schema, table))
            return [row[0] for row in cur.fetchall()]

    def get_foreign_keys(
        self, connector: DatabaseConnector, table: str, schema: str
    ) -> list[ForeignKeyMetadata]:
        """Extract foreign key constraints for given table.

        Args:
            connector: Active database connector with open connection
            table: Table name to extract foreign keys from
            schema: Database name (MySQL uses database name as schema)

        Returns:
            List of ForeignKeyMetadata objects. For composite foreign keys,
            multiple objects share the same constraint_name but have different
            column_name and ordinal_position values.

        Note:
            REFERENCED_TABLE_NAME IS NOT NULL filter is critical - it distinguishes
            foreign key constraints from primary key and unique constraints in
            KEY_COLUMN_USAGE view. Without this filter, PKs would appear as FKs.

            MySQL INFORMATION_SCHEMA is simpler than PostgreSQL - all FK metadata
            is in KEY_COLUMN_USAGE, no joins needed.
        """
        query = """
            SELECT
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME,
                ORDINAL_POSITION
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY CONSTRAINT_NAME, ORDINAL_POSITION
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
