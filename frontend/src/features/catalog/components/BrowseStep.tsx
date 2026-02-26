import { useState } from 'react'
import { RotateCcw, Database, Shield, CheckCircle2, Search, Filter } from 'lucide-react'
import { LiveTableCard } from './LiveTableCard'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { cn } from '@/shared/lib/utils'
import type { Sensitivity } from '@/shared/types/api'

const sensitivityFilters: { value: Sensitivity | 'all'; label: string; color: string }[] = [
  { value: 'all', label: 'All', color: 'bg-primary' },
  { value: 'PII', label: 'PII', color: 'bg-red-500' },
  { value: 'financial', label: 'Financial', color: 'bg-amber-500' },
  { value: 'internal', label: 'Internal', color: 'bg-blue-500' },
  { value: 'public', label: 'Public', color: 'bg-green-500' },
]

export function BrowseStep() {
  const resetCatalog = useCatalogStore((s) => s.reset)
  const resetWizard = useWizardStore((s) => s.reset)
  const tables = useCatalogStore((s) => s.tables)
  const tableOrder = useCatalogStore((s) => s.tableOrder)
  const processedTables = useCatalogStore((s) => s.processedTables)

  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [sensitivityFilter, setSensitivityFilter] = useState<Sensitivity | 'all'>('all')

  const handleStartOver = () => {
    resetCatalog()
    resetWizard()
  }

  // Calculate sensitivity stats
  const tableList = Array.from(tables.values())
  const piiCount = tableList.filter((t) => t.sensitivity === 'PII').length
  const financialCount = tableList.filter((t) => t.sensitivity === 'financial').length
  const internalCount = tableList.filter((t) => t.sensitivity === 'internal').length
  const publicCount = tableList.filter((t) => t.sensitivity === 'public').length

  // Filter tables
  const filteredTables = tableOrder.filter((tableName) => {
    const table = tables.get(tableName)
    if (!table) return false

    const matchesSearch = tableName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      table.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSensitivity = sensitivityFilter === 'all' || table.sensitivity === sensitivityFilter

    return matchesSearch && matchesSensitivity
  })

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] px-4">
      {/* Header */}
      <div className="flex-shrink-0 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-green-500" />
            <div>
              <h1 className="text-xl font-bold">Catalog Browser</h1>
              <p className="text-sm text-muted-foreground">
                Explore your cataloged tables and their relationships
              </p>
            </div>
          </div>
          <Button variant="outline" onClick={handleStartOver}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Start Over
          </Button>
        </div>

        {/* Compact Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Database className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{processedTables}</p>
              <p className="text-xs text-muted-foreground">Total Tables</p>
            </div>
          </div>

          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10">
              <Shield className="h-4 w-4 text-red-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{piiCount + financialCount}</p>
              <p className="text-xs text-muted-foreground">High Sensitivity</p>
            </div>
          </div>

          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Shield className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{internalCount}</p>
              <p className="text-xs text-muted-foreground">Internal</p>
            </div>
          </div>

          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{publicCount}</p>
              <p className="text-xs text-muted-foreground">Public</p>
            </div>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search tables..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            {sensitivityFilters.map((filter) => (
              <button
                key={filter.value}
                onClick={() => setSensitivityFilter(filter.value)}
                className={cn(
                  'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                  sensitivityFilter === filter.value
                    ? `${filter.color} text-white`
                    : 'bg-muted hover:bg-muted/80'
                )}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Card Grid */}
      <div className="flex-1 bg-gradient-to-br from-muted/30 via-background to-muted/30 rounded-xl border overflow-hidden relative">
        <div className="h-full overflow-auto p-6">
          <div className="flex flex-wrap gap-4 justify-center">
            {filteredTables.map((tableName, index) => {
              const table = tables.get(tableName)
              if (!table) return null
              return (
                <LiveTableCard
                  key={tableName}
                  table={table}
                  index={index}
                  isSelected={selectedTable === tableName}
                  onClick={() => setSelectedTable(tableName === selectedTable ? null : tableName)}
                />
              )
            })}
          </div>
          {filteredTables.length === 0 && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Search className="h-12 w-12 text-muted-foreground/50 mx-auto mb-4" />
                <p className="text-lg font-medium">No tables found</p>
                <p className="text-sm text-muted-foreground">Try adjusting your search or filter</p>
              </div>
            </div>
          )}
        </div>

        {/* Results count */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-card/90 backdrop-blur-sm rounded-full px-4 py-2 border shadow-lg">
          <span className="text-sm text-muted-foreground">
            Showing <span className="font-medium text-foreground">{filteredTables.length}</span> of {tableOrder.length} tables
          </span>
        </div>
      </div>
    </div>
  )
}
