import { QueryProvider } from './providers/QueryProvider'
import { AppRouter } from './routes'

export function App() {
  return (
    <QueryProvider>
      <AppRouter />
    </QueryProvider>
  )
}
