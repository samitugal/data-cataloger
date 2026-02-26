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
  )
}
