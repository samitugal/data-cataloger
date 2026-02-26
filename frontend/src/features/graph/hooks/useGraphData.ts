import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useEffect } from 'react'

export function useGraphData() {
  const loadFromGraph = useCatalogStore((s) => s.loadFromGraph)

  const query = useQuery({
    queryKey: ['graph'],
    queryFn: api.getGraph,
  })

  useEffect(() => {
    if (query.data) {
      loadFromGraph(query.data)
    }
  }, [query.data, loadFromGraph])

  return query
}

export function useTableNeighbors(tableName: string | null) {
  return useQuery({
    queryKey: ['graph', 'neighbors', tableName],
    queryFn: () => (tableName ? api.getTableNeighbors(tableName) : null),
    enabled: !!tableName,
  })
}
