"""Tests for prompt templates and builder functions.

Validates that prompts include all required metadata and parent context.
"""

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.cataloging.prompts import SYSTEM_PROMPT, build_user_prompt
from data_cataloger.schema.models import (
    ColumnMetadata,
    ForeignKeyMetadata,
    TableMetadata,
)


def test_system_prompt_exists() -> None:
    """SYSTEM_PROMPT should be non-empty and mention all sensitivity types."""
    assert SYSTEM_PROMPT
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 50

    # Verify all sensitivity types are documented
    assert "PII" in SYSTEM_PROMPT
    assert "financial" in SYSTEM_PROMPT
    assert "public" in SYSTEM_PROMPT
    assert "internal" in SYSTEM_PROMPT

    # Verify it mentions relationships
    assert "foreign key" in SYSTEM_PROMPT.lower()


def test_build_user_prompt_basic_table() -> None:
    """build_user_prompt should include table name and columns."""
    table = TableMetadata(
        schema_name="public",
        table_name="products",
        columns=(
            ColumnMetadata(
                name="id", data_type="integer", is_nullable=False, ordinal_position=1
            ),
            ColumnMetadata(
                name="name",
                data_type="varchar(255)",
                is_nullable=False,
                ordinal_position=2,
            ),
            ColumnMetadata(
                name="description",
                data_type="text",
                is_nullable=True,
                ordinal_position=3,
            ),
        ),
        primary_keys=(),
        foreign_keys=(),
    )

    prompt = build_user_prompt(table, [])

    # Verify table name present
    assert "Table: products" in prompt

    # Verify all columns listed with data types
    assert "id (integer)" in prompt
    assert "name (varchar(255))" in prompt
    assert "description (text)" in prompt

    # Verify no PK or FK sections (table has none)
    assert "Primary Key:" not in prompt
    assert "Foreign Keys:" not in prompt
    assert "Referenced Tables Context:" not in prompt


def test_build_user_prompt_with_primary_key() -> None:
    """build_user_prompt should include primary key section when present."""
    table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(
            ColumnMetadata(
                name="id", data_type="integer", is_nullable=False, ordinal_position=1
            ),
        ),
        primary_keys=("id",),
        foreign_keys=(),
    )

    prompt = build_user_prompt(table, [])

    assert "Primary Key: id" in prompt


def test_build_user_prompt_with_foreign_keys() -> None:
    """build_user_prompt should list all foreign key relationships."""
    table = TableMetadata(
        schema_name="public",
        table_name="orders",
        columns=(
            ColumnMetadata(
                name="id", data_type="integer", is_nullable=False, ordinal_position=1
            ),
            ColumnMetadata(
                name="user_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=2,
            ),
            ColumnMetadata(
                name="product_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=3,
            ),
        ),
        primary_keys=("id",),
        foreign_keys=(
            ForeignKeyMetadata(
                constraint_name="fk_orders_users",
                column_name="user_id",
                referenced_table="users",
                referenced_column="id",
                ordinal_position=1,
            ),
            ForeignKeyMetadata(
                constraint_name="fk_orders_products",
                column_name="product_id",
                referenced_table="products",
                referenced_column="id",
                ordinal_position=1,
            ),
        ),
    )

    prompt = build_user_prompt(table, [])

    # Verify FK section present
    assert "Foreign Keys:" in prompt

    # Verify both FKs listed correctly
    assert "user_id -> users.id" in prompt
    assert "product_id -> products.id" in prompt


def test_build_user_prompt_with_parent_context() -> None:
    """build_user_prompt should include parent table descriptions."""
    # Create parent catalog entry
    users_entry = CatalogEntry(
        table_name="users",
        description="User account information",
        sensitivity="PII",
        example_queries=["SELECT * FROM users WHERE email = ?"],
    )

    # Create child table with FK to users
    table = TableMetadata(
        schema_name="public",
        table_name="orders",
        columns=(
            ColumnMetadata(
                name="id", data_type="integer", is_nullable=False, ordinal_position=1
            ),
            ColumnMetadata(
                name="user_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=2,
            ),
        ),
        primary_keys=("id",),
        foreign_keys=(
            ForeignKeyMetadata(
                constraint_name="fk_orders_users",
                column_name="user_id",
                referenced_table="users",
                referenced_column="id",
                ordinal_position=1,
            ),
        ),
    )

    prompt = build_user_prompt(table, [users_entry])

    # Verify parent context section present
    assert "Referenced Tables Context:" in prompt

    # Verify parent description included
    assert "users: User account information" in prompt


def test_build_user_prompt_nullable_columns() -> None:
    """build_user_prompt should indicate NOT NULL for non-nullable columns."""
    table = TableMetadata(
        schema_name="public",
        table_name="products",
        columns=(
            ColumnMetadata(
                name="id",
                data_type="integer",
                is_nullable=False,  # NOT NULL
                ordinal_position=1,
            ),
            ColumnMetadata(
                name="description",
                data_type="text",
                is_nullable=True,  # Nullable
                ordinal_position=2,
            ),
        ),
        primary_keys=(),
        foreign_keys=(),
    )

    prompt = build_user_prompt(table, [])

    # Non-nullable column should have NOT NULL indicator
    assert "id (integer) NOT NULL" in prompt

    # Nullable column should NOT have NOT NULL indicator
    assert "description (text)" in prompt
    assert "description (text) NOT NULL" not in prompt


def test_build_user_prompt_composite_foreign_key() -> None:
    """build_user_prompt should list all columns in composite foreign keys."""
    table = TableMetadata(
        schema_name="public",
        table_name="order_items",
        columns=(
            ColumnMetadata(
                name="order_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=1,
            ),
            ColumnMetadata(
                name="product_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=2,
            ),
        ),
        primary_keys=("order_id", "product_id"),
        foreign_keys=(
            ForeignKeyMetadata(
                constraint_name="fk_composite",
                column_name="order_id",
                referenced_table="orders",
                referenced_column="id",
                ordinal_position=1,
            ),
            ForeignKeyMetadata(
                constraint_name="fk_composite",
                column_name="product_id",
                referenced_table="products",
                referenced_column="id",
                ordinal_position=2,
            ),
        ),
    )

    prompt = build_user_prompt(table, [])

    # Both FK columns should be listed separately
    assert "order_id -> orders.id" in prompt
    assert "product_id -> products.id" in prompt


def test_build_user_prompt_empty_parent_context() -> None:
    """build_user_prompt should not include context section if list is empty."""
    table = TableMetadata(
        schema_name="public",
        table_name="users",
        columns=(
            ColumnMetadata(
                name="id", data_type="integer", is_nullable=False, ordinal_position=1
            ),
        ),
        primary_keys=("id",),
        foreign_keys=(),
    )

    # Explicitly pass empty list
    prompt = build_user_prompt(table, [])

    assert "Referenced Tables Context:" not in prompt


def test_build_user_prompt_multiple_parent_context() -> None:
    """build_user_prompt should include multiple parent descriptions."""
    users_entry = CatalogEntry(
        table_name="users",
        description="User account information",
        sensitivity="PII",
        example_queries=[],
    )

    products_entry = CatalogEntry(
        table_name="products",
        description="Product catalog",
        sensitivity="public",
        example_queries=[],
    )

    table = TableMetadata(
        schema_name="public",
        table_name="orders",
        columns=(
            ColumnMetadata(
                name="user_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=1,
            ),
            ColumnMetadata(
                name="product_id",
                data_type="integer",
                is_nullable=False,
                ordinal_position=2,
            ),
        ),
        primary_keys=(),
        foreign_keys=(
            ForeignKeyMetadata(
                constraint_name="fk1",
                column_name="user_id",
                referenced_table="users",
                referenced_column="id",
                ordinal_position=1,
            ),
            ForeignKeyMetadata(
                constraint_name="fk2",
                column_name="product_id",
                referenced_table="products",
                referenced_column="id",
                ordinal_position=1,
            ),
        ),
    )

    prompt = build_user_prompt(table, [users_entry, products_entry])

    # Both parent descriptions should be present
    assert "users: User account information" in prompt
    assert "products: Product catalog" in prompt
