import { X, Key, ArrowRight, Code } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import { SensitivityBadge } from '@/shared/components/SensitivityBadge'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'

interface TableDetailProps {
  className?: string
}

export function TableDetail({ className }: TableDetailProps) {
  const tables = useCatalogStore((s) => s.tables)
  const selectedTable = useCatalogStore((s) => s.selectedTable)
  const setSelectedTable = useCatalogStore((s) => s.setSelectedTable)
  const setHighlightedTable = useCatalogStore((s) => s.setHighlightedTable)

  const table = selectedTable ? tables.get(selectedTable) : null

  if (!table) {
    return (
      <div className={cn('flex items-center justify-center text-muted-foreground', className)}>
        Select a table to view details
      </div>
    )
  }

  return (
    <div className={cn('flex flex-col overflow-hidden', className)}>
      <div className="flex items-start justify-between p-4 border-b">
        <div>
          <h2 className="text-xl font-bold">{table.name}</h2>
          <SensitivityBadge sensitivity={table.sensitivity} className="mt-1" />
        </div>
        <Button variant="ghost" size="icon" onClick={() => setSelectedTable(null)}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Description</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{table.description}</p>
          </CardContent>
        </Card>

        {table.foreign_keys.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Key className="h-4 w-4" />
                Foreign Keys
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {table.foreign_keys.map((fk, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm">
                    <code className="px-1 py-0.5 bg-muted rounded text-xs">{fk.column}</code>
                    <ArrowRight className="h-3 w-3 text-muted-foreground" />
                    <button
                      onClick={() => setSelectedTable(fk.references_table)}
                      onMouseEnter={() => setHighlightedTable(fk.references_table)}
                      onMouseLeave={() => setHighlightedTable(null)}
                      className="text-primary hover:underline"
                    >
                      {fk.references_table}
                    </button>
                    <span className="text-muted-foreground">({fk.references_column})</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {table.example_queries.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Code className="h-4 w-4" />
                Example Queries
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {table.example_queries.map((query, idx) => (
                <pre key={idx} className="p-3 bg-muted rounded-md text-xs overflow-x-auto">
                  <code>{query}</code>
                </pre>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
