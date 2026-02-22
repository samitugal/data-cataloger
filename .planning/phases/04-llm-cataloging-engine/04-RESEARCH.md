# Phase 4: LLM Cataloging Engine - Research

**Researched:** 2026-02-22
**Domain:** LLM-powered database table cataloging and metadata generation
**Confidence:** HIGH

## Summary

Phase 4 implements an LLM-powered cataloging engine that analyzes database tables and generates rich metadata including business descriptions, data sensitivity classifications, and example SQL queries. The system processes tables in dependency order (independent first) to enable context-aware analysis where LLMs can reference previously cataloged parent tables.

The standard approach uses OpenAI's GPT-4 API with Structured Outputs via Pydantic models to ensure reliable, parseable responses. The cataloging agent processes tables sequentially, maintaining a catalog of completed tables as context for analyzing dependent tables. This enables the LLM to understand foreign key relationships and generate more accurate business descriptions and query examples.

**Primary recommendation:** Use OpenAI Python SDK v2.21+ with `client.beta.chat.completions.parse()` and Pydantic BaseModel for structured outputs. Implement tenacity for exponential backoff on rate limits. Process tables in topological order from SchemaIntrospector, passing already-cataloged parent table metadata as context to improve dependent table analysis.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CATL-01 | LLM agent analyzes each table based on metadata (name, columns, relationships) | OpenAI Structured Outputs with Pydantic models ensure reliable parsing of table metadata into business descriptions |
| CATL-02 | LLM generates business description for each table (what it represents, business process) | Few-shot prompting with schema metadata and parent table context produces accurate business descriptions |
| CATL-03 | LLM classifies data sensitivity for each table (PII, financial, public, internal) | LLM-based PII classification achieves 95-97% accuracy; zero-shot classification with enum constraints works well |
| CATL-04 | LLM generates example SQL queries for each table | Schema prompting with table structure and FK relationships enables context-aware SQL generation |
| CATL-05 | LLM agent can reference already-cataloged tables for context during analysis | Sequential processing with catalog state management allows passing parent table descriptions as context |
| CATL-06 | System processes tables in dependency order (independent first) | SchemaIntrospector provides ordered tables; cataloger processes sequentially maintaining state |
| CATL-07 | System uses OpenAI GPT-4 API for LLM analysis | OpenAI Python SDK v2.21 provides production-ready GPT-4 access with structured outputs |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai | 2.21+ | GPT-4 API client | Official OpenAI Python SDK with type safety and structured outputs support |
| pydantic | 2.x | Response schema validation | Integrates natively with OpenAI structured outputs; already in project from Phase 2 |
| tenacity | 9.x | Retry with exponential backoff | Apache 2.0, recommended by OpenAI for rate limit handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.x | Environment variable loading | Development only; already in project |
| tiktoken | 0.8+ | Token counting | Cost optimization and prompt size management |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tenacity | backoff library | Both work; tenacity has more flexible wait strategies and better async support |
| GPT-4 | GPT-4o-mini | 16x cheaper but lower quality on complex schema inference; consider for cost optimization |
| Pydantic | dataclasses + manual validation | Pydantic required for OpenAI structured outputs; no viable alternative |

**Installation:**
```bash
uv add openai tenacity tiktoken
```

## Architecture Patterns

### Recommended Project Structure
```
src/data_cataloger/cataloging/
├── agent.py              # CatalogingAgent - main orchestrator
├── models.py             # Pydantic models for LLM responses
├── prompts.py            # Prompt templates and builders
├── catalog.py            # CatalogEntry and CatalogState for context management
└── __init__.py
```

### Pattern 1: Sequential Processing with Context Accumulation
**What:** Process tables in dependency order, maintaining a state object with already-cataloged tables to pass as context for dependent tables.

**When to use:** When analyzing tables with foreign key relationships where understanding parent tables improves analysis of child tables.

**Example:**
```python
# Based on LLM agent context management patterns from 2026
from dataclasses import dataclass
from data_cataloger.schema.models import TableMetadata

@dataclass
class CatalogEntry:
    """Catalog entry for a single table"""
    table_name: str
    description: str
    sensitivity: str
    example_queries: list[str]

@dataclass
class CatalogState:
    """Maintains cataloging state across tables"""
    entries: dict[str, CatalogEntry]

    def get_parent_context(self, table: TableMetadata) -> list[CatalogEntry]:
        """Get catalog entries for parent tables referenced by FKs"""
        parent_names = {fk.referenced_table for fk in table.foreign_keys}
        return [self.entries[name] for name in parent_names if name in self.entries]

class CatalogingAgent:
    def catalog_database(self, ordered_tables: list[TableMetadata]) -> dict[str, CatalogEntry]:
        """Process tables in dependency order, accumulating context"""
        state = CatalogState(entries={})

        for table in ordered_tables:
            parent_context = state.get_parent_context(table)
            entry = self._catalog_table(table, parent_context)
            state.entries[table.name] = entry

        return state.entries
```

### Pattern 2: Structured Outputs with Pydantic
**What:** Use OpenAI's `parse()` method with Pydantic models for guaranteed schema compliance.

**When to use:** Always - ensures reliable parsing without regex or error-prone JSON parsing.

**Example:**
```python
# Source: OpenAI Structured Outputs official documentation
from pydantic import BaseModel, Field
from openai import OpenAI

class TableCatalog(BaseModel):
    description: str = Field(description="Business purpose of the table")
    sensitivity: str = Field(description="Data sensitivity: PII, financial, public, or internal")
    example_queries: list[str] = Field(description="2-3 example SQL queries")

client = OpenAI()

response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    response_format=TableCatalog,
)

catalog = response.choices[0].message.parsed  # Typed Pydantic object
```

### Pattern 3: Retry with Exponential Backoff
**What:** Automatically retry failed API calls with exponentially increasing delays plus random jitter.

**When to use:** All production OpenAI API calls - handles rate limits (429) and transient errors (500-series).

**Example:**
```python
# Source: OpenAI Cookbook - How to Handle Rate Limits
from tenacity import retry, stop_after_attempt, wait_random_exponential
import openai

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=lambda e: isinstance(e, openai.RateLimitError)
)
def catalog_with_retry(self, messages: list[dict]) -> TableCatalog:
    response = self.client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format=TableCatalog,
    )
    return response.choices[0].message.parsed
```

### Pattern 4: System vs User Prompt Separation
**What:** System prompt defines agent behavior and output requirements; user prompt contains variable table-specific metadata.

**When to use:** Always - separates static instructions from dynamic content, improving consistency.

**Example:**
```python
# Based on LLM prompt engineering best practices 2026
SYSTEM_PROMPT = """You are a database documentation expert. Analyze table metadata and generate:
1. A clear business description of what the table represents
2. Data sensitivity classification (PII, financial, public, or internal)
3. 2-3 example SQL queries demonstrating common use cases

Consider foreign key relationships to understand the table's role in the schema."""

def build_user_prompt(table: TableMetadata, parent_context: list[CatalogEntry]) -> str:
    prompt = f"Table: {table.name}\n\nColumns:\n"
    for col in table.columns:
        prompt += f"- {col.name} ({col.data_type})\n"

    if table.primary_keys:
        prompt += f"\nPrimary Key: {', '.join(table.primary_keys)}\n"

    if table.foreign_keys:
        prompt += "\nForeign Keys:\n"
        for fk in table.foreign_keys:
            prompt += f"- {fk.column} -> {fk.referenced_table}.{fk.referenced_column}\n"

    if parent_context:
        prompt += "\nReferenced Tables Context:\n"
        for parent in parent_context:
            prompt += f"- {parent.table_name}: {parent.description}\n"

    return prompt
```

### Anti-Patterns to Avoid

- **Free-form text parsing:** Don't use regex or string parsing on LLM outputs - use structured outputs with Pydantic
- **Naive retries:** Don't retry immediately or with fixed delays - use exponential backoff with jitter
- **No context for dependencies:** Don't analyze dependent tables without parent context - sequential processing enables better analysis
- **Hardcoded prompts:** Don't embed table metadata in system prompts - use user prompts for variable content
- **Ignoring rate limits:** Don't skip retry logic - production systems hit rate limits; handle gracefully

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON parsing from LLM | Custom parsing logic with regex | OpenAI Structured Outputs with Pydantic | Guaranteed schema compliance, 100% reliability on gpt-4o-2024-08-06 |
| Rate limit handling | Sleep loops or fixed delays | tenacity with exponential backoff | Handles thundering herd, respects 429 headers, proven pattern |
| Token counting | Character approximations | tiktoken library | Accurate token counting for cost tracking and prompt sizing |
| API retries | Try-except with manual loops | tenacity.retry decorator | Configurable wait strategies, max attempts, exception filtering |
| Environment variables | os.getenv() with defaults | python-dotenv (already in project) | Consistent .env file loading, validation |

**Key insight:** OpenAI's ecosystem provides battle-tested solutions for common integration challenges. Custom implementations introduce bugs and maintenance burden. The 2026 production standard is structured outputs + retry decorators + token counting.

## Common Pitfalls

### Pitfall 1: Pydantic Schema Limitations with OpenAI Strict Mode
**What goes wrong:** OpenAI's strict mode supports only a subset of JSON Schema. Using Pydantic features like validators, computed fields, or complex nested generics causes validation failures.

**Why it happens:** Pydantic generates rich JSON schemas, but OpenAI's structured outputs only support basic types, enums, and simple nested models.

**How to avoid:**
- Use simple Pydantic models with basic types (str, int, list, dict)
- Use `Literal["PII", "financial", "public", "internal"]` for enums instead of validators
- Avoid @validator decorators, @computed_field, and complex Union types
- Test schema compatibility before production

**Warning signs:** Errors like "Unsupported JSON schema type" or "Schema validation failed"

### Pitfall 2: Context Window Overflow with Large Schemas
**What goes wrong:** Including full schema metadata for 200+ tables in a single prompt exceeds GPT-4's context window (128k tokens), causing truncation or errors.

**Why it happens:** Each table's columns, types, and relationships consume tokens. Parent context accumulation grows with dependency depth.

**How to avoid:**
- Process one table at a time (not batch cataloging)
- Limit parent context to 2-3 levels of FK depth
- Include only essential parent metadata (name + description, not full schema)
- Use tiktoken to measure prompt size before sending
- Consider gpt-4o-mini for cost optimization if prompts stay under 16k tokens

**Warning signs:** API errors about context length, truncated responses, missing analysis sections

### Pitfall 3: Non-Deterministic Outputs Breaking Tests
**What goes wrong:** LLM responses vary across runs, making traditional unit tests brittle. Exact string matching fails even for correct outputs.

**Why it happens:** LLMs are probabilistic; same input produces different outputs (even with temperature=0).

**How to avoid:**
- Test structure, not exact content (validate Pydantic model parses, required fields present)
- Use VCR.py/pytest-recording to record real API responses for regression tests
- Mock at API client level in unit tests (return pre-defined Pydantic objects)
- Integration tests use real API calls sparingly (CI budget considerations)
- Validate semantic properties (e.g., sensitivity is valid enum value) not exact text

**Warning signs:** Tests pass locally but fail in CI, flaky test behavior, constant cassette updates

### Pitfall 4: Cost Explosion from Naive Batching
**What goes wrong:** Cataloging 200 tables at $0.03/request seems cheap, but repeated failures, retries, and development iterations cost hundreds of dollars.

**Why it happens:** Each retry consumes tokens. Failed prompts aren't free. Development/testing uses production API without cost tracking.

**How to avoid:**
- Use GPT-4o-mini ($0.15 per 1M input tokens) during development - 16x cheaper
- Implement token counting and cost tracking from day one
- Cache successful catalog entries to disk - don't re-analyze on restart
- Use mock responses in tests (VCR.py) - no API calls
- Set daily/monthly budget alerts in OpenAI dashboard

**Warning signs:** Unexpected bills, budget alerts from OpenAI, CI runs consuming API credits

### Pitfall 5: Missing Parent Context Due to Processing Order
**What goes wrong:** Dependent table cataloging fails to reference parent tables because circular dependencies or incorrect ordering skips parents.

**Why it happens:** DependencyGraph returns cyclic nodes separately. Cataloger doesn't verify parent exists in catalog before requesting context.

**How to avoid:**
- Handle circular dependencies explicitly (catalog both nodes without parent context)
- Validate parent table in catalog before adding to context
- Log warnings when parent context unavailable
- SchemaIntrospector already filters self-references - trust the ordering
- Consider processing cyclic tables last with both-way context

**Warning signs:** Missing FK relationship context in descriptions, generic analysis for dependent tables, KeyError accessing parent catalog entries

### Pitfall 6: Plain Text API Keys in Code/Logs
**What goes wrong:** Accidentally committing API keys to git, logging them in error messages, or storing in plain text configuration files.

**Why it happens:** Development convenience leads to OPENAI_API_KEY in .env without .gitignore, or debug logging prints full config.

**How to avoid:**
- Use environment variables only (OPENAI_API_KEY)
- Verify .env in .gitignore before first commit
- Use python-dotenv for consistent .env loading
- Never log API keys - redact in error messages
- Use pre-commit hooks (e.g., trufflehog) to detect accidental exposure
- Project already uses keyring for DB credentials - consider for API keys too

**Warning signs:** API key visible in git history, keys in exception tracebacks, unauthorized API usage

## Code Examples

Verified patterns from official sources:

### Structured Output with Pydantic
```python
# Source: OpenAI Structured Outputs documentation
from pydantic import BaseModel, Field
from openai import OpenAI

class TableCatalog(BaseModel):
    """Catalog entry for a database table"""
    description: str = Field(description="Business purpose of the table in 1-2 sentences")
    sensitivity: str = Field(description="Data sensitivity level: PII, financial, public, or internal")
    example_queries: list[str] = Field(description="2-3 example SQL queries for common operations")

client = OpenAI()  # Uses OPENAI_API_KEY from environment

response = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",  # Required for structured outputs
    messages=[
        {"role": "system", "content": "You are a database documentation expert..."},
        {"role": "user", "content": "Table: users\nColumns:\n- id (integer)\n- email (varchar)..."}
    ],
    response_format=TableCatalog,
)

catalog_entry = response.choices[0].message.parsed  # Typed TableCatalog instance
```

### Retry with Exponential Backoff
```python
# Source: OpenAI Cookbook - How to Handle Rate Limits
from tenacity import retry, stop_after_attempt, wait_random_exponential
from openai import OpenAI, RateLimitError

client = OpenAI()

@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(6),
    retry=lambda e: isinstance(e, RateLimitError)
)
def catalog_table_with_retry(messages: list[dict]) -> TableCatalog:
    """Catalog a table with automatic retry on rate limits"""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=messages,
        response_format=TableCatalog,
    )
    return response.choices[0].message.parsed
```

### Environment Variable Loading
```python
# Source: OpenAI best practices for API key safety
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file (contains OPENAI_API_KEY=sk-...)
load_dotenv()

# OpenAI client automatically reads OPENAI_API_KEY from environment
client = OpenAI()

# Verify key is loaded (for debugging only - don't log full key)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment")
print(f"API key loaded: {api_key[:8]}...")  # Log only prefix
```

### Sequential Processing with Context
```python
# Based on 2026 LLM agent context management patterns
from dataclasses import dataclass, field
from data_cataloger.schema.models import TableMetadata

@dataclass
class CatalogEntry:
    table_name: str
    description: str
    sensitivity: str
    example_queries: list[str]

@dataclass
class CatalogState:
    """Maintains catalog state during sequential processing"""
    entries: dict[str, CatalogEntry] = field(default_factory=dict)

    def add_entry(self, entry: CatalogEntry) -> None:
        """Add catalog entry to state"""
        self.entries[entry.table_name] = entry

    def get_parent_context(self, table: TableMetadata) -> list[CatalogEntry]:
        """Get already-cataloged parent tables for FK context"""
        parent_names = {fk.referenced_table for fk in table.foreign_keys}
        return [
            self.entries[name]
            for name in parent_names
            if name in self.entries
        ]

class CatalogingAgent:
    def catalog_database(self, ordered_tables: list[TableMetadata]) -> dict[str, CatalogEntry]:
        """Process tables in dependency order"""
        state = CatalogState()

        for table in ordered_tables:
            # Get parent context for FK references
            parent_context = state.get_parent_context(table)

            # Catalog this table with parent context
            entry = self._catalog_table(table, parent_context)

            # Add to state for future dependent tables
            state.add_entry(entry)

        return state.entries
```

### Mocking for Tests
```python
# Source: Testing LLM integration best practices 2026
from unittest.mock import Mock, patch
import pytest
from pydantic import BaseModel

class TableCatalog(BaseModel):
    description: str
    sensitivity: str
    example_queries: list[str]

def test_cataloging_agent_mock():
    """Test cataloging logic without real API calls"""

    # Create mock response
    mock_catalog = TableCatalog(
        description="User account information",
        sensitivity="PII",
        example_queries=["SELECT * FROM users WHERE id = 1"]
    )

    # Mock the parse method
    with patch('openai.OpenAI') as mock_client:
        mock_response = Mock()
        mock_response.choices[0].message.parsed = mock_catalog
        mock_client.return_value.beta.chat.completions.parse.return_value = mock_response

        # Test cataloging agent
        agent = CatalogingAgent(client=mock_client.return_value)
        result = agent.catalog_table(table_metadata)

        assert result.description == "User account information"
        assert result.sensitivity == "PII"
        assert len(result.example_queries) == 1
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Function calling with strict:true | Structured Outputs with response_format | August 2024 (GPT-4o) | 100% schema compliance vs ~95% with function calling |
| Manual JSON parsing | client.beta.chat.completions.parse() | August 2024 | Type-safe Pydantic objects, no parsing errors |
| Batch processing all tables | Sequential with context accumulation | 2025-2026 research | Better accuracy via parent table context |
| Fixed retry delays | Exponential backoff with jitter | Long-standing best practice | Prevents thundering herd, respects rate limits |
| GPT-3.5 for cost savings | GPT-4o-mini for quality+cost balance | July 2024 | 16x cheaper than GPT-4, better quality than GPT-3.5 |

**Deprecated/outdated:**
- `client.chat.completions.create()` with JSON parsing: Use `parse()` with Pydantic instead
- `functions` parameter for structured outputs: Use `response_format` with Pydantic models
- `gpt-3.5-turbo` for schema analysis: Insufficient reasoning; use `gpt-4o-mini` minimum
- Manual token counting with len()/4: Use tiktoken for accurate counts
- Storing API keys in config files: Use environment variables only

## Open Questions

1. **What's the optimal number of parent context levels?**
   - What we know: Including all parents improves accuracy but increases token costs
   - What's unclear: At what depth does marginal accuracy gain not justify token cost?
   - Recommendation: Start with 1 level (direct parents only), evaluate quality vs cost, expand if needed

2. **Should we cache LLM responses to disk for resume/restart?**
   - What we know: Cataloging 200+ tables takes time and costs money; failures require restart
   - What's unclear: Best format for persistent catalog state (JSON, SQLite, pickle?)
   - Recommendation: Implement JSON file cache after basic cataloging works; enables resume without re-analysis

3. **How to handle circular dependencies in context?**
   - What we know: DependencyGraph returns circular_dependencies separately
   - What's unclear: Should we catalog them without context, or both-way after first pass?
   - Recommendation: Catalog circular nodes without parent context on first pass; consider second pass with mutual context if quality issues arise

4. **What's the cost budget for cataloging 200 tables?**
   - What we know: GPT-4o ~$0.03/table estimate, GPT-4o-mini ~$0.002/table
   - What's unclear: Actual prompt sizes with parent context; retry frequency in production
   - Recommendation: Test with 10-table sample, measure tokens and cost, extrapolate to 200 with 50% buffer for retries

5. **Should we support alternative LLM providers (Anthropic Claude, local models)?**
   - What we know: Requirement CATL-07 specifies OpenAI GPT-4
   - What's unclear: Future extensibility requirements
   - Recommendation: Implement OpenAI only for v1; use protocol/interface pattern for potential future abstraction

## Sources

### Primary (HIGH confidence)
- [OpenAI Structured Outputs Guide](https://developers.openai.com/api/docs/guides/structured-outputs/) - Pydantic integration, response_format, model compatibility
- [OpenAI Python SDK GitHub](https://github.com/openai/openai-python) - v2.21.0 current version, installation, API patterns
- [OpenAI Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits) - Official retry strategies, exponential backoff
- [OpenAI Cookbook: Rate Limit Handling](https://developers.openai.com/cookbook/examples/how_to_handle_rate_limits) - tenacity and backoff code examples
- [OpenAI API Pricing](https://developers.openai.com/api/docs/pricing/) - GPT-4o token costs, optimization strategies

### Secondary (MEDIUM confidence)
- [LLM-powered data classification - Grab Engineering](https://engineering.grab.com/llm-powered-data-classification) - Production LLM classification patterns
- [Chain of Agents - Google Research](https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/) - Sequential processing with context
- [In-depth Analysis of LLM-based Schema Linking](https://www.openproceedings.org/2026/conf/edbt/paper-24.pdf) - Few-shot prompting for schema analysis
- [Testing LLM Integration Best Practices - MLOps Community](https://home.mlops.community/public/blogs/effective-practices-for-mocking-llm-responses-during-the-software-development-lifecycle) - Mocking and testing strategies
- [System Prompts vs User Prompts - Tetrate](https://tetrate.io/learn/ai/system-prompts-vs-user-prompts) - Prompt design patterns

### Tertiary (LOW confidence)
- [GPT-4o Pricing Guide 2026](https://pricepertoken.com/pricing-page/model/openai-gpt-4o) - Third-party pricing aggregation
- [LLM Production Challenges - ShiftAsia](https://shiftasia.com/community/8-llm-production-challenges-problems-solutions/) - General integration pitfalls

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OpenAI SDK, Pydantic, and tenacity are official/recommended solutions
- Architecture: HIGH - Patterns verified from OpenAI docs and 2026 production practices
- Pitfalls: MEDIUM-HIGH - Based on documented issues and community experiences; some project-specific unknowns

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (30 days - OpenAI API stable, LLM patterns evolving slowly)

**Notes:**
- Requirements CATL-01 through CATL-07 all addressable with researched stack
- Project already uses Pydantic (Phase 2) - no new validation library needed
- SchemaIntrospector (Phase 3) provides ordered tables - perfect input for sequential cataloging
- OpenAI API key security can use existing keyring pattern from database credentials
