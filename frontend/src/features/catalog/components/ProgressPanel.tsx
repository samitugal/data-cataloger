import { CheckCircle2, Circle, Loader2 } from 'lucide-react'
import { Progress } from '@/shared/components/ui/Progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import { SensitivityBadge } from '@/shared/components/SensitivityBadge'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { formatDuration } from '@/shared/lib/utils'
import { cn } from '@/shared/lib/utils'

interface ProgressPanelProps {
  duration?: number
  className?: string
}

export function ProgressPanel({ duration, className }: ProgressPanelProps) {
  const isRunning = useCatalogStore((s) => s.isRunning)
  const totalTables = useCatalogStore((s) => s.totalTables)
  const processedTables = useCatalogStore((s) => s.processedTables)
  const currentTable = useCatalogStore((s) => s.currentTable)
  const tableOrder = useCatalogStore((s) => s.tableOrder)
  const tables = useCatalogStore((s) => s.tables)

  const progress = totalTables > 0 ? (processedTables / totalTables) * 100 : 0
  const isComplete = !isRunning && processedTables > 0 && processedTables === totalTables

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Progress</span>
          {isComplete && duration && (
            <span className="text-sm font-normal text-muted-foreground">
              Completed in {formatDuration(duration)}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">
              {isRunning ? `Processing: ${currentTable}` : isComplete ? 'Complete!' : 'Ready'}
            </span>
            <span className="font-medium">
              {processedTables} / {totalTables}
            </span>
          </div>
          <Progress value={progress} className={cn(isComplete && '[&>div]:bg-green-500')} />
        </div>

        <div className="max-h-[300px] overflow-y-auto">
          <ul className="space-y-1">
            {tableOrder.map((name, idx) => {
              const table = tables.get(name)
              const isProcessing = currentTable === name && isRunning
              const isProcessed = idx < processedTables

              return (
                <li
                  key={name}
                  className={cn(
                    'flex items-center gap-2 py-1 px-2 rounded text-sm',
                    isProcessing && 'bg-primary/10',
                    !isProcessed && !isProcessing && 'text-muted-foreground'
                  )}
                >
                  {isProcessing ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  ) : isProcessed ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : (
                    <Circle className="h-4 w-4" />
                  )}
                  <span className="flex-1 truncate">{name}</span>
                  {table && <SensitivityBadge sensitivity={table.sensitivity} />}
                </li>
              )
            })}
          </ul>
        </div>
      </CardContent>
    </Card>
  )
}
