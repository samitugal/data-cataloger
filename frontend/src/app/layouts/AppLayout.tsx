import { Outlet } from 'react-router-dom'
import { Header } from '@/shared/components/layout/Header'

export function AppLayout() {
  return (
    <div className="relative min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container py-6">
        <Outlet />
      </main>
    </div>
  )
}
