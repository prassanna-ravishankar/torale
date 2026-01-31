# Torale Task Runner
# Usage: just <command>
# Run 'just --list' to see all available commands

# Default recipe
default:
    @just --list

# === Development ===

# Start all services (API + Workers + Temporal + PostgreSQL)
# Use TORALE_NOAUTH=1 for no-auth mode
dev: build
    docker compose up

# Start all services in background
dev-bg: build
    docker compose up -d

# Start all services + frontend
dev-full: build
    #!/usr/bin/env bash
    docker compose up -d
    cd frontend && npm install && npm run dev

# Start all services + frontend in no-auth mode
dev-noauth: build
    #!/usr/bin/env bash
    TORALE_NOAUTH=1 docker compose up -d
    cd frontend && npm install && VITE_TORALE_NOAUTH=1 npm run dev

# Start specific service (api, workers)
dev-service service: build
    docker compose up {{service}}

# Start frontend development server
dev-frontend:
    cd frontend && npm run dev

# === Docker ===

# Stop all services
down:
    docker compose down

# Stop and remove volumes
down-v:
    docker compose down -v

# Build/rebuild all services
build:
    @echo "Copying README.md to backend/ for Docker build..."
    @cp README.md backend/README.md
    docker compose build

# Build without cache
build-clean:
    @echo "Copying README.md to backend/ for Docker build..."
    @cp README.md backend/README.md
    docker compose build --no-cache

# Build frontend static files
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

# Show migration history
migrate-history:
    docker compose exec api alembic history

# Create new migration
migrate-new message:
    docker compose exec api alembic revision --autogenerate -m "{{message}}"

# Connect to PostgreSQL
psql:
    docker compose exec postgres psql -U torale -d torale

# Reset database (dangerous!)
reset:
    @echo "⚠️  This will drop all data. Press Ctrl+C to cancel..."
    @sleep 3
    docker compose down -v
    docker compose up -d postgres
    @sleep 2
    docker compose exec api alembic upgrade head

# === Testing ===

# Run backend unit tests
test:
    @echo "Running backend unit tests..."
    cd backend && uv run --all-extras pytest tests/ -v

# Run tests with coverage
test-cov:
    @echo "Running tests with coverage..."
    cd backend && uv run --all-extras pytest tests/ --cov=src/torale --cov-report=term-missing

# Run integration tests (requires services running)
test-integration:
    @echo "Running Integration tests..."
    cd backend && uv run --all-extras pytest tests/integration/ -v

# === Logs ===

# View logs for all services
logs:
    docker compose logs -f

# View logs for specific service
logs-service service:
    docker compose logs -f {{service}}

# === Maintenance ===

# Clean up Docker resources
clean:
    docker compose down -v
    docker system prune -f

# Shell into container
shell service:
    docker compose exec {{service}} /bin/bash

# === Linting ===

# Run all linting (backend + frontend)
lint:
    @echo "Running backend linting..."
    cd backend && uv run ruff check .
    cd backend && uv run ruff format --check .
    @echo "Running frontend linting..."
    cd frontend && npm run lint
    cd frontend && npx tsc --noEmit

# Run ruff formatter
format:
    cd backend && uv run ruff format .

# Run type checker
typecheck:
    cd backend && uv run ty check .

# Run all checks
check: lint typecheck

# === Installation ===

# Install all dependencies
install:
    cd backend && uv sync
    cd frontend && npm install

# === Deployment (K8s) ===

# Deploy to K8s (all)
k8s-deploy:
    helmfile sync

# Build and push images
k8s-push:
    #!/usr/bin/env bash
    set -e
    echo "Building and pushing images..."
    docker build --platform=linux/amd64 -f backend/Dockerfile -t gcr.io/baldmaninc/torale-api:latest ./backend
    docker tag gcr.io/baldmaninc/torale-api:latest gcr.io/baldmaninc/torale-worker:latest
    docker build --platform=linux/amd64 -f frontend/Dockerfile -t gcr.io/baldmaninc/torale-frontend:latest ./frontend
    docker build --platform=linux/amd64 -f torale-agent/Dockerfile -t gcr.io/baldmaninc/torale-agent:latest .
    docker push gcr.io/baldmaninc/torale-api:latest
    docker push gcr.io/baldmaninc/torale-worker:latest
    docker push gcr.io/baldmaninc/torale-frontend:latest
    docker push gcr.io/baldmaninc/torale-agent:latest

# Check K8s status
k8s-status:
    ./scripts/k8s-check-status.sh

# K8s logs
k8s-logs component:
    kubectl logs -n torale -l app.kubernetes.io/component={{component}} -f --tail=100

# K8s port forward API
k8s-pf-api:
    kubectl port-forward -n torale svc/torale-api 8000:80

# K8s logs for agent
k8s-logs-agent:
    kubectl logs -n torale -l app.kubernetes.io/component=agent -f --tail=100

# K8s port forward agent
k8s-pf-agent:
    kubectl port-forward -n torale svc/torale-agent 8001:80

# K8s port forward Temporal
k8s-pf-temporal:
    kubectl port-forward -n temporal svc/temporal-ui 8080:8080
