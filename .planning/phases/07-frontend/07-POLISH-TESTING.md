# Plan 07-07: Polish & Testing

## Objective

Add error handling, loading states, accessibility, and tests.

## Tasks

### 7.1 Error Boundary

**File:** `src/shared/components/ErrorBoundary.tsx`

```typescript
import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/shared/components/ui/Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
          <p className="text-muted-foreground mb-4 max-w-md">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Reload page
          </Button>
        </div>
      )
    }

    return this.props.children
  }
}
```

### 7.2 Loading States

**File:** `src/shared/components/Skeleton.tsx`

```typescript
import { cn } from '@/shared/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div className={cn('animate-pulse rounded-md bg-muted', className)} />
  )
}

export function TableListSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function GraphSkeleton() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="space-y-4 text-center">
        <Skeleton className="h-32 w-32 rounded-full mx-auto" />
        <Skeleton className="h-4 w-48 mx-auto" />
      </div>
    </div>
  )
}

export function DetailSkeleton() {
  return (
    <div className="p-4 space-y-4">
      <div className="space-y-2">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-4 w-1/4" />
      </div>
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
  )
}
```

### 7.3 Toast Notifications

**File:** `src/shared/components/Toast.tsx`

```typescript
import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

type ToastType = 'success' | 'error' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (type: ToastType, message: string) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, type, message }])

    // Auto remove after 5 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 5000)
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

function ToastContainer({
  toasts,
  onRemove,
}: {
  toasts: Toast[]
  onRemove: (id: string) => void
}) {
  if (toasts.length === 0) return null

  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    info: Info,
  }

  const colors = {
    success: 'bg-green-500',
    error: 'bg-destructive',
    info: 'bg-primary',
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => {
        const Icon = icons[toast.type]
        return (
          <div
            key={toast.id}
            className={cn(
              'flex items-center gap-2 px-4 py-3 rounded-lg text-white shadow-lg',
              'animate-in slide-in-from-right-full',
              colors[toast.type]
            )}
          >
            <Icon className="h-5 w-5" />
            <span className="flex-1">{toast.message}</span>
            <button onClick={() => onRemove(toast.id)} className="hover:opacity-80">
              <X className="h-4 w-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
```

### 7.4 Accessibility Improvements

**File:** `src/shared/hooks/useKeyboardNavigation.ts`

```typescript
import { useEffect, useCallback } from 'react'

interface UseKeyboardNavigationOptions {
  onEscape?: () => void
  onEnter?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  enabled?: boolean
}

export function useKeyboardNavigation({
  onEscape,
  onEnter,
  onArrowUp,
  onArrowDown,
  enabled = true,
}: UseKeyboardNavigationOptions) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return

      switch (e.key) {
        case 'Escape':
          onEscape?.()
          break
        case 'Enter':
          onEnter?.()
          break
        case 'ArrowUp':
          e.preventDefault()
          onArrowUp?.()
          break
        case 'ArrowDown':
          e.preventDefault()
          onArrowDown?.()
          break
      }
    },
    [enabled, onEscape, onEnter, onArrowUp, onArrowDown]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])
}
```

### 7.5 Unit Tests Setup

```bash
pnpm add -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

**File:** `vitest.config.ts`

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**File:** `src/test/setup.ts`

```typescript
import '@testing-library/jest-dom'
```

### 7.6 Component Tests

**File:** `src/shared/components/ui/__tests__/Button.test.tsx`

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from '../Button'

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('handles click events', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click me</Button>)
    fireEvent.click(screen.getByText('Click me'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('can be disabled', () => {
    render(<Button disabled>Click me</Button>)
    expect(screen.getByText('Click me')).toBeDisabled()
  })

  it('applies variant classes', () => {
    render(<Button variant="destructive">Delete</Button>)
    expect(screen.getByText('Delete')).toHaveClass('bg-destructive')
  })
})
```

**File:** `src/features/catalog/hooks/__tests__/useLiveCataloging.test.ts`

```typescript
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useLiveCataloging } from '../useLiveCataloging'

// Mock API
vi.mock('@/shared/api/client', () => ({
  api: {
    startCataloging: vi.fn(),
    resetCataloging: vi.fn(),
  },
}))

describe('useLiveCataloging', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('starts in idle state', () => {
    const { result } = renderHook(() => useLiveCataloging())
    expect(result.current.isRunning).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('handles start errors', async () => {
    const { api } = await import('@/shared/api/client')
    vi.mocked(api.startCataloging).mockRejectedValue(new Error('Connection failed'))

    const { result } = renderHook(() => useLiveCataloging())

    await act(async () => {
      await result.current.start({
        host: 'localhost',
        port: 5432,
        database: 'test',
        username: 'user',
        password: 'pass',
        db_type: 'postgresql',
      })
    })

    expect(result.current.error).toBe('Connection failed')
  })
})
```

### 7.7 E2E Tests with Playwright

```bash
pnpm add -D @playwright/test
npx playwright install
```

**File:** `e2e/live-cataloging.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Live Cataloging', () => {
  test('should show cataloging form', async ({ page }) => {
    await page.goto('/live')
    await expect(page.getByText('Database Connection')).toBeVisible()
    await expect(page.getByRole('button', { name: /start cataloging/i })).toBeVisible()
  })

  test('should start cataloging and show progress', async ({ page }) => {
    await page.goto('/live')

    // Fill form
    await page.getByLabel('Host').fill('postgres')
    await page.getByLabel('Database').fill('northwind')

    // Start cataloging
    await page.getByRole('button', { name: /start cataloging/i }).click()

    // Should show progress
    await expect(page.getByText(/processing/i)).toBeVisible({ timeout: 10000 })
  })

  test('should display tables in graph as they are cataloged', async ({ page }) => {
    await page.goto('/live')

    // Start cataloging
    await page.getByRole('button', { name: /start cataloging/i }).click()

    // Wait for first table to appear in graph
    await expect(page.locator('#graph-container canvas')).toBeVisible({ timeout: 30000 })
  })
})
```

### 7.8 Performance Optimizations

**File:** `src/shared/hooks/useDebouncedValue.ts`

```typescript
import { useState, useEffect } from 'react'

export function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}
```

**File:** `src/shared/hooks/useThrottledCallback.ts`

```typescript
import { useCallback, useRef } from 'react'

export function useThrottledCallback<T extends (...args: unknown[]) => void>(
  callback: T,
  delay: number
): T {
  const lastCall = useRef(0)

  return useCallback(
    ((...args) => {
      const now = Date.now()
      if (now - lastCall.current >= delay) {
        lastCall.current = now
        callback(...args)
      }
    }) as T,
    [callback, delay]
  )
}
```

## Verification

```bash
# Run unit tests
pnpm test

# Run e2e tests
pnpm exec playwright test

# Check bundle size
pnpm build && npx vite-bundle-visualizer
```

## Deliverables

- [ ] ErrorBoundary component
- [ ] Skeleton loading states
- [ ] Toast notification system
- [ ] Keyboard navigation hook
- [ ] Vitest setup with React Testing Library
- [ ] Component unit tests
- [ ] Playwright E2E tests
- [ ] Performance hooks (debounce, throttle)
- [ ] Bundle size < 200KB gzipped
