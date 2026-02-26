import { useEffect, useState } from 'react'
import { Table2, Clock, Shield, CheckCircle2 } from 'lucide-react'
import { StatsCard } from '@/shared/components/ui/StatsCard'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { formatDuration } from '@/shared/lib/utils'

export function StatsBar() {
  const [elapsed, setElapsed] = useState(0)
  const processedTables = useCatalogStore((s) => s.processedTables)
  const totalTables = useCatalogStore((s) => s.totalTables)
  const tables = useCatalogStore((s) => s.tables)
  const isRunning = useCatalogStore((s) => s.isRunning)
  const startTime = useWizardStore((s) => s.startTime)

  useEffect(() => {
    if (!startTime || !isRunning) return

    const interval = setInterval(() => {
      setElapsed((Date.now() - startTime) / 1000)
    }, 100)

    return () => clearInterval(interval)
  }, [startTime, isRunning])

  const sensitivityCounts = {
    PII: 0,
    financial: 0,
    internal: 0,
    public: 0,
  }

  tables.forEach((table) => {
    sensitivityCounts[table.sensitivity]++
  })

  const highSensitivity = sensitivityCounts.PII + sensitivityCounts.financial

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatsCard
        title="Tables Cataloged"
        value={`${processedTables} / ${totalTables}`}
        icon={<Table2 className="h-4 w-4" />}
        description={totalTables > 0 ? `${Math.round((processedTables / totalTables) * 100)}% complete` : 'Waiting...'}
      />
      <StatsCard
        title="Elapsed Time"
        value={formatDuration(elapsed)}
        icon={<Clock className="h-4 w-4" />}
        description={isRunning ? 'In progress...' : 'Completed'}
      />
      <StatsCard
        title="High Sensitivity"
        value={highSensitivity}
        icon={<Shield className="h-4 w-4" />}
        description={`${sensitivityCounts.PII} PII, ${sensitivityCounts.financial} Financial`}
      />
      <StatsCard
        title="Completed"
        value={processedTables}
        icon={<CheckCircle2 className="h-4 w-4" />}
        description={`${sensitivityCounts.internal} Internal, ${sensitivityCounts.public} Public`}
      />
    </div>
  )
}
