"""Prompt templates and builders for LLM table cataloging.

Provides system and user prompts that guide GPT-4o to generate accurate
business descriptions, sensitivity classifications, and example queries from
table metadata and parent table context.
"""

from data_cataloger.cataloging.models import CatalogEntry
from data_cataloger.schema.models import TableMetadata

# System prompt defines consistent agent behavior across all table analyses
SYSTEM_PROMPT = """You are a database documentation expert. Analyze table \
metadata and generate:

1. A clear business description of what the table represents (1-2 sentences)
2. Data sensitivity classification: PII, financial, public, or internal
   - PII: Contains personally identifiable information (names, emails, SSN, etc.)
   - financial: Contains financial data (transactions, balances, payment info)
   - public: Publicly accessible information with no sensitive data
   - internal: Internal business data, not sensitive but not public
3. 2-3 example SQL queries demonstrating common use cases

Consider foreign key relationships to understand the table's role in the schema.
When parent table context is provided, use it to inform your analysis."""


def build_user_prompt(table: TableMetadata, parent_context: list[CatalogEntry]) -> str:
    """Build user prompt from table metadata and parent context.

    Creates a structured prompt containing:
    - Table name and all columns with data types and nullability
    - Primary key information (if present)
    - Foreign key relationships (if present)
    - Parent table descriptions from already-cataloged tables (if available)

    This context-aware approach enables the LLM to understand table relationships
    and generate more accurate business descriptions by leveraging knowledge of
    referenced tables.

    Args:
        table: TableMetadata with columns, primary keys, and foreign keys
        parent_context: List of CatalogEntry for already-cataloged parent tables.
            Should include entries for tables referenced by this table's foreign
            keys.

    Returns:
        Formatted prompt string ready for LLM consumption, containing all metadata
        elements needed for accurate table analysis.
    """
    # Start with table name and columns
    prompt = f"Table: {table.table_name}\n\nColumns:\n"

    # List all columns with data types and nullability
    for col in table.columns:
        nullable_indicator = "" if col.is_nullable else " NOT NULL"
        prompt += f"- {col.name} ({col.data_type}){nullable_indicator}\n"

    # Add primary key section if present
    if table.primary_keys:
        pk_list = ", ".join(table.primary_keys)
        prompt += f"\nPrimary Key: {pk_list}\n"

    # Add foreign key section if present
    if table.foreign_keys:
        prompt += "\nForeign Keys:\n"
        for fk in table.foreign_keys:
            prompt += (
                f"- {fk.column_name} -> {fk.referenced_table}.{fk.referenced_column}\n"
            )

    # Add parent context section if available
    if parent_context:
        prompt += "\nReferenced Tables Context:\n"
        for parent in parent_context:
            prompt += f"- {parent.table_name}: {parent.description}\n"

    return prompt
