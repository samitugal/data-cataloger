import type {
  TableSummary,
  TableDetail,
  GraphData,
  CatalogingRequest,
  CatalogingResponse,
  ConnectionRequest,
  DatabaseDiscoveryResponse,
  Sensitivity,
} from '@/shared/types/api'

const API_BASE = '/api'

class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(response.status, error.detail || response.statusText)
  }

  return response.json() as Promise<T>
}

export const api = {
  getTables: () => request<{ tables: TableSummary[]; total: number }>('/tables'),

  getTable: (name: string) => request<TableDetail>(`/tables/${encodeURIComponent(name)}`),

  searchTables: (query: string) =>
    request<{ tables: TableSummary[]; total: number }>(`/tables/search?q=${encodeURIComponent(query)}`),

  getTablesBySensitivity: (sensitivity: Sensitivity) =>
    request<{ tables: TableSummary[]; total: number }>(`/tables/sensitivity/${sensitivity}`),

  getGraph: () => request<GraphData>('/graph'),

  getTableNeighbors: (name: string) =>
    request<GraphData>(`/graph/${encodeURIComponent(name)}/neighbors`),

  startCataloging: (data: CatalogingRequest) =>
    request<CatalogingResponse>('/cataloging/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  resetCataloging: () => request<{ status: string }>('/cataloging/reset', { method: 'POST' }),

  discoverDatabases: (data: ConnectionRequest) =>
    request<DatabaseDiscoveryResponse>('/cataloging/discover', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

export { ApiError }
