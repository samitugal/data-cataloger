import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/utils'

interface StatsCardProps {
  title: string
  value: string | number
  icon?: ReactNode
  description?: string
  trend?: 'up' | 'down' | 'neutral'
  className?: string
}

export function StatsCard({ title, value, icon, description, className }: StatsCardProps) {
  return (
    <div className={cn('rounded-lg border bg-card p-4', className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </div>
      <div className="mt-2">
        <p className="text-2xl font-bold">{value}</p>
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </div>
    </div>
  )
}
