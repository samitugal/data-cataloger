import { useRef, useState, useMemo } from 'react'
import { LiveTableCard } from './LiveTableCard'
import { useCatalogStore } from '@/shared/stores/catalogStore'

interface Position {
  x: number
  y: number
}

const CARD_WIDTH = 180
const CARD_HEIGHT = 140
const GRID_COLS = 4
const CELL_WIDTH = 240
const CELL_HEIGHT = 200
const JITTER = 30

function getScatteredPosition(index: number): Position {
  const col = index % GRID_COLS
  const row = Math.floor(index / GRID_COLS)

  // Add some randomness to positions
  const jitterX = (Math.sin(index * 7.3) * JITTER)
  const jitterY = (Math.cos(index * 5.7) * JITTER)

  return {
    x: col * CELL_WIDTH + CELL_WIDTH / 2 - CARD_WIDTH / 2 + jitterX + 50,
    y: row * CELL_HEIGHT + CELL_HEIGHT / 2 - CARD_HEIGHT / 2 + jitterY + 50,
  }
}

interface RelationshipLine {
  from: string
  to: string
  fromPos: Position
  toPos: Position
}

function OrthogonalPath({ from, to }: { from: Position; to: Position }) {
  // Calculate center points of cards
  const startX = from.x + CARD_WIDTH / 2
  const startY = from.y + CARD_HEIGHT
  const endX = to.x + CARD_WIDTH / 2
  const endY = to.y

  // Create orthogonal path (90 degree turns)
  const midY = startY + (endY - startY) / 2

  const path = `M ${startX} ${startY} 
                L ${startX} ${midY} 
                L ${endX} ${midY} 
                L ${endX} ${endY}`

  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke="#94a3b8"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        markerEnd="url(#arrowhead)"
        className="transition-all duration-300"
      />
    </g>
  )
}

export function RelationshipCanvas() {
  const tables = useCatalogStore((s) => s.tables)
  const tableOrder = useCatalogStore((s) => s.tableOrder)
  const [selectedTable, setSelectedTable] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Calculate positions for all tables
  const cardPositions = useMemo(() => {
    const positions: Map<string, Position> = new Map()
    tableOrder.forEach((tableName, index) => {
      positions.set(tableName, getScatteredPosition(index))
    })
    return positions
  }, [tableOrder])

  // Calculate relationship lines
  const relationshipLines = useMemo(() => {
    const lines: RelationshipLine[] = []

    tableOrder.forEach((tableName) => {
      const table = tables.get(tableName)
      if (!table) return

      const fromPos = cardPositions.get(tableName)
      if (!fromPos) return

      table.foreign_keys.forEach((fk) => {
        const toPos = cardPositions.get(fk.references_table)
        if (toPos) {
          lines.push({
            from: tableName,
            to: fk.references_table,
            fromPos,
            toPos,
          })
        }
      })
    })

    return lines
  }, [tableOrder, tables, cardPositions])

  // Calculate canvas size
  const canvasSize = useMemo(() => {
    let maxX = 800
    let maxY = 600
    cardPositions.forEach((pos) => {
      maxX = Math.max(maxX, pos.x + CARD_WIDTH + 100)
      maxY = Math.max(maxY, pos.y + CARD_HEIGHT + 100)
    })
    return { width: maxX, height: maxY }
  }, [cardPositions])

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-auto">
      <div
        className="relative"
        style={{
          width: canvasSize.width,
          height: canvasSize.height,
          minWidth: '100%',
          minHeight: '100%'
        }}
      >
        {/* SVG Layer for relationship lines */}
        <svg
          className="absolute inset-0 pointer-events-none"
          width={canvasSize.width}
          height={canvasSize.height}
          style={{ zIndex: 1 }}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#94a3b8"
              />
            </marker>
          </defs>

          {relationshipLines.map((line, index) => (
            <OrthogonalPath
              key={`${line.from}-${line.to}-${index}`}
              from={line.fromPos}
              to={line.toPos}
            />
          ))}
        </svg>

        {/* Cards Layer */}
        {tableOrder.map((tableName, index) => {
          const table = tables.get(tableName)
          const position = cardPositions.get(tableName)
          if (!table || !position) return null

          return (
            <div
              key={tableName}
              className="absolute"
              style={{
                left: position.x,
                top: position.y,
                zIndex: selectedTable === tableName ? 20 : 10,
              }}
            >
              <LiveTableCard
                id={`table-${tableName}`}
                table={table}
                index={index}
                isSelected={selectedTable === tableName}
                onClick={() => setSelectedTable(tableName === selectedTable ? null : tableName)}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
