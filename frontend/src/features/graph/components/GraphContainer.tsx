import { useMemo } from 'react'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { CytoscapeGraph, type GraphNode, type GraphEdge } from './CytoscapeGraph'
import { Button } from '@/shared/components/ui/Button'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { cn } from '@/shared/lib/utils'

interface GraphContainerProps {
  className?: string
}

export function GraphContainer({ className }: GraphContainerProps) {
  const nodes = useCatalogStore((s) => s.nodes)
  const edges = useCatalogStore((s) => s.edges)
  const selectedTable = useCatalogStore((s) => s.selectedTable)
  const highlightedTable = useCatalogStore((s) => s.highlightedTable)
  const setSelectedTable = useCatalogStore((s) => s.setSelectedTable)
  const setHighlightedTable = useCatalogStore((s) => s.setHighlightedTable)

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
