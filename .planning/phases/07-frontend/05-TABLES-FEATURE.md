# Plan 07-05: Tables Feature

## Objective

Build table browsing feature with list view, search, filtering, and detail panel.

## Tasks

### 5.1 Table List Component

**File:** `src/features/tables/components/TableList.tsx`

```typescript
import { useState } from 'react'
import { Table2, ChevronRight } from 'lucide-react'
import { SearchInput } from '@/shared/components/ui/SearchInput'
import { SensitivityBadge } from '@/shared/components/SensitivityBadge'
import { EmptyState } from '@/shared/components/ui/EmptyState'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'
import type { Sensitivity } from '@/shared/types/api'

interface TableListProps {
  className?: string
}

export function TableList({ className }: TableListProps) {
  const [search, setSearch] = useState('')
  const [filterSensitivity, setFilterSensitivity] = useState<Sensitivity | null>(null)

  const { tables, tableOrder, selectedTable, setSelectedTable, setHighlightedTable } =
    useCatalogStore()

  // Filter tables
  const filteredTables = tableOrder.filter((name) => {
    const table = tables.get(name)
    if (!table) return false

    // Search filter
    if (search && !name.toLowerCase().includes(search.toLowerCase())) {
      return false
    }

    // Sensitivity filter
    if (filterSensitivity && table.sensitivity !== filterSensitivity) {
      return false
    }

    return true
  })

  const sensitivities: Sensitivity[] = ['PII', 'financial', 'internal', 'public']

  return (
    <div className={cn('flex flex-col', className)}>
      {/* Search */}
      <div className="p-4 border-b">
        <SearchInput
          placeholder="Search tables..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onClear={() => setSearch('')}
        />

        {/* Sensitivity filters */}
        <div className="flex flex-wrap gap-2 mt-3">
          <button
            onClick={() => setFilterSensitivity(null)}
            className={cn(
              'px-2 py-1 text-xs rounded-full border transition-colors',
              !filterSensitivity
                ? 'bg-primary text-primary-foreground'
                : 'hover:bg-muted'
            )}
          >
            All
          </button>
          {sensitivities.map((s) => (
            <button
              key={s}
              onClick={() => setFilterSensitivity(filterSensitivity === s ? null : s)}
              className={cn(
                'px-2 py-1 text-xs rounded-full border transition-colors',
                filterSensitivity === s
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table list */}
      <div className="flex-1 overflow-y-auto">
        {filteredTables.length === 0 ? (
          <EmptyState
            icon={<Table2 className="h-12 w-12" />}
            title="No tables found"
            description={search ? 'Try a different search term' : 'Start cataloging to see tables'}
          />
        ) : (
          <ul className="divide-y">
            {filteredTables.map((name) => {
              const table = tables.get(name)!
              const isSelected = selectedTable === name

              return (
                <li key={name}>
                  <button
                    onClick={() => setSelectedTable(name)}
                    onMouseEnter={() => setHighlightedTable(name)}
                    onMouseLeave={() => setHighlightedTable(null)}
                    className={cn(
                      'w-full px-4 py-3 text-left flex items-center gap-3 transition-colors',
                      isSelected ? 'bg-primary/10' : 'hover:bg-muted'
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{name}</span>
                        <SensitivityBadge sensitivity={table.sensitivity} />
                      </div>
                      <p className="text-sm text-muted-foreground truncate mt-0.5">
                        {table.description}
                      </p>
                    </div>
                    <ChevronRight
                      className={cn(
                        'h-4 w-4 text-muted-foreground transition-transform',
                        isSelected && 'rotate-90'
                      )}
                    />
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t text-xs text-muted-foreground text-center">
        {filteredTables.length} of {tableOrder.length} tables
      </div>
    </div>
  )
}
```

### 5.2 Table Detail Panel

**File:** `src/features/tables/components/TableDetail.tsx`

```typescript
import { X, Key, ArrowRight, Code } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import { SensitivityBadge } from '@/shared/components/SensitivityBadge'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'

interface TableDetailProps {
  className?: string
}

export function TableDetail({ className }: TableDetailProps) {
  const { tables, selectedTable, setSelectedTable, setHighlightedTable } = useCatalogStore()

  const table = selectedTable ? tables.get(selectedTable) : null

  if (!table) {
    return (
      <div className={cn('flex items-center justify-center text-muted-foreground', className)}>
        Select a table to view details
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b">
        <div>
          <h2 className="text-xl font-bold">{table.name}</h2>
          <SensitivityBadge sensitivity={table.sensitivity} className="mt-1" />
        </div>
        <Button variant="ghost" size="icon" onClick={() => setSelectedTable(null)}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Description */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{table.description}</p>
          </CardContent>
        </Card>

        {/* Foreign Keys */}
        {table.foreign_keys.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Key className="h-4 w-4" />
                Foreign Keys
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {table.foreign_keys.map((fk, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm">
                    <code className="px-1 py-0.5 bg-muted rounded text-xs">
                      {fk.column}
                    </code>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <button
                      onClick={() => setSelectedTable(fk.references_table)}
                      onMouseEnter={() => setHighlightedTable(fk.references_table)}
                      onMouseLeave={() => setHighlightedTable(null)}
                      className="text-primary hover:underline"
                    >
                      {fk.references_table}
                    </button>
                    <span className="text-muted-foreground">
                      ({fk.references_column})
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Example Queries */}
        {table.example_queries.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Code className="h-4 w-4" />
                Example Queries
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {table.example_queries.map((query, idx) => (
                <pre
                  key={idx}
                  className="p-3 bg-muted rounded-md text-xs overflow-x-auto"
                >
                  <code>{query}</code>
                </pre>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
```

### 5.3 Table Card Component (for grid view)

**File:** `src/features/tables/components/TableCard.tsx`

```typescript
import { Card, CardContent, CardHeader } from '@/shared/components/ui/Card'
import { SensitivityBadge } from '@/shared/components/SensitivityBadge'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'
import type { TableDetail } from '@/shared/types/api'

interface TableCardProps {
  table: TableDetail
  className?: string
}

export function TableCard({ table, className }: TableCardProps) {
  const { selectedTable, setSelectedTable, setHighlightedTable } = useCatalogStore()
  const isSelected = selectedTable === table.name

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-md',
        isSelected && 'ring-2 ring-primary',
        className
      )}
      onClick={() => setSelectedTable(table.name)}
      onMouseEnter={() => setHighlightedTable(table.name)}
      onMouseLeave={() => setHighlightedTable(null)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold truncate">{table.name}</h3>
          <SensitivityBadge sensitivity={table.sensitivity} />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground line-clamp-2">{table.description}</p>
        {table.foreign_keys.length > 0 && (
          <p className="text-xs text-muted-foreground mt-2">
            {table.foreign_keys.length} foreign key{table.foreign_keys.length > 1 ? 's' : ''}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
```

### 5.4 Tables Page

**File:** `src/features/tables/pages/TablesPage.tsx`

```typescript
import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { TableList } from '../components/TableList'
import { TableDetail } from '../components/TableDetail'
import { GraphContainer } from '@/features/graph'
import { useGraphData } from '@/features/graph/hooks/useGraphData'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { LoadingSpinner } from '@/shared/components/ui/LoadingSpinner'

export default function TablesPage() {
  const { name } = useParams<{ name?: string }>()
  const { isLoading } = useGraphData()
  const setSelectedTable = useCatalogStore((s) => s.setSelectedTable)

  // Set selected table from URL
  useEffect(() => {
    if (name) {
      setSelectedTable(name)
    }
  }, [name, setSelectedTable])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-8rem)]">
      {/* Table List */}
      <div className="lg:col-span-3 bg-card rounded-lg border overflow-hidden">
        <TableList className="h-full" />
      </div>

      {/* Graph */}
      <div className="lg:col-span-6 bg-card rounded-lg border p-4">
        <GraphContainer className="h-full" />
      </div>

      {/* Detail Panel */}
      <div className="lg:col-span-3 bg-card rounded-lg border overflow-hidden">
        <TableDetail className="h-full" />
      </div>
    </div>
  )
}
```

### 5.5 Tables Hooks

**File:** `src/features/tables/hooks/useTables.ts`

```typescript
import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import type { Sensitivity } from '@/shared/types/api'

export function useTables() {
  return useQuery({
    queryKey: ['tables'],
    queryFn: api.getTables,
  })
}

export function useTable(name: string | null) {
  return useQuery({
    queryKey: ['tables', name],
    queryFn: () => (name ? api.getTable(name) : null),
    enabled: !!name,
  })
}

export function useSearchTables(query: string) {
  return useQuery({
    queryKey: ['tables', 'search', query],
    queryFn: () => api.searchTables(query),
    enabled: query.length > 0,
  })
}

export function useTablesBySensitivity(sensitivity: Sensitivity | null) {
  return useQuery({
    queryKey: ['tables', 'sensitivity', sensitivity],
    queryFn: () => (sensitivity ? api.getTablesBySensitivity(sensitivity) : null),
    enabled: !!sensitivity,
  })
}
```

### 5.6 Feature Index

**File:** `src/features/tables/index.ts`

```typescript
export { TableList } from './components/TableList'
export { TableDetail } from './components/TableDetail'
export { TableCard } from './components/TableCard'
export { useTables, useTable, useSearchTables, useTablesBySensitivity } from './hooks/useTables'
```

## Verification

```typescript
// Test table list
<TableList className="h-[600px]" />

// Test detail panel
<TableDetail className="h-[600px]" />

// Test full page
<TablesPage />
```

## Deliverables

- [ ] TableList with search and filter
- [ ] TableDetail panel
- [ ] TableCard for grid view
- [ ] TablesPage layout
- [ ] useTables hooks
- [ ] Feature exports
