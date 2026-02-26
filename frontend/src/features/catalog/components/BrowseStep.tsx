import { RotateCcw } from 'lucide-react'
import { GraphContainer } from '@/features/graph'
import { TableList, TableDetail } from '@/features/tables'
import { StatsBar } from './StatsBar'
import { Button } from '@/shared/components/ui/Button'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useWizardStore } from '@/shared/stores/wizardStore'

export function BrowseStep() {
  const resetCatalog = useCatalogStore((s) => s.reset)
  const resetWizard = useWizardStore((s) => s.reset)

  const handleStartOver = () => {
    resetCatalog()
    resetWizard()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Catalog Browser</h1>
          <p className="text-muted-foreground">
            Explore your cataloged tables and their relationships
          </p>
        </div>
        <Button variant="outline" onClick={handleStartOver}>
          <RotateCcw className="mr-2 h-4 w-4" />
          Start Over
        </Button>
      </div>

      <StatsBar />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-[calc(100vh-20rem)]">
        <div className="lg:col-span-3 bg-card rounded-lg border overflow-hidden">
          <TableList className="h-full" />
        </div>

        <div className="lg:col-span-6 bg-card rounded-lg border p-4">
          <GraphContainer className="h-full" />
        </div>

        <div className="lg:col-span-3 bg-card rounded-lg border overflow-hidden">
          <TableDetail className="h-full" />
        </div>
      </div>
    </div>
  )
}
