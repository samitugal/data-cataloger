import { useState, useCallback, useRef } from 'react'
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
  const eventSourceRef = useRef<EventSource | null>(null)

  const isRunning = useCatalogStore((s) => s.isRunning)
  const addTable = useCatalogStore((s) => s.addTable)
  const startCataloging = useCatalogStore((s) => s.startCataloging)
  const completeCataloging = useCatalogStore((s) => s.completeCataloging)
  const resetStore = useCatalogStore((s) => s.reset)

  const connectSSE = useCallback(
    (databaseName: string) => {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }

      const url = `/api/progress?database_name=${encodeURIComponent(databaseName)}`
      const es = new EventSource(url)
      eventSourceRef.current = es

      es.onerror = () => {
        setError('Connection lost')
      }

      es.addEventListener('table:cataloged', (e: MessageEvent) => {
        try {
          const event = JSON.parse(e.data) as TableCatalogedEvent
          addTable({
            name: event.table_name,
            description: event.description,
            sensitivity: event.sensitivity,
            example_queries: event.example_queries,
            schema_name: event.schema_name,
            foreign_keys: event.foreign_keys,
          })
        } catch (err) {
          console.error('Failed to parse table event:', err)
        }
      })

      es.addEventListener('cataloging:completed', (e: MessageEvent) => {
        try {
          const event = JSON.parse(e.data) as CatalogingCompletedEvent
          setDuration(event.duration_seconds)
          completeCataloging()
        } catch (err) {
          console.error('Failed to parse completed event:', err)
        }
      })

      setIsConnected(true)
    },
    [addTable, completeCataloging]
  )

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsConnected(false)
  }, [])

  const start = useCallback(
    async (config: CatalogingRequest) => {
      setError(null)
      setDuration(null)

      try {
        const response = await api.startCataloging(config)

        if (response.status === 'started') {
          startCataloging(response.total_tables)
          // Connect SSE with the correct database name immediately
          connectSSE(config.database)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start cataloging')
      }
    },
    [startCataloging, connectSSE]
  )

  const reset = useCallback(async () => {
    disconnect()
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
