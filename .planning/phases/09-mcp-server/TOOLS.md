# Phase 9: MCP Tools Specification

## Tool Categories

### 1. Catalog Query Tools

#### `list_tables`
List all cataloged tables in a database.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "tables": [
    {
      "name": "customers",
      "description": "Customer information...",
      "sensitivity": "PII"
    }
  ],
  "count": 14
}
```

---

#### `get_table`
Get detailed information about a specific table.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| table_name | string | Yes | Name of the table |
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "name": "customers",
  "description": "This table stores customer information...",
  "sensitivity": "PII",
  "example_queries": [
    "SELECT * FROM customers WHERE country = 'USA'",
    "SELECT customer_id, company_name FROM customers"
  ],
  "foreign_keys": [
    {
      "column": "customer_type_id",
      "references_table": "customer_demographics",
      "references_column": "customer_type_id"
    }
  ]
}
```

---

#### `search_tables`
Search tables by keyword in name or description.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| keyword | string | Yes | Search keyword |
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "tables": [...],
  "count": 3,
  "keyword": "customer"
}
```

---

#### `filter_by_sensitivity`
Filter tables by sensitivity classification.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| sensitivity | string | Yes | Sensitivity level (PII, financial, internal, public) |
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "tables": [...],
  "count": 4,
  "sensitivity": "PII"
}
```

---

### 2. Relationship Tools

#### `get_relationships`
Get foreign key relationships for a specific table.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| table_name | string | Yes | Name of the table |
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "table": "orders",
  "relationships": [
    {
      "column": "customer_id",
      "references_table": "customers",
      "references_column": "customer_id"
    },
    {
      "column": "employee_id",
      "references_table": "employees",
      "references_column": "employee_id"
    }
  ]
}
```

---

#### `get_graph`
Get the full relationship graph for visualization.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| database_name | string | Yes | Name of the database |

**Returns:**
```json
{
  "nodes": [
    {"name": "customers", "sensitivity": "PII"},
    {"name": "orders", "sensitivity": "internal"}
  ],
  "edges": [
    {"source": "orders", "target": "customers", "column": "customer_id"}
  ]
}
```

---

### 3. Semantic Search Tools (Phase 10)

#### `semantic_search`
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
      "description": "Stores customer order information...",
      "similarity": 0.89
    },
    {
      "name": "order_details",
      "description": "Line items for each order...",
      "similarity": 0.85
    },
    {
      "name": "customers",
      "description": "Customer master data...",
      "similarity": 0.78
    }
  ],
  "count": 3
}
```

---

## MCP Resources (Optional)

Resources provide static data that can be read by AI assistants.

| Resource URI | Description |
|--------------|-------------|
| `catalog://tables` | List of all tables |
| `catalog://tables/{name}` | Specific table details |
| `catalog://graph` | Relationship graph |

## Error Handling

All tools should return structured errors:

```json
{
  "error": true,
  "code": "TABLE_NOT_FOUND",
  "message": "Table 'unknown_table' not found in database 'northwind'"
}
```

## Common Error Codes

| Code | Description |
|------|-------------|
| `DATABASE_NOT_CONNECTED` | No database connection |
| `TABLE_NOT_FOUND` | Table does not exist |
| `DATABASE_NOT_FOUND` | Database not cataloged |
| `INVALID_SENSITIVITY` | Invalid sensitivity value |
