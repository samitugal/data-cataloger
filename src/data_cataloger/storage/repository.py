"""GraphRepository for querying catalog data from Neo4j.

Provides read-only access to the catalog knowledge graph with methods that return
existing domain objects (CatalogEntry). Encapsulates all Cypher queries behind
clean Python methods for Phase 6 Web Interface consumption.

All query methods use parameterized Cypher to prevent injection attacks and
always specify the database_ parameter to avoid extra round-trips.
"""

from neo4j import Driver, Record

from data_cataloger.cataloging.models import CatalogEntry


class GraphRepository:
    """Read-only repository for querying catalog graph.

    Provides methods to retrieve catalog entries, relationships, and search
    functionality. All methods return domain objects (CatalogEntry) or
    simple dicts, never graph-specific DTOs.

    Attributes:
        _driver: Neo4j driver instance for executing queries
        _database: Database name to query (default "neo4j")
    """

    def __init__(self, driver: Driver, database: str = "neo4j") -> None:
        """Initialize GraphRepository with Neo4j driver.

        Args:
            driver: Neo4j driver instance (already connected and verified)
            database: Neo4j database name (default "neo4j")
        """
        self._driver = driver
        self._database = database

    def list_databases(self) -> list[dict[str, str]]:
        """List all cataloged databases via MetadataRepository.

        Returns:
            List of dicts with keys: name, type, created_at, table_count
        """
        query = """
        MATCH (repo:MetadataRepository)-[:CONTAINS_DATABASE]->(db:Database)
        OPTIONAL MATCH (db)-[:HAS_TABLE]->(t:Table)
        WHERE t.description IS NOT NULL
        RETURN db.name AS name,
               db.type AS type,
               db.created_at AS created_at,
               count(t) AS table_count
        ORDER BY db.name
        """
        records, _, _ = self._driver.execute_query(
            query,
            database_=self._database,
        )

        return [
            {
                "name": record["name"],
                "type": record["type"],
                "created_at": record["created_at"],
                "table_count": record["table_count"],
            }
            for record in records
        ]

    def database_exists(self, database_name: str) -> bool:
        """Check if a database has been cataloged.

        Args:
            database_name: Name of the database to check

        Returns:
            True if database exists and has at least one cataloged table
        """
        query = """
        MATCH (db:Database {name: $database_name})-[:HAS_TABLE]->(t:Table)
        WHERE t.description IS NOT NULL
        RETURN count(t) > 0 AS exists
        """
        records, _, _ = self._driver.execute_query(
            query,
            database_name=database_name,
            database_=self._database,
        )

        if not records:
            return False
        return records[0]["exists"]

    def get_table(self, table_name: str, database_name: str) -> CatalogEntry | None:
        """Retrieve catalog entry for a specific table.

        Args:
            table_name: Name of the table to retrieve
            database_name: Database the table belongs to

        Returns:
            CatalogEntry if table exists and is cataloged, None otherwise.
            Returns None for stub nodes (created for FK references but not
            yet cataloged - they have no description).
        """
        query = """
        MATCH (t:Table {name: $table_name, database: $database_name})
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               t.example_queries AS example_queries
        """
        records, _, _ = self._driver.execute_query(
            query,
            table_name=table_name,
            database_name=database_name,
            database_=self._database,
        )

        if not records:
            return None

        return self._to_catalog_entry(records[0])

    def list_tables(self, database_name: str) -> list[CatalogEntry]:
        """List all cataloged tables in a database.

        Filters out stub nodes (created for FK references but not yet cataloged).
        Stub nodes have no description property, so we filter by WHERE
        t.description IS NOT NULL.

        Args:
            database_name: Database to list tables from

        Returns:
            List of catalog entries sorted by table name. Empty list if
            no cataloged tables exist.
        """
        query = """
        MATCH (t:Table {database: $database_name})
        WHERE t.description IS NOT NULL
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               t.example_queries AS example_queries
        ORDER BY t.name
        """
        records, _, _ = self._driver.execute_query(
            query,
            database_name=database_name,
            database_=self._database,
        )

        return [self._to_catalog_entry(record) for record in records]

    def get_relationships(
        self, table_name: str, database_name: str
    ) -> list[dict[str, str]]:
        """Get direct foreign key relationships for a table.

        Returns only immediate FK connections (no multi-hop traversal).
        Each relationship includes the referenced table name and FK metadata.

        Args:
            table_name: Name of the source table
            database_name: Database the table belongs to

        Returns:
            List of dicts with keys:
            - referenced_table: Name of the referenced table
            - fk_column: Foreign key column name
            - referenced_column: Referenced column name
            - constraint_name: FK constraint name

            Empty list if table has no foreign key relationships.
        """
        query = """
        MATCH (source:Table {name: $table_name, database: $database_name})
              -[r:REFERENCES_VIA]->(target:Table)
        RETURN target.name AS referenced_table,
               r.fk_column AS fk_column,
               r.referenced_column AS referenced_column,
               r.constraint_name AS constraint_name
        """
        records, _, _ = self._driver.execute_query(
            query,
            table_name=table_name,
            database_name=database_name,
            database_=self._database,
        )

        # Materialize records to list of dicts before returning
        return [dict(record) for record in records]

    def get_full_graph(self, database_name: str) -> dict[str, list[dict[str, str]]]:
        """Get full graph (all nodes and edges) for a database.

        Returns both nodes and edges for visualization purposes. Executes
        two separate queries (simpler than complex Cypher WITH/collect which
        can have subtle bugs).

        Args:
            database_name: Database to retrieve graph for

        Returns:
            Dict with two keys:
            - "nodes": List of dicts with table metadata
              (name, description, sensitivity)
            - "edges": List of dicts with relationship metadata
              (source, target, FK info)

            Both lists may be empty if database has no cataloged tables.
        """
        # Query 1: Get all table nodes
        nodes_query = """
        MATCH (t:Table {database: $database_name})
        WHERE t.description IS NOT NULL
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity
        """
        node_records, _, _ = self._driver.execute_query(
            nodes_query,
            database_name=database_name,
            database_=self._database,
        )

        # Query 2: Get all relationships
        edges_query = """
        MATCH (source:Table {database: $database_name})
              -[r:REFERENCES_VIA]->(target:Table)
        RETURN source.name AS source,
               target.name AS target,
               r.fk_column AS fk_column,
               r.referenced_column AS referenced_column
        """
        edge_records, _, _ = self._driver.execute_query(
            edges_query,
            database_name=database_name,
            database_=self._database,
        )

        # Materialize both result sets to lists of dicts
        return {
            "nodes": [dict(record) for record in node_records],
            "edges": [dict(record) for record in edge_records],
        }

    def search_by_sensitivity(
        self, sensitivity: str, database_name: str
    ) -> list[CatalogEntry]:
        """Search tables by sensitivity classification.

        Args:
            sensitivity: Sensitivity level to search for (e.g., "PII", "financial")
            database_name: Database to search in

        Returns:
            List of catalog entries with matching sensitivity, sorted by name.
            Empty list if no matches found.
        """
        query = """
        MATCH (t:Table {database: $database_name})
        WHERE t.sensitivity = $sensitivity
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               t.example_queries AS example_queries
        ORDER BY t.name
        """
        records, _, _ = self._driver.execute_query(
            query,
            sensitivity=sensitivity,
            database_name=database_name,
            database_=self._database,
        )

        return [self._to_catalog_entry(record) for record in records]

    def search_by_keyword(self, keyword: str, database_name: str) -> list[CatalogEntry]:
        """Search tables by keyword in descriptions.

        Case-insensitive search using Neo4j toLower() function. Matches
        partial words (CONTAINS operator).

        Args:
            keyword: Keyword to search for in table descriptions
            database_name: Database to search in

        Returns:
            List of catalog entries with matching descriptions, sorted by name.
            Empty list if no matches found.
        """
        query = """
        MATCH (t:Table {database: $database_name})
        WHERE toLower(t.description) CONTAINS toLower($keyword)
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               t.example_queries AS example_queries
        ORDER BY t.name
        """
        records, _, _ = self._driver.execute_query(
            query,
            keyword=keyword,
            database_name=database_name,
            database_=self._database,
        )

        return [self._to_catalog_entry(record) for record in records]

    def semantic_search(
        self,
        query_embedding: list[float],
        database_name: str,
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[dict[str, object]]:
        """Search tables by semantic similarity using vector embeddings.

        Uses Neo4j's vector similarity function to find tables with descriptions
        semantically similar to the query embedding.

        Args:
            query_embedding: Query vector (1536 dimensions from OpenAI)
            database_name: Database to search in
            limit: Maximum number of results (default: 5)
            threshold: Minimum similarity score (default: 0.7)

        Returns:
            List of dicts with keys:
            - name: Table name
            - description: Table description
            - sensitivity: Sensitivity classification
            - similarity: Cosine similarity score (0-1)

            Sorted by similarity descending. Empty list if no matches.
        """
        query = """
        MATCH (t:Table {database: $database_name})
        WHERE t.embedding IS NOT NULL AND t.description IS NOT NULL
        WITH t, vector.similarity.cosine(t.embedding, $query_embedding) AS score
        WHERE score >= $threshold
        RETURN t.name AS name,
               t.description AS description,
               t.sensitivity AS sensitivity,
               score AS similarity
        ORDER BY score DESC
        LIMIT $limit
        """
        records, _, _ = self._driver.execute_query(
            query,
            query_embedding=query_embedding,
            database_name=database_name,
            threshold=threshold,
            limit=limit,
            database_=self._database,
        )

        return [dict(record) for record in records]

    def _to_catalog_entry(self, record: Record) -> CatalogEntry:
        """Convert Neo4j record to CatalogEntry domain object.

        Extracts record-to-CatalogEntry extraction to avoid code duplication
        across query methods.

        Args:
            record: Neo4j Record object with table properties

        Returns:
            CatalogEntry constructed from record fields
        """
        example_queries = record["example_queries"]
        if example_queries is None:
            example_queries = []

        return CatalogEntry(
            table_name=record["name"],
            description=record["description"],
            sensitivity=record["sensitivity"],
            example_queries=example_queries,
        )
