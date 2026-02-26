import { Link, useLocation } from 'react-router-dom'
import { Database, Play, Table2 } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

const navItems = [
  { path: '/', label: 'Tables', icon: Table2 },
  { path: '/live', label: 'Live Catalog', icon: Play },
]

export function Header() {
  const location = useLocation()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link to="/" className="flex items-center space-x-2 mr-6">
          <Database className="h-6 w-6 text-primary" />
          <span className="font-bold">Data Cataloger</span>
        </Link>

        <nav className="flex items-center space-x-6 text-sm font-medium">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={cn(
                'flex items-center space-x-1 transition-colors hover:text-foreground/80',
                location.pathname === path ? 'text-foreground' : 'text-foreground/60'
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
