# Plan 07-08: Docker Integration

## Objective

Containerize frontend and integrate with existing Docker Compose stack.

## Tasks

### 8.1 Frontend Dockerfile

**File:** `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy source
COPY . .

# Build
RUN pnpm build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 8.2 Nginx Configuration

**File:** `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    gzip_min_length 1000;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api/ {
        proxy_pass http://web:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        
        # SSE support
        proxy_buffering off;
        proxy_read_timeout 86400s;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 8.3 Update Docker Compose

**File:** `docker-compose.yml` (updated)

```yaml
services:
  # Neo4j Graph Database
  neo4j:
    image: neo4j:5-community
    container_name: data-cataloger-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:7474"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 40s
    networks:
      - cataloger-net

  # PostgreSQL Sample Database
  postgres:
    image: postgres:15
    container_name: data-cataloger-postgres
    ports:
      - "5433:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: northwind
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/init-db:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d northwind"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - cataloger-net

  # Backend API
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: data-cataloger-web
    ports:
      - "8000:8000"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: neo4j
      NEO4J_PASSWORD: password
      DATABASE_NAME: northwind
      PYTHONUNBUFFERED: "1"
    depends_on:
      neo4j:
        condition: service_healthy
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
    networks:
      - cataloger-net

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: data-cataloger-frontend
    ports:
      - "3000:80"
    depends_on:
      web:
        condition: service_healthy
    networks:
      - cataloger-net

volumes:
  neo4j_data:
  neo4j_logs:
  postgres_data:

networks:
  cataloger-net:
    driver: bridge
```

### 8.4 Development Docker Compose Override

**File:** `docker-compose.dev.yml`

```yaml
# Development overrides - use with: docker compose -f docker-compose.yml -f docker-compose.dev.yml up
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend/src:/app/src:ro
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
```

**File:** `frontend/Dockerfile.dev`

```dockerfile
FROM node:20-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
```

### 8.5 Environment Configuration

**File:** `frontend/.env.example`

```env
# API URL (for development)
VITE_API_URL=http://localhost:8000

# Feature flags
VITE_ENABLE_DEVTOOLS=true
```

**File:** `frontend/src/shared/config/env.ts`

```typescript
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || '',
  enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true',
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
} as const
```

### 8.6 Build Scripts

**File:** `frontend/package.json` (scripts section)

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint . --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "typecheck": "tsc --noEmit"
  }
}
```

### 8.7 CI/CD GitHub Actions

**File:** `.github/workflows/frontend.yml`

```yaml
name: Frontend CI

on:
  push:
    paths:
      - 'frontend/**'
  pull_request:
    paths:
      - 'frontend/**'

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
          cache-dependency-path: frontend/pnpm-lock.yaml

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Type check
        run: pnpm typecheck

      - name: Test
        run: pnpm test --run

      - name: Build
        run: pnpm build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: frontend-dist
          path: frontend/dist
```

## Verification

```bash
# Build and run full stack
docker compose build
docker compose up -d

# Check services
docker compose ps

# Access frontend
open http://localhost:3000

# Access API directly
curl http://localhost:8000/health

# View logs
docker compose logs -f frontend
```

## Deliverables

- [ ] Frontend Dockerfile (multi-stage)
- [ ] Nginx configuration with API proxy
- [ ] Updated docker-compose.yml
- [ ] Development docker-compose override
- [ ] Environment configuration
- [ ] Build scripts
- [ ] GitHub Actions workflow
