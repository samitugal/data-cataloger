# Phase 7: Frontend - Implementation Checklist

## Plan 01: Project Setup
- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure strict TypeScript
- [ ] Install core dependencies
- [ ] Configure Tailwind CSS with custom theme
- [ ] Setup path aliases (@/*)
- [ ] Configure ESLint + Prettier
- [ ] Create directory structure

## Plan 02: Core Infrastructure
- [ ] Define API types (TableSummary, GraphData, etc.)
- [ ] Create API client with all endpoints
- [ ] Create SSE hook for real-time events
- [ ] Create Zustand store for catalog state
- [ ] Setup React Query provider
- [ ] Setup React Router with lazy loading
- [ ] Create App entry point

## Plan 03: Shared Components
- [ ] Utility functions (cn, formatDuration)
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

## Plan 04: Graph Feature
- [ ] CytoscapeGraph wrapper component
- [ ] Sensitivity-based node coloring
- [ ] Node selection and highlighting
- [ ] Hover effects with neighbor highlighting
- [ ] Animated layout on data change
- [ ] GraphContainer with toolbar
- [ ] Legend component
- [ ] useGraphData hook

## Plan 05: Tables Feature
- [ ] TableList with search and filter
- [ ] TableDetail panel
- [ ] TableCard for grid view
- [ ] TablesPage layout
- [ ] useTables hooks

## Plan 06: Catalog Feature
- [ ] CatalogingForm with database config
- [ ] ProgressPanel with table list
- [ ] useLiveCataloging hook with SSE
- [ ] LivePage layout
- [ ] Alert component

## Plan 07: Polish & Testing
- [ ] ErrorBoundary component
- [ ] Skeleton loading states
- [ ] Toast notification system
- [ ] Keyboard navigation hook
- [ ] Vitest setup
- [ ] Component unit tests
- [ ] Playwright E2E tests
- [ ] Performance hooks

## Plan 08: Docker Integration
- [ ] Frontend Dockerfile
- [ ] Nginx configuration
- [ ] Update docker-compose.yml
- [ ] Development docker-compose override
- [ ] Environment configuration
- [ ] GitHub Actions workflow

---

## Estimated Timeline

| Plan | Duration | Dependencies |
|------|----------|--------------|
| 01 - Project Setup | 1 hour | None |
| 02 - Core Infrastructure | 2 hours | Plan 01 |
| 03 - Shared Components | 2 hours | Plan 01 |
| 04 - Graph Feature | 3 hours | Plan 02, 03 |
| 05 - Tables Feature | 2 hours | Plan 02, 03 |
| 06 - Catalog Feature | 3 hours | Plan 02, 03, 04 |
| 07 - Polish & Testing | 2 hours | Plan 04, 05, 06 |
| 08 - Docker Integration | 1 hour | Plan 07 |

**Total: ~16 hours**

## Key Files to Create

```
frontend/
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── providers/
│   │   │   └── QueryProvider.tsx
│   │   ├── routes/
│   │   │   └── index.tsx
│   │   └── layouts/
│   │       └── AppLayout.tsx
│   ├── features/
│   │   ├── catalog/
│   │   │   ├── components/
│   │   │   │   ├── CatalogingForm.tsx
│   │   │   │   └── ProgressPanel.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useLiveCataloging.ts
│   │   │   ├── pages/
│   │   │   │   └── LivePage.tsx
│   │   │   └── index.ts
│   │   ├── graph/
│   │   │   ├── components/
│   │   │   │   ├── CytoscapeGraph.tsx
│   │   │   │   └── GraphContainer.tsx
│   │   │   ├── hooks/
│   │   │   │   └── useGraphData.ts
│   │   │   └── index.ts
│   │   └── tables/
│   │       ├── components/
│   │       │   ├── TableList.tsx
│   │       │   ├── TableDetail.tsx
│   │       │   └── TableCard.tsx
│   │       ├── hooks/
│   │       │   └── useTables.ts
│   │       ├── pages/
│   │       │   └── TablesPage.tsx
│   │       └── index.ts
│   ├── shared/
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Progress.tsx
│   │   │   │   └── ...
│   │   │   ├── layout/
│   │   │   │   └── Header.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── SensitivityBadge.tsx
│   │   │   └── Skeleton.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts
│   │   │   ├── useKeyboardNavigation.ts
│   │   │   └── useDebouncedValue.ts
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── stores/
│   │   │   └── catalogStore.ts
│   │   └── types/
│   │       └── api.ts
│   └── index.css
├── public/
├── e2e/
│   └── live-cataloging.spec.ts
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
├── vitest.config.ts
├── nginx.conf
├── Dockerfile
└── Dockerfile.dev
```
