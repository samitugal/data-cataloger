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

  // Determine best connection points based on relative positions
  const fromCenterX = from.x + cardWidth / 2
  const fromCenterY = from.y + cardHeight / 2
  const toCenterX = to.x + cardWidth / 2
  const toCenterY = to.y + cardHeight / 2

  const dx = toCenterX - fromCenterX
  const dy = toCenterY - fromCenterY

  // Choose exit/entry sides based on relative position
  let startX: number, startY: number, endX: number, endY: number
  let midX: number, midY: number
  let pathType: 'horizontal-first' | 'vertical-first'

  if (Math.abs(dx) > Math.abs(dy)) {
    // Horizontal dominant - exit from sides
    if (dx > 0) {
      // Target is to the right
      startX = from.x + cardWidth
      startY = fromCenterY
      endX = to.x
      endY = toCenterY
    } else {
      // Target is to the left
      startX = from.x
      startY = fromCenterY
      endX = to.x + cardWidth
      endY = toCenterY
    }
    pathType = 'horizontal-first'
    midX = (startX + endX) / 2
    midY = startY
  } else {
    // Vertical dominant - exit from top/bottom
    if (dy > 0) {
      // Target is below
      startX = fromCenterX
      startY = from.y + cardHeight
      endX = toCenterX
      endY = to.y
    } else {
      // Target is above
      startX = fromCenterX
      startY = from.y
      endX = toCenterX
      endY = to.y + cardHeight
    }
    pathType = 'vertical-first'
    midX = startX
    midY = (startY + endY) / 2
  }

  // Create orthogonal path (90 degree turns only)
  let path: string
  if (pathType === 'horizontal-first') {
    // Go horizontal first, then vertical
    const turnX = (startX + endX) / 2
    path = `M ${startX} ${startY} L ${turnX} ${startY} L ${turnX} ${endY} L ${endX} ${endY}`
    midX = turnX
    midY = (startY + endY) / 2
  } else {
    // Go vertical first, then horizontal
    const turnY = (startY + endY) / 2
    path = `M ${startX} ${startY} L ${startX} ${turnY} L ${endX} ${turnY} L ${endX} ${endY}`
    midX = (startX + endX) / 2
    midY = turnY
  }

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
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth="16"
      />

      {/* Visible line */}
      <path
        d={path}
        fill="none"
        stroke={isHovered ? '#6366f1' : '#94a3b8'}
        strokeWidth={isHovered ? 3 : 2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className="transition-all duration-200"
      />

      {/* Arrow head at end */}
      <circle
        cx={endX}
        cy={endY}
        r={isHovered ? 6 : 4}
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
