import { useState } from 'react'
import { Database, Server, Key, User, ArrowRight } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/Card'
import { useWizardStore } from '@/shared/stores/wizardStore'
import { useCatalogStore } from '@/shared/stores/catalogStore'
import { api } from '@/shared/api/client'
import type { CatalogingRequest } from '@/shared/types/api'

export function ConnectionStep() {
  const dbConfig = useWizardStore((s) => s.dbConfig)
  const setDbConfig = useWizardStore((s) => s.setDbConfig)
  const startCataloging = useWizardStore((s) => s.startCataloging)
  const catalogStoreStart = useCatalogStore((s) => s.startCataloging)

  const [config, setConfig] = useState<CatalogingRequest>(
    dbConfig || {
      host: 'postgres',
      port: 5432,
      database: 'northwind',
      username: 'postgres',
      password: 'postgres',
      db_type: 'postgresql',
    }
  )
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const response = await api.startCataloging(config)

      if (response.status === 'started') {
        setDbConfig(config)
        catalogStoreStart(response.total_tables)
        startCataloging()
      } else {
        setError(response.message || 'Failed to start cataloging')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Database className="h-8 w-8 text-primary" />
        </div>
        <h1 className="text-2xl font-bold">Connect to Database</h1>
        <p className="text-muted-foreground mt-2">
          Enter your database credentials to start cataloging
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Database Connection</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Server className="h-4 w-4 text-muted-foreground" />
                  Host
                </label>
                <Input
                  value={config.host}
                  onChange={(e) => setConfig({ ...config, host: e.target.value })}
                  placeholder="localhost"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Port</label>
                <Input
                  type="number"
                  value={config.port}
                  onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) || 5432 })}
                  placeholder="5432"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4 text-muted-foreground" />
                Database Name
              </label>
              <Input
                value={config.database}
                onChange={(e) => setConfig({ ...config, database: e.target.value })}
                placeholder="northwind"
                disabled={isLoading}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  Username
                </label>
                <Input
                  value={config.username}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                  placeholder="postgres"
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Key className="h-4 w-4 text-muted-foreground" />
                  Password
                </label>
                <Input
                  type="password"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                  placeholder="••••••••"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Database Type</label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="db_type"
                    value="postgresql"
                    checked={config.db_type === 'postgresql'}
                    onChange={() => setConfig({ ...config, db_type: 'postgresql' })}
                    disabled={isLoading}
                    className="text-primary"
                  />
                  <span className="text-sm">PostgreSQL</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="db_type"
                    value="mysql"
                    checked={config.db_type === 'mysql'}
                    onChange={() => setConfig({ ...config, db_type: 'mysql' })}
                    disabled={isLoading}
                    className="text-primary"
                  />
                  <span className="text-sm">MySQL</span>
                </label>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                'Connecting...'
              ) : (
                <>
                  Start Cataloging
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="text-center text-xs text-muted-foreground mt-4">
        Your credentials are used only for this session and are not stored.
      </p>
    </div>
  )
}
