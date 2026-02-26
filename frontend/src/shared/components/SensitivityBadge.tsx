import { Badge } from '@/shared/components/ui/Badge'
import type { Sensitivity } from '@/shared/types/api'

interface SensitivityBadgeProps {
  sensitivity: Sensitivity
  className?: string
}

const sensitivityLabels: Record<Sensitivity, string> = {
  PII: 'PII',
  financial: 'Financial',
  internal: 'Internal',
  public: 'Public',
}

export function SensitivityBadge({ sensitivity, className }: SensitivityBadgeProps) {
  const variant = sensitivity === 'PII' ? 'pii' : sensitivity
  return (
    <Badge variant={variant} className={className}>
      {sensitivityLabels[sensitivity]}
    </Badge>
  )
}
