import { useState } from 'react'
import { Database, Play, RotateCcw } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import type { CatalogingRequest } from '@/shared/types/api'

interface CatalogingFormProps {
  onStart: (config: CatalogingRequest) => void
  onReset: () => void
  isRunning: boolean
  disabled?: boolean
}

const defaultConfig: CatalogingRequest = {
  host: 'postgres',
  port: 5432,
  database: 'northwind',
  username: 'postgres',
  password: 'postgres',
  db_type: 'postgresql',
}

export function CatalogingForm({ onStart, onReset, isRunning, disabled }: CatalogingFormProps) {
  const [config, setConfig] = useState<CatalogingRequest>(defaultConfig)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStart(config)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="h-5 w-5" />
          Database Connection
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Host</label>
              <Input
                value={config.host}
                onChange={(e) => setConfig({ ...config, host: e.target.value })}
                disabled={isRunning || disabled}
              />
            </div>
            <div>
              <label className="text-sm font-medium">Port</label>
              <Input
                type="number"
                value={config.port}
                onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) })}
                disabled={isRunning || disabled}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">Database</label>
            <Input
              value={config.database}
              onChange={(e) => setConfig({ ...config, database: e.target.value })}
              disabled={isRunning || disabled}
            />
          </div>

          {showAdvanced && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium">Username</label>
                <Input
                  value={config.username}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                  disabled={isRunning || disabled}
                />
              </div>
              <div>
                <label className="text-sm font-medium">Password</label>
                <Input
                  type="password"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                  disabled={isRunning || disabled}
                />
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            {showAdvanced ? 'Hide' : 'Show'} advanced options
          </button>

          <div className="flex gap-2 pt-2">
            <Button type="submit" disabled={isRunning || disabled} className="flex-1">
              <Play className="h-4 w-4 mr-2" />
              {isRunning ? 'Cataloging...' : 'Start Cataloging'}
            </Button>
            <Button type="button" variant="outline" onClick={onReset} disabled={isRunning}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
