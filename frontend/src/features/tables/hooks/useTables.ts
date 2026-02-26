import { useQuery } from '@tanstack/react-query'
import { api } from '@/shared/api/client'
import type { Sensitivity } from '@/shared/types/api'

export function useTables() {
  return useQuery({
    queryKey: ['tables'],
    queryFn: api.getTables,
  })
}

export function useTable(name: string | null) {
  return useQuery({
    queryKey: ['tables', name],
    queryFn: () => (name ? api.getTable(name) : null),
    enabled: !!name,
  })
}

export function useSearchTables(query: string) {
  return useQuery({
    queryKey: ['tables', 'search', query],
    queryFn: () => api.searchTables(query),
    enabled: query.length > 0,
  })
}

export function useTablesBySensitivity(sensitivity: Sensitivity | null) {
  return useQuery({
    queryKey: ['tables', 'sensitivity', sensitivity],
    queryFn: () => (sensitivity ? api.getTablesBySensitivity(sensitivity) : null),
    enabled: !!sensitivity,
  })
}
