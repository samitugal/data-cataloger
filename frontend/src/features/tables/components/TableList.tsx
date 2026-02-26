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

  const tables = useCatalogStore((s) => s.tables)
  const tableOrder = useCatalogStore((s) => s.tableOrder)
  const selectedTable = useCatalogStore((s) => s.selectedTable)
  const setSelectedTable = useCatalogStore((s) => s.setSelectedTable)
  const setHighlightedTable = useCatalogStore((s) => s.setHighlightedTable)

  const filteredTables = tableOrder.filter((name) => {
    const table = tables.get(name)
    if (!table) return false

    if (search && !name.toLowerCase().includes(search.toLowerCase())) {
      return false
    }

    if (filterSensitivity && table.sensitivity !== filterSensitivity) {
      return false
    }

    return true
  })

  const sensitivities: Sensitivity[] = ['PII', 'financial', 'internal', 'public']

  return (
    <div className={cn('flex flex-col', className)}>
      <div className="p-4 border-b">
        <SearchInput
          placeholder="Search tables..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onClear={() => setSearch('')}
        />

        <div className="flex flex-wrap gap-2 mt-3">
          <button
            onClick={() => setFilterSensitivity(null)}
            className={cn(
              'px-2 py-1 text-xs rounded-full border transition-colors',
              !filterSensitivity ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
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
                filterSensitivity === s ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

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

      <div className="p-3 border-t text-xs text-muted-foreground text-center">
        {filteredTables.length} of {tableOrder.length} tables
      </div>
    </div>
  )
}
