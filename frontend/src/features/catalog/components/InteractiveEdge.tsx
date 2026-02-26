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
  index?: number
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

  // Calculate dynamic popup width based on text length
  const fromText = `${fromTable}.${column}`
  const toText = `${toTable}.${referencedColumn}`
  const maxTextLength = Math.max(fromText.length, toText.length)
  const popupWidth = Math.max(180, maxTextLength * 8 + 40)
  const popupHeight = 50

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
        <g style={{ pointerEvents: 'none' }}>
          {/* Background */}
          <rect
            x={midX - popupWidth / 2}
            y={midY - popupHeight / 2}
            width={popupWidth}
            height={popupHeight}
            rx="8"
            fill="white"
            stroke="#6366f1"
            strokeWidth="2"
            filter="drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15))"
          />
          {/* Relationship text */}
          <text
            x={midX}
            y={midY - 8}
            textAnchor="middle"
            fontWeight="600"
            fill="#374151"
            style={{ fontSize: '12px' }}
          >
            {fromText}
          </text>
          <text
            x={midX}
            y={midY + 8}
            textAnchor="middle"
            fill="#6366f1"
            style={{ fontSize: '14px' }}
          >
            ↓
          </text>
          <text
            x={midX}
            y={midY + 22}
            textAnchor="middle"
            fontWeight="600"
            fill="#6366f1"
            style={{ fontSize: '12px' }}
          >
            {toText}
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
