# Plan 07-01: Project Setup

## Objective

Initialize React + TypeScript project with modern tooling and configuration.

## Prerequisites

- Node.js 20+
- pnpm (preferred) or npm

## Tasks

### 1.1 Initialize Vite Project

```bash
cd data-cataloger
pnpm create vite frontend --template react-ts
cd frontend
pnpm install
```

**Output:**
- `frontend/` directory with Vite + React + TypeScript template

### 1.2 Configure TypeScript (Strict)

**File:** `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### 1.3 Install Core Dependencies

```bash
# UI & Styling
pnpm add tailwindcss postcss autoprefixer
pnpm add -D @tailwindcss/typography @tailwindcss/forms

# Component Library (shadcn/ui prerequisites)
pnpm add class-variance-authority clsx tailwind-merge
pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu
pnpm add @radix-ui/react-tooltip @radix-ui/react-scroll-area

# Icons
pnpm add lucide-react

# State Management
pnpm add zustand immer

# Data Fetching
pnpm add @tanstack/react-query

# Routing
pnpm add react-router-dom

# Graph Visualization
pnpm add cytoscape
pnpm add -D @types/cytoscape

# Utilities
pnpm add date-fns
```

### 1.4 Configure Tailwind CSS

**File:** `frontend/tailwind.config.js`

```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        // Sensitivity colors
        sensitivity: {
          pii: '#ef4444',
          financial: '#f59e0b',
          internal: '#3b82f6',
          public: '#22c55e',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
}
```

**File:** `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 238 73% 67%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 238 73% 67%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

### 1.5 Configure Path Aliases

**File:** `frontend/vite.config.ts`

```ts
import path from 'path'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### 1.6 Setup ESLint & Prettier

```bash
pnpm add -D eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser
pnpm add -D eslint-plugin-react eslint-plugin-react-hooks
pnpm add -D prettier eslint-config-prettier eslint-plugin-prettier
```

**File:** `frontend/.eslintrc.cjs`

```js
module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
    'prettier',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json', './tsconfig.node.json'],
    tsconfigRootDir: __dirname,
  },
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
  settings: {
    react: { version: 'detect' },
  },
}
```

**File:** `frontend/.prettierrc`

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100
}
```

### 1.7 Create Directory Structure

```bash
mkdir -p src/{app,features,shared}
mkdir -p src/app/{providers,routes}
mkdir -p src/features/{catalog,graph,tables}
mkdir -p src/shared/{api,components,hooks,types,lib}
```

**Final Structure:**
```
frontend/
├── src/
│   ├── app/
│   │   ├── providers/      # Context providers
│   │   ├── routes/         # Route definitions
│   │   ├── App.tsx         # Root component
│   │   └── main.tsx        # Entry point
│   ├── features/
│   │   ├── catalog/        # Cataloging feature
│   │   ├── graph/          # Graph visualization
│   │   └── tables/         # Table browsing
│   ├── shared/
│   │   ├── api/            # API client, types
│   │   ├── components/     # Reusable UI
│   │   ├── hooks/          # Custom hooks
│   │   ├── lib/            # Utilities
│   │   └── types/          # Shared types
│   └── index.css
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── .eslintrc.cjs
```

## Verification

```bash
cd frontend
pnpm dev
# Should start on http://localhost:3000
# Should proxy /api/* to http://localhost:8000
```

## Deliverables

- [ ] Vite project initialized
- [ ] TypeScript strict mode configured
- [ ] Tailwind CSS with custom theme
- [ ] Path aliases working (@/*)
- [ ] ESLint + Prettier configured
- [ ] Directory structure created
- [ ] Dev server running with API proxy
