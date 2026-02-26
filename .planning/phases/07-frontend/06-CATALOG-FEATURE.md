# Plan 07-06: Catalog Feature

## Objective

Build live cataloging feature with real-time SSE updates and progress visualization.

## Tasks

### 6.1 Cataloging Form Component

**File:** `src/features/catalog/components/CatalogingForm.tsx`

```typescript
import { useState } from 'react'
import { Database, Play, RotateCcw } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import type { CatalogingRequest } from '@/shared/types/api'

interface CatalogingFormProps {
  onStart: (config: CatalogingRequest) => void
  onReset: () => void
  isRunning: boolean
  disabled?: boolean
}

const defaultConfig: CatalogingRequest = {
  host: 'postgres',
  port: 5432,
  database: 'northwind',
  username: 'postgres',
  password: 'postgres',
  db_type: 'postgresql',
}

export function CatalogingForm({ onStart, onReset, isRunning, disabled }: CatalogingFormProps) {
  const [config, setConfig] = useState<CatalogingRequest>(defaultConfig)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStart(config)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Database Connection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Host</label>
              <Input
                value={config.host}
                onChange={(e) => setConfig({ ...config, host: e.target.value })}
                disabled={isRunning || disabled}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Port</label>
              <Input
                type="number"
                value={config.port}
                onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) })}
                disabled={isRunning || disabled}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Database</label>
            <Input
              value={config.database}
              onChange={(e) => setConfig({ ...config, database: e.target.value })}
              disabled={isRunning || disabled}
            />
          </div>

          {showAdvanced && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Username</label>
                <Input
                  value={config.username}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                  disabled={isRunning || disabled}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Password</label>
                <Input
                  type="password"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                  disabled={isRunning || disabled}
                />
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            {showAdvanced ? 'Hide' : 'Show'} advanced options
          </button>

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isRunning || disabled} className="flex-1">
              <Play className="h-4 w-4 mr-2" />
              {isRunning ? 'Cataloging...' : 'Start Cataloging'}
            </Button>
            <Button type="button" variant="outline" onClick={onReset} disabled={isRunning}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
```

### 6.2 Progress Panel Component

**File:** `src/features/catalog/components/ProgressPanel.tsx`

```typescript
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
  const { isRunning, totalTables, processedTables, currentTable, tableOrder, tables } =
    useCatalogStore()

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
        {/* Progress bar */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">
              {isRunning ? `Processing: ${currentTable}` : isComplete ? 'Complete!' : 'Ready'}
            </span>
            <span className="font-medium">
              {processedTables} / {totalTables}
            </span>
          </div>
          <Progress
            value={progress}
            className={cn(isComplete && '[&>div]:bg-green-500')}
          />
        </div>

        {/* Table list */}
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
```

### 6.3 Live Cataloging Hook

**File:** `src/features/catalog/hooks/useLiveCataloging.ts`

```typescript
import { useState, useCallback } from 'react'
import { useSSE } from '@/shared/hooks/useSSE'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { api } from '@/shared/api/client'
import type {
  CatalogingRequest,
  TableCatalogedEvent,
  CatalogingCompletedEvent,
  HeartbeatEvent,
} from '@/shared/types/api'

type SSEEvent = TableCatalogedEvent | CatalogingCompletedEvent | HeartbeatEvent

export function useLiveCataloging() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState<number | null>(null)

  const {
    isRunning,
    addTable,
    startCataloging,
    completeCataloging,
    reset: resetStore,
  } = useCatalogStore()

  // Handle SSE events
  const handleSSEMessage = useCallback(
    (eventType: string, data: SSEEvent) => {
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
          const event = data as CatalogingCompletedEvent
          setDuration(event.duration_seconds)
          completeCataloging()
          break
        }
        case 'heartbeat': {
          // Just keep connection alive
          break
        }
      }
    },
    [addTable, completeCataloging]
  )

  // SSE connection
  const { status, connect, disconnect } = useSSE<SSEEvent>({
    url: '/api/progress',
    onMessage: handleSSEMessage,
    onError: () => setError('Connection lost'),
    enabled: isConnected,
  })

  // Start cataloging
  const start = useCallback(
    async (config: CatalogingRequest) => {
      setError(null)
      setDuration(null)

      try {
        const response = await api.startCataloging(config)

        if (response.status === 'started') {
          startCataloging(response.total_tables)
          setIsConnected(true)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start cataloging')
      }
    },
    [startCataloging]
  )

  // Reset
  const reset = useCallback(async () => {
    disconnect()
    setIsConnected(false)
    setError(null)
    setDuration(null)
    resetStore()

    try {
      await api.resetCataloging()
    } catch {
      // Ignore reset errors
    }
  }, [disconnect, resetStore])

  return {
    isRunning,
    isConnected,
    connectionStatus: status,
    error,
    duration,
    start,
    reset,
  }
}
```

### 6.4 Live Cataloging Page

**File:** `src/features/catalog/pages/LivePage.tsx`

```typescript
import { CatalogingForm } from '../components/CatalogingForm'
import { ProgressPanel } from '../components/ProgressPanel'
import { GraphContainer } from '@/features/graph'
import { TableList } from '@/features/tables'
import { TableDetail } from '@/features/tables'
import { useLiveCataloging } from '../hooks/useLiveCataloging'
import { Alert, AlertDescription } from '@/shared/components/ui/Alert'
import { AlertCircle } from 'lucide-react'

export default function LivePage() {
  const { isRunning, error, duration, start, reset } = useLiveCataloging()

  return (
    <div className="space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Live Cataloging</h1>
        <p className="text-muted-foreground">
          Watch tables appear in real-time as they are cataloged
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left column - Form & Progress */}
        <div className="lg:col-span-3 space-y-4">
          <CatalogingForm
            onStart={start}
            onReset={reset}
            isRunning={isRunning}
          />
          <ProgressPanel duration={duration ?? undefined} />
        </div>

        {/* Center - Graph */}
        <div className="lg:col-span-6">
          <div className="bg-card rounded-lg border p-4 h-[600px]">
            <h2 className="text-lg font-semibold mb-2">Relationship Graph</h2>
            <GraphContainer className="h-[calc(100%-2rem)]" />
          </div>
        </div>

        {/* Right column - Tables & Detail */}
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
```

### 6.5 Alert Component (needed for errors)

**File:** `src/shared/components/ui/Alert.tsx`

```typescript
import { forwardRef, HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/shared/lib/utils'

const alertVariants = cva(
  'relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground',
  {
    variants: {
      variant: {
        default: 'bg-background text-foreground',
        destructive:
          'border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export const Alert = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & VariantProps<typeof alertVariants>
>(({ className, variant, ...props }, ref) => (
  <div ref={ref} role="alert" className={cn(alertVariants({ variant }), className)} {...props} />
))
Alert.displayName = 'Alert'

export const AlertDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('text-sm [&_p]:leading-relaxed', className)} {...props} />
))
AlertDescription.displayName = 'AlertDescription'
```

### 6.6 Feature Index

**File:** `src/features/catalog/index.ts`

```typescript
export { CatalogingForm } from './components/CatalogingForm'
export { ProgressPanel } from './components/ProgressPanel'
export { useLiveCataloging } from './hooks/useLiveCataloging'
```

## Verification

```typescript
// Test live page
<LivePage />

// Test form
<CatalogingForm onStart={console.log} onReset={console.log} isRunning={false} />

// Test progress
<ProgressPanel duration={45.2} />
```

## Deliverables

- [ ] CatalogingForm with database config
- [ ] ProgressPanel with table list
- [ ] useLiveCataloging hook with SSE
- [ ] LivePage layout
- [ ] Alert component
- [ ] Feature exports
