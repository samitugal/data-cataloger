import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { AppLayout } from '@/app/layouts/AppLayout'
import { LoadingSpinner } from '@/shared/components/ui/LoadingSpinner'

const WizardPage = lazy(() => import('@/features/catalog/pages/WizardPage'))

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingSpinner size="lg" />}>
            <WizardPage />
          </Suspense>
        ),
      },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
