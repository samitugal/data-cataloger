import { useState } from 'react'
import { Database, Key, Lock, Shield, Globe, DollarSign } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { TableDetail, Sensitivity } from '@/shared/types/api'

interface LiveTableCardProps {
  table: TableDetail
  index: number
  isSelected?: boolean
  onClick?: () => void
}

const sensitivityConfig: Record<Sensitivity, { color: string; bg: string; icon: typeof Lock }> = {
  PII: { color: 'text-red-500', bg: 'bg-red-500/10 border-red-500/30', icon: Lock },
  financial: { color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/30', icon: DollarSign },
  internal: { color: 'text-blue-500', bg: 'bg-blue-500/10 border-blue-500/30', icon: Shield },
  public: { color: 'text-green-500', bg: 'bg-green-500/10 border-green-500/30', icon: Globe },
}

export function LiveTableCard({ table, index, isSelected, onClick }: LiveTableCardProps) {
  const [isHovered, setIsHovered] = useState(false)
  const config = sensitivityConfig[table.sensitivity]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'relative w-[200px] h-[140px] rounded-xl border-2 cursor-pointer transition-all duration-300',
        'bg-card/80 backdrop-blur-sm shadow-lg hover:shadow-xl',
        'animate-in fade-in slide-in-from-bottom-4',
        config.bg,
        isSelected && 'ring-2 ring-primary ring-offset-2',
        isHovered && 'scale-105 z-10'
      )}
      style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'backwards' }}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-border/50">
        <Database className={cn('h-4 w-4', config.color)} />
        <span className="font-semibold text-sm truncate flex-1">{table.name}</span>
        <Icon className={cn('h-4 w-4', config.color)} />
      </div>

      {/* Columns Preview */}
      <div className="p-3 space-y-1">
        {table.foreign_keys.slice(0, 3).map((fk, i) => (
          <div key={i} className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Key className="h-3 w-3 text-amber-500" />
            <span className="truncate">{fk.column}</span>
            <span className="text-muted-foreground/50">→</span>
            <span className="truncate text-primary/70">{fk.references_table}</span>
          </div>
        ))}
        {table.foreign_keys.length === 0 && (
          <div className="text-xs text-muted-foreground/50 italic">No foreign keys</div>
        )}
        {table.foreign_keys.length > 3 && (
          <div className="text-xs text-muted-foreground/50">
            +{table.foreign_keys.length - 3} more
          </div>
        )}
      </div>

      {/* Sensitivity Badge */}
      <div className="absolute bottom-2 right-2">
        <span className={cn(
          'text-[10px] font-medium px-2 py-0.5 rounded-full uppercase',
          config.bg, config.color
        )}>
          {table.sensitivity}
        </span>
      </div>

      {/* Hover Detail Overlay */}
      {isHovered && (
        <div className={cn(
          'absolute inset-0 rounded-xl p-3 bg-popover/95 backdrop-blur-md border-2',
          'animate-in fade-in zoom-in-95 duration-200',
          config.bg
        )}>
          <div className="flex items-center gap-2 mb-2">
            <Database className={cn('h-4 w-4', config.color)} />
            <span className="font-bold text-sm">{table.name}</span>
          </div>
          <p className="text-xs text-muted-foreground line-clamp-4 leading-relaxed">
            {table.description}
          </p>
          <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
            <span className={cn(
              'text-[10px] font-medium px-2 py-0.5 rounded-full uppercase',
              config.bg, config.color
            )}>
              {table.sensitivity}
            </span>
            <span className="text-[10px] text-muted-foreground">
              {table.foreign_keys.length} FK{table.foreign_keys.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
