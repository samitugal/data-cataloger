.PHONY: install dev build test lint format clean docker-up docker-down docker-build frontend-install frontend-dev frontend-build all

install:
	uv sync

dev:
	@if [ "$(FORCE)" = "1" ] || [ "$(force)" = "1" ]; then \
		lsof -ti:8000 | xargs kill -9 2>/dev/null || true; \
		sleep 1; \
	fi
	uv run uvicorn data_cataloger.web.app:app --reload --host 0.0.0.0 --port 8000

dev-force:
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	uv run uvicorn data_cataloger.web.app:app --reload --host 0.0.0.0 --port 8000

build:
	uv build

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src/data_cataloger --cov-report=html

lint:
	uv run ruff check src/ tests/
	uv run mypy src/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -type d -name __pycache__ -exec rm -rf {} +

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

frontend-lint:
	cd frontend && npm run lint

all: install frontend-install

mcp-server:
	uv run python -m data_cataloger.mcp

dev-all:
	make -j2 dev frontend-dev
