import { useCallback, useState, useEffect } from 'react'
import { LiveTableCard } from './LiveTableCard'
import { useSSE } from '@/shared/hooks/useSSE'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { Button } from '@/shared/components/ui/Button'
import { ArrowRight, Database, Clock, Shield, CheckCircle2, Loader2 } from 'lucide-react'
import type { TableCatalogedEvent } from '@/shared/types/api'

export function CatalogStep() {
  const isRunning = useCatalogStore((s) => s.isRunning)
  const addTable = useCatalogStore((s) => s.addTable)
  const completeCataloging = useCatalogStore((s) => s.completeCataloging)
  const processedTables = useCatalogStore((s) => s.processedTables)
  const totalTables = useCatalogStore((s) => s.totalTables)
  const tables = useCatalogStore((s) => s.tables)
  const tableOrder = useCatalogStore((s) => s.tableOrder)

  const wizardComplete = useWizardStore((s) => s.completeCataloging)
  const setStep = useWizardStore((s) => s.setStep)
  const startTime = useWizardStore((s) => s.startTime)

  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      if (startTime) {
        setElapsedTime((Date.now() - startTime) / 1000)
      }
    }, 100)
    return () => clearInterval(interval)
  }, [startTime])

  const handleSSEMessage = useCallback(
    (eventType: string, data: unknown) => {
      switch (eventType) {
        case 'table:cataloged': {
          const event = data as TableCatalogedEvent
          addTable({
            name: event.table_name,
            description: event.description,
            sensitivity: event.sensitivity,
            example_queries: event.example_queries,
            schema_name: event.schema_name,
            foreign_keys: event.foreign_keys,
          })
          break
        }
        case 'cataloging:completed': {
          completeCataloging()
          wizardComplete()
          break
        }
      }
    },
    [addTable, completeCataloging, wizardComplete]
  )

  const dbConfig = useWizardStore((s) => s.dbConfig)

  useSSE({
    url: `/api/progress?database=${dbConfig?.database || 'northwind'}`,
    onMessage: handleSSEMessage,
    enabled: true,
  })

  const isComplete = !isRunning && processedTables > 0 && processedTables === totalTables
  const progress = totalTables > 0 ? (processedTables / totalTables) * 100 : 0

  // Calculate sensitivity stats
  const tableList = Array.from(tables.values())
  const piiCount = tableList.filter((t) => t.sensitivity === 'PII').length
  const financialCount = tableList.filter((t) => t.sensitivity === 'financial').length
  const internalCount = tableList.filter((t) => t.sensitivity === 'internal').length
  const publicCount = tableList.filter((t) => t.sensitivity === 'public').length

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] px-4">
      {/* Compact Dashboard Header */}
      <div className="flex-shrink-0 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            {isRunning ? (
              <Loader2 className="h-6 w-6 text-primary animate-spin" />
            ) : (
              <CheckCircle2 className="h-6 w-6 text-green-500" />
            )}
            <div>
              <h1 className="text-xl font-bold">
                {isComplete ? 'Cataloging Complete!' : 'Discovering Tables...'}
              </h1>
              <p className="text-sm text-muted-foreground">
                {isComplete
                  ? 'All tables have been analyzed'
                  : 'Watch as tables appear in real-time'}
              </p>
            </div>
          </div>
          {isComplete && (
            <Button onClick={() => setStep('browse')} size="lg">
              View Results
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Database className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-2xl font-bold">{processedTables}/{totalTables}</p>
              <p className="text-xs text-muted-foreground">Tables</p>
            </div>
            <div className="ml-auto">
              <div className="w-12 h-12 relative">
                <svg className="w-12 h-12 -rotate-90">
                  <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="4" className="text-muted/20" />
                  <circle cx="24" cy="24" r="20" fill="none" stroke="currentColor" strokeWidth="4" className="text-primary" strokeDasharray={`${progress * 1.256} 125.6`} strokeLinecap="round" />
                </svg>
                <span className="absolute inset-0 flex items-center justify-center text-xs font-medium">{Math.round(progress)}%</span>
              </div>
            </div>
          </div>

          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Clock className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{elapsedTime.toFixed(1)}s</p>
              <p className="text-xs text-muted-foreground">{isRunning ? 'Elapsed' : 'Total Time'}</p>
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
            <div className="ml-auto text-xs text-muted-foreground">
              <span className="text-red-500">{piiCount} PII</span>
              <span className="mx-1">·</span>
              <span className="text-amber-500">{financialCount} Fin</span>
            </div>
          </div>

          <div className="bg-card rounded-lg border p-3 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold">{internalCount + publicCount}</p>
              <p className="text-xs text-muted-foreground">Standard</p>
            </div>
            <div className="ml-auto text-xs text-muted-foreground">
              <span className="text-blue-500">{internalCount} Int</span>
              <span className="mx-1">·</span>
              <span className="text-green-500">{publicCount} Pub</span>
            </div>
          </div>
        </div>
      </div>

      {/* Full Page Interactive Card Grid */}
      <div className="flex-1 bg-gradient-to-br from-muted/30 via-background to-muted/30 rounded-xl border overflow-hidden">
        <div className="h-full overflow-auto p-6">
          {tableOrder.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="h-12 w-12 text-primary animate-spin mx-auto mb-4" />
                <p className="text-lg font-medium">Discovering tables...</p>
                <p className="text-sm text-muted-foreground">Tables will appear here as they are cataloged</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-4 justify-center">
              {tableOrder.map((tableName, index) => {
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
          )}
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-card/90 backdrop-blur-sm rounded-full px-4 py-2 border shadow-lg">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-xs">PII</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="text-xs">Financial</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-xs">Internal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-xs">Public</span>
          </div>
        </div>
      </div>
    </div>
  )
}
