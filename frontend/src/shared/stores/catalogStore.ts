import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import { enableMapSet } from 'immer'
import type { TableDetail, GraphData, Sensitivity } from '@/shared/types/api'

enableMapSet()

interface GraphNode {
  id: string
  label: string
  sensitivity: Sensitivity
}

interface GraphEdge {
  source: string
  target: string
  label: string
}

interface CatalogState {
  tables: Map<string, TableDetail>
  tableOrder: string[]
  nodes: Map<string, GraphNode>
  edges: GraphEdge[]
  isRunning: boolean
  totalTables: number
  processedTables: number
  currentTable: string | null
  selectedTable: string | null
  highlightedTable: string | null

  addTable: (table: TableDetail) => void
  setSelectedTable: (name: string | null) => void
  setHighlightedTable: (name: string | null) => void
  startCataloging: (total: number) => void
  completeCataloging: () => void
  reset: () => void
  loadFromGraph: (data: GraphData) => void
}

export const useCatalogStore = create<CatalogState>()(
  immer((set) => ({
    tables: new Map(),
    tableOrder: [],
    nodes: new Map(),
    edges: [],
    isRunning: false,
    totalTables: 0,
    processedTables: 0,
    currentTable: null,
    selectedTable: null,
    highlightedTable: null,

    addTable: (table) =>
      set((state) => {
        state.tables.set(table.name, table)
        if (!state.tableOrder.includes(table.name)) {
          state.tableOrder.push(table.name)
        }

        state.nodes.set(table.name, {
          id: table.name,
          label: table.name,
          sensitivity: table.sensitivity,
        })

        table.foreign_keys.forEach((fk) => {
          if (state.nodes.has(fk.references_table)) {
            state.edges.push({
              source: table.name,
              target: fk.references_table,
              label: `${fk.column} → ${fk.references_column}`,
            })
          }
        })

        state.processedTables = state.tableOrder.length
        state.currentTable = table.name
      }),

    setSelectedTable: (name) =>
      set((state) => {
        state.selectedTable = name
      }),

    setHighlightedTable: (name) =>
      set((state) => {
        state.highlightedTable = name
      }),

    startCataloging: (total) =>
      set((state) => {
        state.isRunning = true
        state.totalTables = total
        state.processedTables = 0
        state.currentTable = null
      }),

    completeCataloging: () =>
      set((state) => {
        state.isRunning = false
        state.currentTable = null
      }),

    reset: () =>
      set((state) => {
        state.tables.clear()
        state.tableOrder = []
        state.nodes.clear()
        state.edges = []
        state.isRunning = false
        state.totalTables = 0
        state.processedTables = 0
        state.currentTable = null
        state.selectedTable = null
        state.highlightedTable = null
      }),

    loadFromGraph: (data) =>
      set((state) => {
        state.nodes.clear()
        state.edges = []

        data.nodes.forEach((node) => {
          state.nodes.set(node.id, node)
        })

        state.edges = data.edges
      }),
  }))
)
