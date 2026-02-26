# Plan 07-03: Shared Components

## Objective

Build reusable UI component library using shadcn/ui patterns and Tailwind CSS.

## Tasks

### 3.1 Utility Functions

**File:** `src/shared/lib/utils.ts`

```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs.toFixed(0)}s`
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}
```

### 3.2 Base Components

**File:** `src/shared/components/ui/Button.tsx`

```typescript
import { forwardRef, ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/shared/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'
```

**File:** `src/shared/components/ui/Card.tsx`

```typescript
import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)}
      {...props}
    />
  )
)
Card.displayName = 'Card'

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
  )
)
CardHeader.displayName = 'CardHeader'

export const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3 ref={ref} className={cn('text-2xl font-semibold leading-none tracking-tight', className)} {...props} />
  )
)
CardTitle.displayName = 'CardTitle'

export const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('p-6 pt-0', className)} {...props} />
  )
)
CardContent.displayName = 'CardContent'
```

**File:** `src/shared/components/ui/Badge.tsx`

```typescript
import { HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/shared/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground',
        secondary: 'bg-secondary text-secondary-foreground',
        destructive: 'bg-destructive text-destructive-foreground',
        outline: 'border text-foreground',
        pii: 'bg-sensitivity-pii text-white',
        financial: 'bg-sensitivity-financial text-white',
        internal: 'bg-sensitivity-internal text-white',
        public: 'bg-sensitivity-public text-white',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}
```

### 3.3 Input Components

**File:** `src/shared/components/ui/Input.tsx`

```typescript
import { forwardRef, InputHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background',
          'file:border-0 file:bg-transparent file:text-sm file:font-medium',
          'placeholder:text-muted-foreground',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = 'Input'
```

**File:** `src/shared/components/ui/SearchInput.tsx`

```typescript
import { forwardRef, InputHTMLAttributes } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

export interface SearchInputProps extends InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, value, onClear, ...props }, ref) => {
    return (
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          className={cn(
            'flex h-10 w-full rounded-md border border-input bg-background pl-10 pr-10 py-2 text-sm',
            'placeholder:text-muted-foreground',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
            className
          )}
          ref={ref}
          value={value}
          {...props}
        />
        {value && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    )
  }
)
SearchInput.displayName = 'SearchInput'
```

### 3.4 Feedback Components

**File:** `src/shared/components/ui/Progress.tsx`

```typescript
import { HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/utils'

interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number
  max?: number
  showLabel?: boolean
}

export function Progress({ value, max = 100, showLabel, className, ...props }: ProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100))

  return (
    <div className={cn('space-y-1', className)} {...props}>
      {showLabel && (
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Progress</span>
          <span>{Math.round(percentage)}%</span>
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full bg-primary transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
```

**File:** `src/shared/components/ui/LoadingSpinner.tsx`

```typescript
import { cn } from '@/shared/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <div
        className={cn(
          'animate-spin rounded-full border-2 border-current border-t-transparent text-primary',
          sizeClasses[size]
        )}
      />
    </div>
  )
}
```

**File:** `src/shared/components/ui/EmptyState.tsx`

```typescript
import { ReactNode } from 'react'
import { cn } from '@/shared/lib/utils'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
```

### 3.5 Layout Components

**File:** `src/shared/components/layout/Header.tsx`

```typescript
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
```

**File:** `src/app/layouts/AppLayout.tsx`

```typescript
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
```

### 3.6 Sensitivity Badge Component

**File:** `src/shared/components/SensitivityBadge.tsx`

```typescript
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
  return (
    <Badge variant={sensitivity} className={className}>
      {sensitivityLabels[sensitivity]}
    </Badge>
  )
}
```

### 3.7 Component Index

**File:** `src/shared/components/ui/index.ts`

```typescript
export * from './Badge'
export * from './Button'
export * from './Card'
export * from './EmptyState'
export * from './Input'
export * from './LoadingSpinner'
export * from './Progress'
export * from './SearchInput'
```

## Verification

```typescript
// Visual test all components
import { Button, Card, Badge, Progress, LoadingSpinner } from '@/shared/components/ui'

<Button variant="default">Click me</Button>
<Badge variant="pii">PII</Badge>
<Progress value={50} showLabel />
<LoadingSpinner size="lg" />
```

## Deliverables

- [ ] Utility functions (cn, formatDuration, truncate)
- [ ] Button with variants
- [ ] Card components
- [ ] Badge with sensitivity variants
- [ ] Input and SearchInput
- [ ] Progress bar
- [ ] LoadingSpinner
- [ ] EmptyState
- [ ] Header with navigation
- [ ] AppLayout
- [ ] SensitivityBadge
- [ ] Component index exports
