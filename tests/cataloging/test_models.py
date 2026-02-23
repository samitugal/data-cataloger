"""Tests for catalog data models.

Validates Pydantic schema enforcement, dataclass immutability, and state
management including parent context extraction.
"""

import pytest
from pydantic import ValidationError

from data_cataloger.cataloging.models import CatalogEntry, CatalogState, TableCatalog
from data_cataloger.schema.models import ForeignKeyMetadata, TableMetadata


class TestTableCatalogPydanticValidation:
    """Test Pydantic validation for TableCatalog model."""

    def test_valid_table_catalog(self) -> None:
        """TableCatalog accepts valid data with all required fields."""
        catalog = TableCatalog(
            description="Stores customer account information",
            sensitivity="PII",
            example_queries=[
                "SELECT * FROM users WHERE email = 'test@example.com'",
                "SELECT id, name FROM users WHERE created_at > '2024-01-01'",
            ],
        )

        assert catalog.description == "Stores customer account information"
        assert catalog.sensitivity == "PII"
        assert len(catalog.example_queries) == 2

    def test_all_valid_sensitivity_values(self) -> None:
        """TableCatalog accepts all defined sensitivity classifications."""
        valid_sensitivities = ["PII", "financial", "public", "internal"]

        for sensitivity in valid_sensitivities:
            catalog = TableCatalog(
                description="Test table",
                sensitivity=sensitivity,  # type: ignore[arg-type]
                example_queries=["SELECT * FROM test"],
            )
            assert catalog.sensitivity == sensitivity

    def test_invalid_sensitivity_raises_validation_error(self) -> None:
        """TableCatalog rejects sensitivity values not in Literal definition."""
        with pytest.raises(ValidationError) as exc_info:
            TableCatalog(
                description="Test table",
                sensitivity="confidential",  # type: ignore[arg-type]
                example_queries=["SELECT * FROM test"],
            )

        # Verify error mentions the invalid value
        error_str = str(exc_info.value)
        assert "sensitivity" in error_str.lower()

    def test_missing_required_fields_raises_validation_error(self) -> None:
        """TableCatalog requires all fields to be provided."""
        # Missing description
        with pytest.raises(ValidationError) as exc_info:
            TableCatalog(  # type: ignore[call-arg]
                sensitivity="public",
                example_queries=["SELECT * FROM test"],
            )
        assert "description" in str(exc_info.value).lower()

        # Missing sensitivity
        with pytest.raises(ValidationError) as exc_info:
            TableCatalog(  # type: ignore[call-arg]
                description="Test",
                example_queries=["SELECT * FROM test"],
            )
        assert "sensitivity" in str(exc_info.value).lower()

        # Missing example_queries
        with pytest.raises(ValidationError) as exc_info:
            TableCatalog(  # type: ignore[call-arg]
                description="Test",
                sensitivity="public",
            )
        assert "example_queries" in str(exc_info.value).lower()

    def test_extra_fields_allowed(self) -> None:
        """TableCatalog allows extra fields (Pydantic default behavior)."""
        catalog = TableCatalog(
            description="Test table",
            sensitivity="public",
            example_queries=["SELECT * FROM test"],
            extra_field="ignored",  # type: ignore[call-arg]
        )

        assert catalog.description == "Test table"
        # Extra field is not stored in model
        assert not hasattr(catalog, "extra_field")


class TestCatalogEntryImmutability:
    """Test immutability of CatalogEntry frozen dataclass."""

    def test_catalog_entry_creation(self) -> None:
        """CatalogEntry can be created with all fields."""
        entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users WHERE id = 1"],
        )

        assert entry.table_name == "users"
        assert entry.description == "Customer accounts"
        assert entry.sensitivity == "PII"
        assert len(entry.example_queries) == 1

    def test_catalog_entry_is_frozen(self) -> None:
        """CatalogEntry fields cannot be modified after creation."""
        entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )

        # Attempting to modify frozen dataclass raises FrozenInstanceError
        with pytest.raises(Exception) as exc_info:  # FrozenInstanceError is subclass
            entry.description = "Modified description"  # type: ignore[misc]

        assert "frozen" in str(type(exc_info.value)).lower()


class TestCatalogStateAddEntry:
    """Test CatalogState.add_entry method."""

    def test_add_single_entry(self) -> None:
        """add_entry adds entry to state registry."""
        state = CatalogState()
        entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )

        state.add_entry(entry)

        assert "users" in state.entries
        assert state.entries["users"] == entry

    def test_add_multiple_entries(self) -> None:
        """add_entry can add multiple different entries."""
        state = CatalogState()

        users_entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )
        orders_entry = CatalogEntry(
            table_name="orders",
            description="Customer orders",
            sensitivity="financial",
            example_queries=["SELECT * FROM orders"],
        )

        state.add_entry(users_entry)
        state.add_entry(orders_entry)

        assert len(state.entries) == 2
        assert state.entries["users"] == users_entry
        assert state.entries["orders"] == orders_entry

    def test_overwriting_entry_replaces_old(self) -> None:
        """add_entry replaces existing entry with same table_name."""
        state = CatalogState()

        original_entry = CatalogEntry(
            table_name="users",
            description="Original description",
            sensitivity="public",
            example_queries=["SELECT * FROM users"],
        )
        updated_entry = CatalogEntry(
            table_name="users",
            description="Updated description",
            sensitivity="PII",
            example_queries=["SELECT id, email FROM users"],
        )

        state.add_entry(original_entry)
        state.add_entry(updated_entry)

        assert len(state.entries) == 1
        assert state.entries["users"].description == "Updated description"
        assert state.entries["users"].sensitivity == "PII"


class TestCatalogStateGetParentContext:
    """Test CatalogState.get_parent_context method."""

    def test_table_with_no_foreign_keys_returns_empty_list(self) -> None:
        """get_parent_context returns empty list for tables without FKs."""
        state = CatalogState()

        # Create table with no foreign keys
        table = TableMetadata(
            schema_name="public",
            table_name="users",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(),
        )

        result = state.get_parent_context(table)
        assert result == []

    def test_table_with_fk_to_cataloged_parent_returns_parent(self) -> None:
        """get_parent_context returns parent entry when it exists in state."""
        state = CatalogState()

        # Add parent table to state
        users_entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )
        state.add_entry(users_entry)

        # Create child table with FK to users
        orders_table = TableMetadata(
            schema_name="public",
            table_name="orders",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(
                ForeignKeyMetadata(
                    constraint_name="fk_orders_user_id",
                    column_name="user_id",
                    referenced_table="users",
                    referenced_column="id",
                    ordinal_position=1,
                ),
            ),
        )

        result = state.get_parent_context(orders_table)

        assert len(result) == 1
        assert result[0] == users_entry

    def test_table_with_fk_to_uncataloged_parent_returns_empty_list(self) -> None:
        """get_parent_context returns empty list when parent not yet cataloged."""
        state = CatalogState()

        # Create child table with FK to uncataloged parent
        orders_table = TableMetadata(
            schema_name="public",
            table_name="orders",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(
                ForeignKeyMetadata(
                    constraint_name="fk_orders_user_id",
                    column_name="user_id",
                    referenced_table="users",
                    referenced_column="id",
                    ordinal_position=1,
                ),
            ),
        )

        result = state.get_parent_context(orders_table)
        assert result == []

    def test_table_with_multiple_fks_returns_all_cataloged_parents(self) -> None:
        """get_parent_context returns all parent entries that exist in state."""
        state = CatalogState()

        # Add two parent tables
        users_entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )
        products_entry = CatalogEntry(
            table_name="products",
            description="Product catalog",
            sensitivity="public",
            example_queries=["SELECT * FROM products"],
        )
        state.add_entry(users_entry)
        state.add_entry(products_entry)

        # Create table with FKs to both parents and one uncataloged parent
        order_items_table = TableMetadata(
            schema_name="public",
            table_name="order_items",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(
                ForeignKeyMetadata(
                    constraint_name="fk_order_items_user_id",
                    column_name="user_id",
                    referenced_table="users",
                    referenced_column="id",
                    ordinal_position=1,
                ),
                ForeignKeyMetadata(
                    constraint_name="fk_order_items_product_id",
                    column_name="product_id",
                    referenced_table="products",
                    referenced_column="id",
                    ordinal_position=1,
                ),
                ForeignKeyMetadata(
                    constraint_name="fk_order_items_warehouse_id",
                    column_name="warehouse_id",
                    referenced_table="warehouses",
                    referenced_column="id",
                    ordinal_position=1,
                ),
            ),
        )

        result = state.get_parent_context(order_items_table)

        # Should return only the two cataloged parents, not warehouses
        assert len(result) == 2
        assert users_entry in result
        assert products_entry in result


class TestCatalogStateGetParentContextDeduplication:
    """Test parent context deduplication for composite foreign keys."""

    def test_composite_fk_returns_single_parent_entry(self) -> None:
        """get_parent_context deduplicates parent when composite FK references it."""
        state = CatalogState()

        # Add parent table
        users_entry = CatalogEntry(
            table_name="users",
            description="Customer accounts",
            sensitivity="PII",
            example_queries=["SELECT * FROM users"],
        )
        state.add_entry(users_entry)

        # Create table with composite FK (multiple columns referencing same parent)
        user_sessions_table = TableMetadata(
            schema_name="public",
            table_name="user_sessions",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(
                ForeignKeyMetadata(
                    constraint_name="fk_sessions_user",
                    column_name="user_id",
                    referenced_table="users",
                    referenced_column="id",
                    ordinal_position=1,
                ),
                ForeignKeyMetadata(
                    constraint_name="fk_sessions_user",
                    column_name="tenant_id",
                    referenced_table="users",
                    referenced_column="tenant_id",
                    ordinal_position=2,
                ),
            ),
        )

        result = state.get_parent_context(user_sessions_table)

        # Should return users only once despite two FK columns
        assert len(result) == 1
        assert result[0] == users_entry

    def test_self_reference_filtered_out(self) -> None:
        """get_parent_context filters out self-referencing foreign keys."""
        state = CatalogState()

        # Add hierarchical table to state
        categories_entry = CatalogEntry(
            table_name="categories",
            description="Product categories",
            sensitivity="public",
            example_queries=["SELECT * FROM categories"],
        )
        state.add_entry(categories_entry)

        # Create table with self-referencing FK
        categories_table = TableMetadata(
            schema_name="public",
            table_name="categories",
            columns=(),
            primary_keys=("id",),
            foreign_keys=(
                ForeignKeyMetadata(
                    constraint_name="fk_categories_parent",
                    column_name="parent_id",
                    referenced_table="categories",
                    referenced_column="id",
                    ordinal_position=1,
                ),
            ),
        )

        result = state.get_parent_context(categories_table)

        # Should not return self-reference
        assert result == []
