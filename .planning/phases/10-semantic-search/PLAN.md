# Phase 10: Semantic Search with Embeddings

## Objective

Add vector embeddings to table descriptions and enable semantic search, allowing users to find tables by meaning rather than exact keyword matches.

## Overview

By generating embeddings from LLM-generated descriptions and storing them in Neo4j, we can perform similarity searches. This enables queries like "find tables related to customer orders" to return relevant tables even if they don't contain those exact words.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Cataloging Flow                     │
│                                                      │
│  Table Description ──► OpenAI Embeddings API        │
│         │                      │                     │
│         ▼                      ▼                     │
│  "This table stores      [0.023, -0.156, ...]       │
│   customer info..."       (1536 dimensions)          │
│                                                      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                     Neo4j                            │
│                                                      │
│  (:Table {                                          │
│    name: "customers",                               │
│    description: "This table stores...",            │
│    sensitivity: "PII",                              │
│    embedding: [0.023, -0.156, ...]  ◄── NEW        │
│  })                                                 │
│                                                      │
│  Vector Index: table_embedding_index                │
│                                                      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Semantic Search                     │
│                                                      │
│  Query: "customer purchase history"                 │
│         │                                           │
│         ▼                                           │
│  OpenAI Embeddings ──► Query Vector                 │
│         │                                           │
│         ▼                                           │
│  Neo4j Vector Search (cosine similarity)            │
│         │                                           │
│         ▼                                           │
│  Results: orders, order_details, customers          │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Neo4j Vector Index

Neo4j 5.x supports native vector indexes. We'll create an index on the embedding property:

```cypher
CREATE VECTOR INDEX table_embedding_index IF NOT EXISTS
FOR (t:Table)
ON t.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }
}
```

## Embedding Model

| Option | Dimensions | Cost | Speed |
|--------|------------|------|-------|
| `text-embedding-3-small` | 1536 | $0.02/1M tokens | Fast |
| `text-embedding-3-large` | 3072 | $0.13/1M tokens | Slower |
| `text-embedding-ada-002` | 1536 | $0.10/1M tokens | Legacy |

**Recommendation:** `text-embedding-3-small` - Good balance of quality, cost, and speed.

## Implementation Steps

### Step 1: Embedding Client
Create an embedding client that wraps OpenAI's embedding API.

```python
class EmbeddingClient:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
```

### Step 2: Update Neo4j Writer
Modify the writer to store embeddings alongside descriptions.

```python
def write_table_with_embedding(
    self, 
    table_name: str, 
    description: str, 
    embedding: list[float],
    ...
):
    query = """
    MERGE (t:Table {name: $name, database: $database})
    SET t.description = $description,
        t.embedding = $embedding,
        ...
    """
```

### Step 3: Create Vector Index
Add migration/setup script to create the vector index.

### Step 4: Semantic Search Query
Implement similarity search using Neo4j's vector functions.

```cypher
MATCH (t:Table {database: $database})
WHERE t.embedding IS NOT NULL
WITH t, vector.similarity.cosine(t.embedding, $query_embedding) AS score
WHERE score > $threshold
RETURN t.name, t.description, score
ORDER BY score DESC
LIMIT $limit
```

### Step 5: MCP Tool Integration
Add `semantic_search` tool to MCP server.

## New MCP Tool

### `semantic_search`
Search tables by semantic similarity to a natural language query.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| query | string | Yes | Natural language search query |
| database_name | string | Yes | Database to search |
| limit | integer | No | Max results (default: 5) |
| threshold | float | No | Min similarity score (default: 0.7) |

**Returns:**
```json
{
  "query": "customer purchase history",
  "results": [
    {
      "name": "orders",
      "description": "...",
      "similarity": 0.89
    },
    {
      "name": "order_details",
      "description": "...",
      "similarity": 0.85
    }
  ]
}
```

## File Structure

```
src/data_cataloger/
├── embeddings/
│   ├── __init__.py
│   ├── client.py         # OpenAI embedding client
│   └── models.py         # Embedding-related models
├── storage/
│   ├── writer.py         # Updated with embedding support
│   └── repository.py     # Updated with semantic search
```

## Migration Strategy

For existing catalogs without embeddings:
1. Query all tables with descriptions
2. Generate embeddings in batch
3. Update nodes with embeddings
4. Create vector index

## Timeline

| Step | Description | Estimate |
|------|-------------|----------|
| 1 | Create EmbeddingClient | 15 min |
| 2 | Update Neo4j Writer | 15 min |
| 3 | Create vector index setup | 10 min |
| 4 | Implement semantic search | 20 min |
| 5 | Add MCP semantic_search tool | 15 min |
| 6 | Migration script for existing data | 15 min |
| 7 | Testing | 15 min |
| **Total** | | **~105 min** |

## Success Criteria

- [ ] Embeddings generated during cataloging
- [ ] Embeddings stored in Neo4j nodes
- [ ] Vector index created successfully
- [ ] Semantic search returns relevant results
- [ ] MCP `semantic_search` tool works
- [ ] Existing catalogs can be migrated

## Dependencies

- `openai` (already installed)
- Neo4j 5.x with vector index support
