# Plan 07-04: Graph Feature

## Objective

Build interactive graph visualization with Cytoscape.js for real-time table relationship display.

## Tasks

### 4.1 Cytoscape React Wrapper

**File:** `src/features/graph/components/CytoscapeGraph.tsx`

```typescript
import { useEffect, useRef, useCallback, memo } from 'react'
import cytoscape, { Core, NodeSingular, EdgeSingular } from 'cytoscape'
import type { Sensitivity } from '@/shared/types/api'

// Sensitivity color mapping
const sensitivityColors: Record<Sensitivity, string> = {
  PII: '#ef4444',
  financial: '#f59e0b',
  internal: '#3b82f6',
  public: '#22c55e',
}

// Cytoscape style configuration
const cytoscapeStyles: cytoscape.Stylesheet[] = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#6366f1',
      color: '#fff',
      'text-outline-color': '#6366f1',
      'text-outline-width': 2,
      'font-size': '11px',
      width: 70,
      height: 70,
      'transition-property': 'background-color, border-color, border-width',
      'transition-duration': '0.2s',
    },
  },
  // Sensitivity-based colors
  ...Object.entries(sensitivityColors).map(([sensitivity, color]) => ({
    selector: `node[sensitivity="${sensitivity}"]`,
    style: {
      'background-color': color,
      'text-outline-color': color,
    },
  })),
  // Selected state
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#1e1b4b',
    },
  },
  // Highlighted state (hover or related)
  {
    selector: 'node.highlighted',
    style: {
      'border-width': 4,
      'border-color': '#fbbf24',
    },
  },
  // New node animation
  {
    selector: 'node.new',
    style: {
      'border-width': 4,
      'border-color': '#fbbf24',
    },
  },
  // Dimmed state
  {
    selector: 'node.dimmed',
    style: {
      opacity: 0.3,
    },
  },
  // Edge styles
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#94a3b8',
      'target-arrow-color': '#94a3b8',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      label: 'data(label)',
      'font-size': '9px',
      'text-rotation': 'autorotate',
      'text-margin-y': -8,
      'transition-property': 'line-color, opacity',
      'transition-duration': '0.2s',
    },
  },
  {
    selector: 'edge.highlighted',
    style: {
      'line-color': '#6366f1',
      'target-arrow-color': '#6366f1',
      width: 3,
    },
  },
  {
    selector: 'edge.dimmed',
    style: {
      opacity: 0.2,
    },
  },
]

export interface GraphNode {
  id: string
  label: string
  sensitivity: Sensitivity
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
}

interface CytoscapeGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  selectedNode?: string | null
  highlightedNode?: string | null
  onNodeClick?: (nodeId: string) => void
  onNodeHover?: (nodeId: string | null) => void
  onBackgroundClick?: () => void
  className?: string
}

export const CytoscapeGraph = memo(function CytoscapeGraph({
  nodes,
  edges,
  selectedNode,
  highlightedNode,
  onNodeClick,
  onNodeHover,
  onBackgroundClick,
  className,
}: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return

    const cy = cytoscape({
      container: containerRef.current,
      style: cytoscapeStyles,
      layout: { name: 'preset' },
      minZoom: 0.2,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    })

    cyRef.current = cy

    // Event handlers
    cy.on('tap', 'node', (evt) => {
      const node = evt.target as NodeSingular
      onNodeClick?.(node.id())
    })

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        onBackgroundClick?.()
      }
    })

    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target as NodeSingular
      onNodeHover?.(node.id())
    })

    cy.on('mouseout', 'node', () => {
      onNodeHover?.(null)
    })

    return () => {
      cy.destroy()
      cyRef.current = null
    }
  }, [onNodeClick, onNodeHover, onBackgroundClick])

  // Update elements when data changes
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    // Get current element IDs
    const currentNodeIds = new Set(cy.nodes().map((n) => n.id()))
    const newNodeIds = new Set(nodes.map((n) => n.id))

    // Remove nodes that no longer exist
    cy.nodes().forEach((node) => {
      if (!newNodeIds.has(node.id())) {
        node.remove()
      }
    })

    // Add or update nodes
    nodes.forEach((node) => {
      if (currentNodeIds.has(node.id)) {
        // Update existing node
        cy.$(`#${node.id}`).data(node)
      } else {
        // Add new node with 'new' class
        cy.add({
          data: node,
          classes: 'new',
        })
      }
    })

    // Update edges
    cy.edges().remove()
    edges.forEach((edge) => {
      if (cy.$(`#${edge.source}`).length && cy.$(`#${edge.target}`).length) {
        cy.add({
          data: edge,
          group: 'edges',
        })
      }
    })

    // Run layout if we have new nodes
    if (nodes.length > 0) {
      cy.layout({
        name: 'cose',
        animate: true,
        animationDuration: 500,
        nodeRepulsion: () => 6000,
        idealEdgeLength: () => 80,
        fit: true,
        padding: 30,
      }).run()
    }

    // Remove 'new' class after animation
    setTimeout(() => {
      cy.nodes('.new').removeClass('new')
    }, 1000)
  }, [nodes, edges])

  // Handle selection
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    cy.nodes().unselect()
    if (selectedNode) {
      cy.$(`#${selectedNode}`).select()
    }
  }, [selectedNode])

  // Handle highlighting
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    // Reset all
    cy.elements().removeClass('highlighted dimmed')

    if (highlightedNode) {
      const node = cy.$(`#${highlightedNode}`)
      const neighborhood = node.neighborhood().add(node)

      // Highlight node and neighbors
      neighborhood.addClass('highlighted')

      // Dim others
      cy.elements().not(neighborhood).addClass('dimmed')
    }
  }, [highlightedNode])

  // Fit to viewport
  const fitToViewport = useCallback(() => {
    cyRef.current?.fit(undefined, 50)
  }, [])

  // Center on node
  const centerOnNode = useCallback((nodeId: string) => {
    const cy = cyRef.current
    if (!cy) return

    const node = cy.$(`#${nodeId}`)
    if (node.length) {
      cy.animate({
        center: { eles: node },
        zoom: 1.5,
        duration: 300,
      })
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: '100%', height: '100%' }}
    />
  )
})
```

### 4.2 Graph Container Component

**File:** `src/features/graph/components/GraphContainer.tsx`

```typescript
import { useMemo } from 'react'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { CytoscapeGraph, GraphNode, GraphEdge } from './CytoscapeGraph'
import { Button } from '@/shared/components/ui/Button'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'

interface GraphContainerProps {
  className?: string
}

export function GraphContainer({ className }: GraphContainerProps) {
  const { nodes, edges, selectedTable, highlightedTable, setSelectedTable, setHighlightedTable } =
    useCatalogStore()

  // Convert Map to array for Cytoscape
  const graphNodes: GraphNode[] = useMemo(
    () =>
      Array.from(nodes.values()).map((node) => ({
        id: node.id,
        label: node.label,
        sensitivity: node.sensitivity,
      })),
    [nodes]
  )

  const graphEdges: GraphEdge[] = useMemo(
    () =>
      edges.map((edge, idx) => ({
        id: `edge-${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.label,
      })),
    [edges]
  )

  return (
    <div className={cn('relative flex flex-col', className)}>
      {/* Toolbar */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        <Button variant="outline" size="icon" title="Zoom In">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" title="Zoom Out">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="outline" size="icon" title="Fit to View">
          <Maximize2 className="h-4 w-4" />
        </Button>
      </div>

      {/* Graph */}
      <div className="flex-1 min-h-[400px] border rounded-lg bg-muted/30">
        {graphNodes.length > 0 ? (
          <CytoscapeGraph
            nodes={graphNodes}
            edges={graphEdges}
            selectedNode={selectedTable}
            highlightedNode={highlightedTable}
            onNodeClick={setSelectedTable}
            onNodeHover={setHighlightedTable}
            onBackgroundClick={() => setSelectedTable(null)}
            className="w-full h-full"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No tables to display. Start cataloging to see the graph.
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sensitivity-pii" />
          <span>PII</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sensitivity-financial" />
          <span>Financial</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sensitivity-internal" />
          <span>Internal</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-sensitivity-public" />
          <span>Public</span>
        </div>
      </div>
    </div>
  )
}
```

### 4.3 Graph Hooks

**File:** `src/features/graph/hooks/useGraphData.ts`

```typescript
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

  // Load into store when data arrives
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
```

### 4.4 Feature Index

**File:** `src/features/graph/index.ts`

```typescript
export { CytoscapeGraph } from './components/CytoscapeGraph'
export { GraphContainer } from './components/GraphContainer'
export { useGraphData, useTableNeighbors } from './hooks/useGraphData'
```

## Verification

```typescript
// Test graph rendering
<GraphContainer className="h-[600px]" />

// Test with mock data
const mockNodes = [
  { id: 'users', label: 'users', sensitivity: 'PII' },
  { id: 'orders', label: 'orders', sensitivity: 'financial' },
]
const mockEdges = [
  { id: 'e1', source: 'orders', target: 'users', label: 'user_id' },
]
```

## Deliverables

- [ ] CytoscapeGraph wrapper component
- [ ] Sensitivity-based node coloring
- [ ] Node selection and highlighting
- [ ] Hover effects with neighbor highlighting
- [ ] Animated layout on data change
- [ ] GraphContainer with toolbar
- [ ] Legend component
- [ ] useGraphData hook
- [ ] Feature exports
