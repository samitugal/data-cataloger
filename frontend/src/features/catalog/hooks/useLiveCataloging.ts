import { useState, useCallback } from 'react'
import { useSSE } from '@/shared/hooks/useSSE'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { api } from '@/shared/api/client'
import type {
  CatalogingRequest,
  TableCatalogedEvent,
  CatalogingCompletedEvent,
} from '@/shared/types/api'

export function useLiveCataloging() {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duration, setDuration] = useState<number | null>(null)
  const [databaseName, setDatabaseName] = useState<string>('northwind')

  const isRunning = useCatalogStore((s) => s.isRunning)
  const addTable = useCatalogStore((s) => s.addTable)
  const startCataloging = useCatalogStore((s) => s.startCataloging)
  const completeCataloging = useCatalogStore((s) => s.completeCataloging)
  const resetStore = useCatalogStore((s) => s.reset)

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
          const event = data as CatalogingCompletedEvent
          setDuration(event.duration_seconds)
          completeCataloging()
          break
        }
        case 'heartbeat': {
          break
        }
      }
    },
    [addTable, completeCataloging]
  )

  const { disconnect } = useSSE({
    url: `/api/progress?database_name=${encodeURIComponent(databaseName)}`,
    onMessage: handleSSEMessage,
    onError: () => setError('Connection lost'),
    enabled: isConnected,
  })

  const start = useCallback(
    async (config: CatalogingRequest) => {
      setError(null)
      setDuration(null)
      setDatabaseName(config.database)

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
    error,
    duration,
    start,
    reset,
  }
}
