import { AlertCircle } from 'lucide-react'
import { CatalogingForm } from '../components/CatalogingForm'
import { ProgressPanel } from '../components/ProgressPanel'
import { GraphContainer } from '@/features/graph'
import { TableList, TableDetail } from '@/features/tables'
import { useLiveCataloging } from '../hooks/useLiveCataloging'
import { Alert, AlertDescription } from '@/shared/components/ui/Alert'

export default function LivePage() {
  const { isRunning, error, duration, start, reset } = useLiveCataloging()

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Live Cataloging</h1>
        <p className="text-muted-foreground">
          Watch tables appear in real-time as they are cataloged
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-3 space-y-4">
          <CatalogingForm onStart={start} onReset={reset} isRunning={isRunning} />
          <ProgressPanel duration={duration ?? undefined} />
        </div>

        <div className="lg:col-span-6">
          <div className="bg-card rounded-lg border p-4 h-[600px]">
            <h2 className="text-lg font-semibold mb-2">Relationship Graph</h2>
            <GraphContainer className="h-[calc(100%-2rem)]" />
          </div>
        </div>

        <div className="lg:col-span-3 space-y-4">
          <div className="bg-card rounded-lg border h-[300px] overflow-hidden">
            <TableList className="h-full" />
          </div>
          <div className="bg-card rounded-lg border h-[284px] overflow-hidden">
            <TableDetail className="h-full" />
          </div>
        </div>
      </div>
    </div>
  )
}
