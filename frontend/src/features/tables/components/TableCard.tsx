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
  const selectedTable = useCatalogStore((s) => s.selectedTable)
  const setSelectedTable = useCatalogStore((s) => s.setSelectedTable)
  const setHighlightedTable = useCatalogStore((s) => s.setHighlightedTable)
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
