import { useEffect, useRef, useCallback, useState } from 'react'

type SSEStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

interface UseSSEOptions {
  url: string
  onMessage?: (event: string, data: unknown) => void
  onError?: (error: Event) => void
  enabled?: boolean
}

export function useSSE({ url, onMessage, onError, enabled = true }: UseSSEOptions) {
  const [status, setStatus] = useState<SSEStatus>('disconnected')
  const eventSourceRef = useRef<EventSource | null>(null)
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
  }, [onMessage, onError])

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setStatus('connecting')
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => setStatus('connected')

    es.onerror = (e) => {
      setStatus('error')
      onErrorRef.current?.(e)
    }

    const eventTypes = ['table:cataloged', 'cataloging:completed', 'heartbeat']
    eventTypes.forEach((eventType) => {
      es.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data: unknown = JSON.parse(e.data as string)
          onMessageRef.current?.(eventType, data)
        } catch (err) {
          console.error('Failed to parse SSE data:', err)
        }
      })
    })

    return es
  }, [url])

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setStatus('disconnected')
    }
  }, [])

  useEffect(() => {
    if (enabled) {
      connect()
    } else {
      disconnect()
    }

    return () => disconnect()
  }, [enabled, connect, disconnect])

  return { status, connect, disconnect }
}
