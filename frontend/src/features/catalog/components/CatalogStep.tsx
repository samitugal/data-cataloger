import { useCallback } from 'react'
import { StatsBar } from './StatsBar'
import { ProgressPanel } from './ProgressPanel'
import { GraphContainer } from '@/features/graph'
import { TableList, TableDetail } from '@/features/tables'
import { useSSE } from '@/shared/hooks/useSSE'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { Button } from '@/shared/components/ui/Button'
import { ArrowRight } from 'lucide-react'
import type { TableCatalogedEvent } from '@/shared/types/api'

export function CatalogStep() {
  const isRunning = useCatalogStore((s) => s.isRunning)
  const addTable = useCatalogStore((s) => s.addTable)
  const completeCataloging = useCatalogStore((s) => s.completeCataloging)
  const processedTables = useCatalogStore((s) => s.processedTables)
  const totalTables = useCatalogStore((s) => s.totalTables)

  const wizardComplete = useWizardStore((s) => s.completeCataloging)
  const setStep = useWizardStore((s) => s.setStep)

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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            {isComplete ? 'Cataloging Complete!' : 'Cataloging in Progress...'}
          </h1>
          <p className="text-muted-foreground">
            {isComplete
              ? 'All tables have been analyzed and cataloged'
              : 'Watch as tables are discovered and analyzed in real-time'}
          </p>
        </div>
        {isComplete && (
          <Button onClick={() => setStep('browse')}>
            View Results
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>

      <StatsBar />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <ProgressPanel />
        </div>

        <div className="lg:col-span-6">
          <div className="bg-card rounded-lg border p-4 h-[500px]">
            <h2 className="text-lg font-semibold mb-2">Relationship Graph</h2>
            <GraphContainer className="h-[calc(100%-2rem)]" />
          </div>
        </div>

        <div className="lg:col-span-3 space-y-4">
          <div className="bg-card rounded-lg border h-[240px] overflow-hidden">
            <TableList className="h-full" />
          </div>
          <div className="bg-card rounded-lg border h-[244px] overflow-hidden">
            <TableDetail className="h-full" />
          </div>
        </div>
      </div>
    </div>
  )
}
