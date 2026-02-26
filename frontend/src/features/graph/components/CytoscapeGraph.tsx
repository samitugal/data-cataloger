import { useEffect, useRef, memo } from 'react'
import cytoscape, { type Core, type NodeSingular } from 'cytoscape'
import type { Sensitivity } from '@/shared/types/api'

const sensitivityColors: Record<Sensitivity, string> = {
  PII: '#ef4444',
  financial: '#f59e0b',
  internal: '#3b82f6',
  public: '#22c55e',
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cytoscapeStyles: any[] = [
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
    },
  },
  ...Object.entries(sensitivityColors).map(([sensitivity, color]) => ({
    selector: `node[sensitivity="${sensitivity}"]`,
    style: {
      'background-color': color,
      'text-outline-color': color,
    },
  })),
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
      'border-color': '#1e1b4b',
    },
  },
  {
    selector: 'node.highlighted',
    style: {
      'border-width': 4,
      'border-color': '#fbbf24',
    },
  },
  {
    selector: 'node.new',
    style: {
      'border-width': 4,
      'border-color': '#fbbf24',
    },
  },
  {
    selector: 'node.dimmed',
    style: {
      opacity: 0.3,
    },
  },
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

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    const currentNodeIds = new Set(cy.nodes().map((n) => n.id()))
    const newNodeIds = new Set(nodes.map((n) => n.id))

    cy.nodes().forEach((node) => {
      if (!newNodeIds.has(node.id())) {
        node.remove()
      }
    })

    nodes.forEach((node) => {
      if (currentNodeIds.has(node.id)) {
        cy.$(`#${node.id}`).data(node)
      } else {
        cy.add({
          data: node,
          classes: 'new',
        })
      }
    })

    cy.edges().remove()
    edges.forEach((edge) => {
      if (cy.$(`#${edge.source}`).length && cy.$(`#${edge.target}`).length) {
        cy.add({
          data: edge,
          group: 'edges',
        })
      }
    })

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

    setTimeout(() => {
      cy.nodes('.new').removeClass('new')
    }, 1000)
  }, [nodes, edges])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    cy.nodes().unselect()
    if (selectedNode) {
      cy.$(`#${selectedNode}`).select()
    }
  }, [selectedNode])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    cy.elements().removeClass('highlighted dimmed')

    if (highlightedNode) {
      const node = cy.$(`#${highlightedNode}`)
      const neighborhood = node.neighborhood().add(node)

      neighborhood.addClass('highlighted')
      cy.elements().not(neighborhood).addClass('dimmed')
    }
  }, [highlightedNode])


  return <div ref={containerRef} className={className} style={{ width: '100%', height: '100%' }} />
})
