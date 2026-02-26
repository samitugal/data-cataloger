export type Sensitivity = 'PII' | 'financial' | 'internal' | 'public'

export interface TableSummary {
  name: string
  description: string
  sensitivity: Sensitivity
  example_queries: string[]
}

export interface ForeignKey {
  column: string
  references_table: string
  references_column: string
}

export interface TableDetail extends TableSummary {
  schema_name: string
  foreign_keys: ForeignKey[]
}

export interface GraphNode {
  id: string
  label: string
  sensitivity: Sensitivity
}

export interface GraphEdge {
  source: string
  target: string
  label: string
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface CatalogingRequest {
  host: string
  port: number
  database: string
  username: string
  password: string
  db_type: 'postgresql' | 'mysql'
}

export interface CatalogingResponse {
  status: 'started' | 'error'
  message: string
  total_tables: number
}

export interface TableCatalogedEvent {
  table_name: string
  description: string
  sensitivity: Sensitivity
  example_queries: string[]
  schema_name: string
  foreign_keys: ForeignKey[]
  index: number
  total: number
}

export interface CatalogingCompletedEvent {
  total_tables: number
  duration_seconds: number
}

export interface HeartbeatEvent {
  status: 'waiting' | 'processing'
  current_table?: string
  processed?: number
  total?: number
}
