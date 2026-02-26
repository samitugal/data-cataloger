import { useState } from 'react'

interface Position {
  x: number
  y: number
}

interface InteractiveEdgeProps {
  from: Position
  to: Position
  fromTable: string
  toTable: string
  column: string
  referencedColumn: string
  cardWidth: number
  cardHeight: number
}

export function InteractiveEdge({
  from,
  to,
  fromTable,
  toTable,
  column,
  referencedColumn,
  cardWidth,
  cardHeight,
}: InteractiveEdgeProps) {
  const [isHovered, setIsHovered] = useState(false)

  // Calculate connection points (center bottom of source, center top of target)
  const startX = from.x + cardWidth / 2
  const startY = from.y + cardHeight
  const endX = to.x + cardWidth / 2
  const endY = to.y

  // Calculate midpoint for label
  const midX = (startX + endX) / 2
  const midY = (startY + endY) / 2

  // Calculate angle for the line
  const angle = Math.atan2(endY - startY, endX - startX)
  const arrowLength = 10

  // Arrow points
  const arrowX = endX - arrowLength * Math.cos(angle)
  const arrowY = endY - arrowLength * Math.sin(angle)

  return (
    <g
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="cursor-pointer"
    >
      {/* Invisible wider path for easier hover */}
      <path
        d={`M ${startX} ${startY} L ${endX} ${endY}`}
        fill="none"
        stroke="transparent"
        strokeWidth="20"
      />

      {/* Visible line */}
      <path
        d={`M ${startX} ${startY} L ${endX} ${endY}`}
        fill="none"
        stroke={isHovered ? '#6366f1' : '#94a3b8'}
        strokeWidth={isHovered ? 3 : 2}
        strokeLinecap="round"
        className="transition-all duration-200"
      />

      {/* Arrow head */}
      <polygon
        points={`
          ${endX},${endY}
          ${arrowX - 5 * Math.cos(angle - Math.PI / 2)},${arrowY - 5 * Math.sin(angle - Math.PI / 2)}
          ${arrowX + 5 * Math.cos(angle - Math.PI / 2)},${arrowY + 5 * Math.sin(angle - Math.PI / 2)}
        `}
        fill={isHovered ? '#6366f1' : '#94a3b8'}
        className="transition-all duration-200"
      />

      {/* Hover tooltip */}
      {isHovered && (
        <g>
          {/* Background */}
          <rect
            x={midX - 80}
            y={midY - 30}
            width="160"
            height="40"
            rx="6"
            fill="white"
            stroke="#e2e8f0"
            strokeWidth="1"
            filter="drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))"
          />
          {/* Relationship text */}
          <text
            x={midX}
            y={midY - 10}
            textAnchor="middle"
            className="text-xs font-semibold fill-gray-700"
            style={{ fontSize: '11px' }}
          >
            {fromTable}.{column}
          </text>
          <text
            x={midX}
            y={midY + 5}
            textAnchor="middle"
            className="text-xs fill-gray-500"
            style={{ fontSize: '10px' }}
          >
            →
          </text>
          <text
            x={midX}
            y={midY + 18}
            textAnchor="middle"
            className="text-xs font-semibold fill-indigo-600"
            style={{ fontSize: '11px' }}
          >
            {toTable}.{referencedColumn}
          </text>
        </g>
      )}

      {/* Connection dot at start */}
      <circle
        cx={startX}
        cy={startY}
        r={isHovered ? 5 : 3}
        fill={isHovered ? '#6366f1' : '#94a3b8'}
        className="transition-all duration-200"
      />
    </g>
  )
}
