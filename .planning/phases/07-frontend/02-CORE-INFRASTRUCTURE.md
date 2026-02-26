# Plan 07-02: Core Infrastructure

## Objective

Setup API client, state management, routing, and provider architecture.

## Tasks

### 2.1 Define API Types

**File:** `src/shared/types/api.ts`

```typescript
// Table types
export type Sensitivity = 'PII' | 'financial' | 'internal' | 'public'

export interface TableSummary {
  name: string
  description: string
  sensitivity: Sensitivity
  example_queries: string[]
}

export interface TableDetail extends TableSummary {
  schema_name: string
  columns?: Column[]
  foreign_keys: ForeignKey[]
}

export interface Column {
  name: string
  data_type: string
  nullable: boolean
  is_primary_key: boolean
}

export interface ForeignKey {
  column: string
  references_table: string
  references_column: string
}

// Graph types
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

// Cataloging types
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

// SSE Event types
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
```

### 2.2 Create API Client

**File:** `src/shared/api/client.ts`

```typescript
const API_BASE = '/api'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
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

  return response.json()
}

export const api = {
  // Tables
  getTables: () => request<{ tables: TableSummary[]; total: number }>('/tables'),
  
  getTable: (name: string) => 
    request<TableDetail>(`/tables/${encodeURIComponent(name)}`),
  
  searchTables: (query: string) =>
    request<{ tables: TableSummary[]; total: number }>(`/tables/search?q=${encodeURIComponent(query)}`),
  
  getTablesBySensitivity: (sensitivity: Sensitivity) =>
    request<{ tables: TableSummary[]; total: number }>(`/tables/sensitivity/${sensitivity}`),

  // Graph
  getGraph: () => request<GraphData>('/graph'),
  
  getTableNeighbors: (name: string) =>
    request<GraphData>(`/graph/${encodeURIComponent(name)}/neighbors`),

  // Cataloging
  startCataloging: (data: CatalogingRequest) =>
    request<CatalogingResponse>('/cataloging/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  resetCataloging: () =>
    request<{ status: string }>('/cataloging/reset', { method: 'POST' }),
}

export { ApiError }
```

### 2.3 Create SSE Hook

**File:** `src/shared/hooks/useSSE.ts`

```typescript
import { useEffect, useRef, useCallback, useState } from 'react'

type SSEStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseSSEOptions<T> {
  url: string
  onMessage?: (event: string, data: T) => void
  onError?: (error: Event) => void
  enabled?: boolean
}

export function useSSE<T>({ url, onMessage, onError, enabled = true }: UseSSEOptions<T>) {
  const [status, setStatus] = useState<SSEStatus>('disconnected')
  const eventSourceRef = useRef<EventSource | null>(null)
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)

  // Keep callbacks fresh
  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
  }, [onMessage, onError])

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStatus('connecting')
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => setStatus('connected')
    
    es.onerror = (e) => {
      setStatus('error')
      onErrorRef.current?.(e)
    }

    // Listen for all event types
    const eventTypes = ['table:cataloged', 'cataloging:completed', 'heartbeat']
    eventTypes.forEach((eventType) => {
      es.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as T
          onMessageRef.current?.(eventType, data)
        } catch (err) {
          console.error('Failed to parse SSE data:', err)
        }
      })
    })

    return es
  }, [url])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setStatus('disconnected')
    }
  }, [])

  useEffect(() => {
    if (enabled) {
      connect()
    } else {
      disconnect()
    }

    return () => disconnect()
  }, [enabled, connect, disconnect])

  return { status, connect, disconnect }
}
```

### 2.4 Create Zustand Stores

**File:** `src/shared/stores/catalogStore.ts`

```typescript
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import type { TableDetail, GraphData, Sensitivity } from '@/shared/types/api'

interface CatalogState {
  // Tables
  tables: Map<string, TableDetail>
  tableOrder: string[]
  
  // Graph
  nodes: Map<string, { id: string; label: string; sensitivity: Sensitivity }>
  edges: { source: string; target: string; label: string }[]
  
  // Cataloging progress
  isRunning: boolean
  totalTables: number
  processedTables: number
  currentTable: string | null
  
  // UI state
  selectedTable: string | null
  highlightedTable: string | null
  
  // Actions
  addTable: (table: TableDetail) => void
  setSelectedTable: (name: string | null) => void
  setHighlightedTable: (name: string | null) => void
  startCataloging: (total: number) => void
  completeCataloging: () => void
  reset: () => void
  loadFromGraph: (data: GraphData) => void
}

export const useCatalogStore = create<CatalogState>()(
  immer((set) => ({
    // Initial state
    tables: new Map(),
    tableOrder: [],
    nodes: new Map(),
    edges: [],
    isRunning: false,
    totalTables: 0,
    processedTables: 0,
    currentTable: null,
    selectedTable: null,
    highlightedTable: null,

    // Actions
    addTable: (table) =>
      set((state) => {
        // Add to tables map
        state.tables.set(table.name, table)
        if (!state.tableOrder.includes(table.name)) {
          state.tableOrder.push(table.name)
        }

        // Add node
        state.nodes.set(table.name, {
          id: table.name,
          label: table.name,
          sensitivity: table.sensitivity,
        })

        // Add edges for foreign keys
        table.foreign_keys.forEach((fk) => {
          // Only add edge if target exists
          if (state.nodes.has(fk.references_table)) {
            state.edges.push({
              source: table.name,
              target: fk.references_table,
              label: `${fk.column} → ${fk.references_column}`,
            })
          }
        })

        // Update progress
        state.processedTables = state.tableOrder.length
        state.currentTable = table.name
      }),

    setSelectedTable: (name) =>
      set((state) => {
        state.selectedTable = name
      }),

    setHighlightedTable: (name) =>
      set((state) => {
        state.highlightedTable = name
      }),

    startCataloging: (total) =>
      set((state) => {
        state.isRunning = true
        state.totalTables = total
        state.processedTables = 0
        state.currentTable = null
      }),

    completeCataloging: () =>
      set((state) => {
        state.isRunning = false
        state.currentTable = null
      }),

    reset: () =>
      set((state) => {
        state.tables.clear()
        state.tableOrder = []
        state.nodes.clear()
        state.edges = []
        state.isRunning = false
        state.totalTables = 0
        state.processedTables = 0
        state.currentTable = null
        state.selectedTable = null
        state.highlightedTable = null
      }),

    loadFromGraph: (data) =>
      set((state) => {
        state.nodes.clear()
        state.edges = []
        
        data.nodes.forEach((node) => {
          state.nodes.set(node.id, node)
        })
        
        state.edges = data.edges
      }),
  }))
)
```

### 2.5 Setup React Query

**File:** `src/app/providers/QueryProvider.tsx`

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { ReactNode, useState } from 'react'

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### 2.6 Setup Routing

**File:** `src/app/routes/index.tsx`

```typescript
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { AppLayout } from '@/app/layouts/AppLayout'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'

// Lazy load pages
const CatalogPage = lazy(() => import('@/features/catalog/pages/CatalogPage'))
const TablesPage = lazy(() => import('@/features/tables/pages/TablesPage'))
const LivePage = lazy(() => import('@/features/catalog/pages/LivePage'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <TablesPage />
          </Suspense>
        ),
      },
      {
        path: 'live',
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <LivePage />
          </Suspense>
        ),
      },
      {
        path: 'tables',
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <TablesPage />
          </Suspense>
        ),
      },
      {
        path: 'tables/:name',
        element: (
          <Suspense fallback={<LoadingSpinner />}>
            <TablesPage />
          </Suspense>
        ),
      },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
```

### 2.7 Create App Entry Point

**File:** `src/app/App.tsx`

```typescript
import { QueryProvider } from './providers/QueryProvider'
import { AppRouter } from './routes'

export function App() {
  return (
    <QueryProvider>
      <AppRouter />
    </QueryProvider>
  )
}
```

**File:** `src/main.tsx`

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './app/App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

## Verification

```typescript
// Test API client
import { api } from '@/shared/api/client'
const tables = await api.getTables()

// Test store
import { useCatalogStore } from '@/shared/stores/catalogStore'
const { addTable, tables } = useCatalogStore()

// Test SSE hook
import { useSSE } from '@/shared/hooks/useSSE'
const { status } = useSSE({ url: '/api/progress', enabled: true })
```

## Deliverables

- [ ] API types defined
- [ ] API client with all endpoints
- [ ] SSE hook for real-time events
- [ ] Zustand store for catalog state
- [ ] React Query provider configured
- [ ] React Router setup with lazy loading
- [ ] App entry point working
