# Torale Task Runner
# Usage: just <command>
# Run 'just --list' to see all available commands

# Default recipe
default:
    @just --list

# === Development ===

# Start all services (API + PostgreSQL)
# Use WEBWHEN_NOAUTH=1 for no-auth mode
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
    WEBWHEN_NOAUTH=1 docker compose up -d
    cd frontend && npm install && NEXT_PUBLIC_WEBWHEN_NOAUTH=1 npm run dev

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
    @echo "Running agent unit and protocol tests..."
    cd torale-agent && uv run pytest tests/ -v

# Run the live SDK suite against an explicitly isolated no-auth API
test-sdk-live:
    #!/usr/bin/env bash
    set -e
    if [ "${WEBWHEN_SDK_TEST_ISOLATED:-}" != "1" ]; then
        echo "Set WEBWHEN_SDK_TEST_ISOLATED=1 only for an isolated disposable API/database."
        exit 1
    fi
    cd backend
    uv run --all-extras pytest tests/test_sdk_integration.py -m integration -v

# Run tests with coverage
test-cov:
    @echo "Running tests with coverage..."
    cd backend && uv run --all-extras pytest tests/ --cov=src/torale --cov-report=term-missing

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
    @echo "Running agent linting and type checking..."
    cd torale-agent && uv run ruff check .
    cd torale-agent && uv run ruff format --check .
    cd torale-agent && uv run ty check .
    cd torale-agent && uv run python -c "import server"
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
    docker build --platform=linux/amd64 -f frontend/Dockerfile -t gcr.io/baldmaninc/torale-frontend:latest ./frontend
    docker build --platform=linux/amd64 -f torale-agent/Dockerfile -t gcr.io/baldmaninc/torale-agent:latest ./torale-agent
    docker push gcr.io/baldmaninc/torale-api:latest
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

# Scale staging deployments to zero
staging-down:
    kubectl scale deployment --all -n torale-staging --replicas=0

# Scale staging deployments back up
staging-up:
    kubectl scale deployment --all -n torale-staging --replicas=1
