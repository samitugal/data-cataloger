import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { AppLayout } from '@/app/layouts/AppLayout'
import { LoadingSpinner } from '@/shared/components/ui/LoadingSpinner'

const TablesPage = lazy(() => import('@/features/tables/pages/TablesPage'))
const LivePage = lazy(() => import('@/features/catalog/pages/LivePage'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingSpinner size="lg" />}>
            <TablesPage />
          </Suspense>
        ),
      },
      {
        path: 'live',
        element: (
          <Suspense fallback={<LoadingSpinner size="lg" />}>
            <LivePage />
          </Suspense>
        ),
      },
      {
        path: 'tables',
        element: (
          <Suspense fallback={<LoadingSpinner size="lg" />}>
            <TablesPage />
          </Suspense>
        ),
      },
      {
        path: 'tables/:name',
        element: (
          <Suspense fallback={<LoadingSpinner size="lg" />}>
            <TablesPage />
          </Suspense>
        ),
      },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
