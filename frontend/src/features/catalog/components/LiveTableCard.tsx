import { useState, useRef } from 'react'
import { Database, Key, Lock, Shield, Globe, DollarSign } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { TableDetail, Sensitivity } from '@/shared/types/api'

interface LiveTableCardProps {
  table: TableDetail
  index: number
  isSelected?: boolean
  onClick?: () => void
  id?: string
}

const sensitivityConfig: Record<Sensitivity, { color: string; bg: string; border: string; icon: typeof Lock }> = {
  PII: { color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', icon: Lock },
  financial: { color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', icon: DollarSign },
  internal: { color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200', icon: Shield },
  public: { color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', icon: Globe },
}

export function LiveTableCard({ table, index, isSelected, onClick, id }: LiveTableCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const cardRef = useRef<HTMLDivElement>(null)
  const config = sensitivityConfig[table.sensitivity]
  const Icon = config.icon

  return (
    <div
      ref={cardRef}
      id={id}
      data-table={table.name}
      className={cn(
        'relative w-[180px] rounded-lg border-2 cursor-pointer transition-all duration-300',
        'shadow-md hover:shadow-xl',
        config.bg, config.border,
        isSelected && 'ring-2 ring-primary ring-offset-2',
        isHovered && 'scale-105 z-20'
      )}
      style={{
        animation: `popIn 0.4s ease-out ${index * 80}ms backwards`,
      }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className={cn(
        'flex items-center gap-2 px-3 py-2 border-b',
        config.border
      )}>
        <Database className={cn('h-4 w-4 flex-shrink-0', config.color)} />
        <span className="font-semibold text-sm truncate flex-1 text-gray-800">{table.name}</span>
        <Icon className={cn('h-4 w-4 flex-shrink-0', config.color)} />
      </div>

      {/* Foreign Keys Preview */}
      <div className="px-3 py-2 space-y-1 min-h-[60px]">
        {table.foreign_keys.slice(0, 3).map((fk, i) => (
          <div key={i} className="flex items-center gap-1 text-[11px] text-gray-600">
            <Key className="h-3 w-3 text-amber-500 flex-shrink-0" />
            <span className="truncate">{fk.column}</span>
            <span className="text-gray-400">→</span>
            <span className="truncate text-blue-600 font-medium">{fk.references_table}</span>
          </div>
        ))}
        {table.foreign_keys.length === 0 && (
          <div className="text-[11px] text-gray-400 italic">No foreign keys</div>
        )}
        {table.foreign_keys.length > 3 && (
          <div className="text-[11px] text-gray-400">
            +{table.foreign_keys.length - 3} more
          </div>
        )}
      </div>

      {/* Sensitivity Badge */}
      <div className="px-3 pb-2">
        <span className={cn(
          'text-[10px] font-bold px-2 py-1 rounded uppercase inline-block',
          config.bg, config.color,
          'border', config.border
        )}>
          {table.sensitivity}
        </span>
      </div>

      {/* Popup Detail on Hover */}
      {isHovered && (
        <div
          className={cn(
            'absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-[280px] z-50',
            'bg-white rounded-lg shadow-2xl border-2 p-4',
            'animate-in fade-in zoom-in-95 slide-in-from-bottom-2 duration-200',
            config.border
          )}
        >
          {/* Arrow */}
          <div className={cn(
            'absolute left-1/2 -translate-x-1/2 -bottom-2 w-4 h-4 rotate-45',
            'bg-white border-r-2 border-b-2',
            config.border
          )} />

          <div className="flex items-center gap-2 mb-2">
            <Database className={cn('h-5 w-5', config.color)} />
            <span className="font-bold text-base text-gray-800">{table.name}</span>
            <span className={cn(
              'text-[10px] font-bold px-2 py-0.5 rounded uppercase ml-auto',
              config.bg, config.color
            )}>
              {table.sensitivity}
            </span>
          </div>

          <p className="text-sm text-gray-600 leading-relaxed mb-3">
            {table.description}
          </p>

          {table.foreign_keys.length > 0 && (
            <div className="border-t pt-2 mt-2">
              <p className="text-xs font-semibold text-gray-500 mb-1">Foreign Keys:</p>
              <div className="space-y-1">
                {table.foreign_keys.map((fk, i) => (
                  <div key={i} className="flex items-center gap-1 text-xs text-gray-600">
                    <Key className="h-3 w-3 text-amber-500" />
                    <span className="font-medium">{fk.column}</span>
                    <span className="text-gray-400">→</span>
                    <span className="text-blue-600">{fk.references_table}.{fk.references_column}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
