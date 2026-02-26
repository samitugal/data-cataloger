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
    <div className="flex flex-col h-[calc(100vh-80px)]">
      {/* Minimal Top Dashboard Bar */}
      <div className="flex-shrink-0 bg-white border-b px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left: Status */}
          <div className="flex items-center gap-3">
            {isRunning ? (
              <Loader2 className="h-5 w-5 text-primary animate-spin" />
            ) : (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            )}
            <div>
              <h1 className="text-lg font-semibold">
                {isComplete ? 'Cataloging Complete!' : 'Discovering Tables...'}
              </h1>
              <p className="text-xs text-gray-500">
                {isComplete ? 'All tables have been analyzed' : 'Watch as tables appear in real-time'}
              </p>
            </div>
          </div>

          {/* Center: Stats */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-primary" />
              <span className="text-lg font-bold">{processedTables}/{totalTables}</span>
              <div className="flex items-center gap-1 px-2 py-0.5 bg-primary/10 rounded-full">
                <span className="text-xs font-medium text-primary">{Math.round(progress)}%</span>
              </div>
              <span className="text-xs text-gray-500">Tables</span>
            </div>

            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-lg font-bold">{elapsedTime.toFixed(1)}s</span>
              <span className="text-xs text-gray-500">{isRunning ? 'Elapsed' : 'Total'}</span>
            </div>

            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-red-500" />
              <span className="text-lg font-bold">{piiCount + financialCount}</span>
              <span className="text-xs text-gray-500">High Sensitivity</span>
              <span className="text-xs text-red-500">{piiCount} PII</span>
              <span className="text-xs text-gray-400">·</span>
              <span className="text-xs text-amber-500">{financialCount} Fin</span>
            </div>

            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-lg font-bold">{internalCount + publicCount}</span>
              <span className="text-xs text-gray-500">Standard</span>
              <span className="text-xs text-blue-500">{internalCount} Int</span>
              <span className="text-xs text-gray-400">·</span>
              <span className="text-xs text-green-500">{publicCount} Pub</span>
            </div>
          </div>

          {/* Right: Action */}
          {isComplete && (
            <Button onClick={() => setStep('browse')} size="default">
              View Results
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Full Page Canvas - Excalidraw Style */}
      <div className="flex-1 relative overflow-hidden canvas-grid bg-gray-50">
        <div className="absolute inset-0 overflow-auto p-8">
          {tableOrder.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="h-16 w-16 text-primary animate-spin mx-auto mb-4" />
                <p className="text-xl font-medium text-gray-700">Discovering tables...</p>
                <p className="text-sm text-gray-500">Tables will pop in as they are cataloged</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-6 justify-center items-start pt-4">
              {tableOrder.map((tableName, index) => {
                const table = tables.get(tableName)
                if (!table) return null
                return (
                  <LiveTableCard
                    key={tableName}
                    id={`table-${tableName}`}
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

        {/* Bottom Legend */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-white/95 backdrop-blur-sm rounded-full px-5 py-2.5 border shadow-lg">
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-red-100 border-2 border-red-300" />
            <span className="text-xs font-medium text-gray-600">PII</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-amber-100 border-2 border-amber-300" />
            <span className="text-xs font-medium text-gray-600">Financial</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-blue-100 border-2 border-blue-300" />
            <span className="text-xs font-medium text-gray-600">Internal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded bg-green-100 border-2 border-green-300" />
            <span className="text-xs font-medium text-gray-600">Public</span>
          </div>
        </div>
      </div>
    </div>
  )
}
