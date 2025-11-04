# Torale Task Runner
# Usage: just <command>
# Run 'just --list' to see all available commands

# Default recipe (runs when you just type 'just')
default:
    @just --list

# === Development ===

# Start all services (API + Workers + Temporal + PostgreSQL)
dev:
    docker compose up

# Start all services in background
dev-bg:
    docker compose up -d

# Start only API service
dev-api:
    docker compose up api

# Start only workers service
dev-workers:
    docker compose up workers

# Start frontend development server
dev-frontend:
    cd frontend && npm run dev

# Start all services + frontend
dev-all:
    #!/usr/bin/env bash
    docker compose up -d
    cd frontend && npm run dev

# View logs for all services
logs:
    docker compose logs -f

# View logs for specific service (e.g., just logs-service api)
logs-service service:
    docker compose logs -f {{service}}

# Restart all services
restart:
    docker compose restart

# Restart specific service
restart-service service:
    docker compose restart {{service}}

# === Testing ===

# Run all tests (e2e + unit)
test: test-e2e test-unit

# Run end-to-end test (manual execution via Temporal)
test-e2e:
    @echo "Running Temporal E2E test..."
    ./backend/scripts/test_temporal_e2e.sh

# Run schedule test (automatic execution)
test-schedule:
    @echo "Running schedule test..."
    ./backend/scripts/test_schedule.sh

# Run grounded search test
test-grounded:
    @echo "Running grounded search test..."
    ./backend/scripts/test_grounded_search.sh

# Run unit tests with pytest
test-unit:
    @echo "Running unit tests..."
    cd backend && uv run --with pytest --with pytest-asyncio --with pytest-cov pytest

# Run all e2e tests
test-all-e2e: test-e2e test-schedule test-grounded

# === Docker ===

# Start all services in background (alias for dev-bg)
up:
    docker compose up -d

# Stop all services
down:
    docker compose down

# Stop and remove volumes
down-v:
    docker compose down -v

# Build/rebuild all services
build:
    docker compose build

# Build without cache
build-clean:
    docker compose build --no-cache

# Build frontend for production
build-frontend:
    cd frontend && npm run build

# Preview frontend production build
preview-frontend:
    cd frontend && npm run preview

# Show service status
ps:
    docker compose ps

# === Database ===

# Run database migrations
migrate:
    docker compose exec api alembic upgrade head

# Rollback one migration
rollback:
    docker compose exec api alembic downgrade -1

# Show current migration version
migrate-status:
    docker compose exec api alembic current

# Show migration history
migrate-history:
    docker compose exec api alembic history

# Create new migration (requires message, e.g., just migrate-new "add new field")
migrate-new message:
    docker compose exec api alembic revision --autogenerate -m "{{message}}"

# Connect to PostgreSQL
psql:
    docker compose exec postgres psql -U torale -d torale

# Reset database (dangerous! drops all data)
reset:
    @echo "⚠️  This will drop all data. Press Ctrl+C to cancel..."
    @sleep 3
    docker compose down -v
    docker compose up -d postgres
    @sleep 2
    docker compose exec api alembic upgrade head

# === Maintenance ===

# Clean up Docker resources
clean:
    docker compose down -v
    docker system prune -f

# View API logs
logs-api:
    docker compose logs -f api

# View worker logs
logs-workers:
    docker compose logs -f workers

# View all logs related to temporal
logs-temporal:
    docker compose logs -f temporal

# Shell into API container
shell-api:
    docker compose exec api /bin/bash

# Shell into worker container
shell-workers:
    docker compose exec workers /bin/bash

# === Linting and Formatting ===

# Run ruff linter
lint:
    cd backend && uv run ruff check .

# Run ruff formatter
format:
    cd backend && uv run ruff format .

# Run type checker
typecheck:
    cd backend && uv run ty check .

# Run all checks (lint + format + typecheck)
check: lint typecheck

# === Installation ===

# Install backend dependencies
install:
    cd backend && uv sync

# Install backend dependencies (dev mode)
install-dev:
    cd backend && uv sync --dev

# Install frontend dependencies
install-frontend:
    cd frontend && npm install

# Install all dependencies (backend + frontend)
install-all: install install-frontend

# === Deployment ===

# Deploy to Google Cloud Run
deploy:
    ./deploy.sh

# Build for production
build-prod:
    docker build -f backend/Dockerfile -t torale-api ./backend
