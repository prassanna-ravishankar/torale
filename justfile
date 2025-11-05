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

# Run backend unit tests
test:
    @echo "Running backend unit tests..."
    cd backend && uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    @echo "Running tests with coverage..."
    cd backend && uv run pytest tests/ --cov=src/torale --cov-report=term-missing

# Run e2e integration tests (requires services running)
test-e2e:
    @echo "Running E2E tests..."
    @echo "Note: Set TORALE_NOAUTH=1 for no-auth mode, or CLERK_TEST_TOKEN for Clerk auth"
    @echo ""
    ./backend/scripts/test_temporal_e2e.sh
    ./backend/scripts/test_schedule.sh
    ./backend/scripts/test_grounded_search.sh

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

# Build frontend static files (npm build)
build-frontend-static:
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

# === CI/CD ===

# Setup CI/CD (run once): Configure Cloud Build triggers and permissions
ci-setup:
    ./scripts/ci-setup.sh

# Build custom helm-deploy image for Cloud Build
ci-build-helm-image:
    gcloud builds submit --config=cloudbuild/build-helm-image.yaml cloudbuild/

# Manually trigger production build
ci-build-prod:
    gcloud builds submit --config=cloudbuild.yaml

# Manually trigger branch build
ci-build-branch:
    gcloud builds submit --config=cloudbuild-branch.yaml

# View recent Cloud Build history
ci-logs:
    gcloud builds list --limit=10

# View specific build logs (e.g., just ci-logs-build abc-123)
ci-logs-build build_id:
    gcloud builds log {{build_id}} --stream

# List Cloud Build triggers
ci-triggers:
    gcloud builds triggers list

# List all branch deployments
ci-list-branches:
    @echo "Branch Deployments:"
    @kubectl get namespaces -l type=branch-deployment --no-headers -o custom-columns=":metadata.name,:metadata.labels.branch,:metadata.creationTimestamp"

# Cleanup specific branch deployment (e.g., just ci-cleanup-branch feat-auth)
ci-cleanup-branch branch:
    ./scripts/k8s-cleanup-branch.sh {{branch}}

# Cleanup all branch deployments older than 7 days
ci-cleanup-old-branches:
    #!/usr/bin/env bash
    echo "🗑️  Cleaning up branch deployments older than 7 days..."
    kubectl get namespaces -l type=branch-deployment -o json | \
      jq -r '.items[] | select(.metadata.creationTimestamp | fromdateiso8601 < (now - 604800)) | .metadata.name' | \
      while read ns; do
        echo "Deleting old namespace: $ns"
        kubectl delete namespace "$ns" --timeout=2m || true
      done
    echo "✅ Cleanup complete"

# === Deployment ===

# Build for production
build-prod:
    docker build -f backend/Dockerfile -t torale-api ./backend

# Build frontend production image
build-frontend:
    docker build -f frontend/Dockerfile -t torale-frontend ./frontend

# Push images to GCR (builds with correct platform for GKE)
k8s-push:
    #!/usr/bin/env bash
    set -e
    echo "Building and pushing images to GCR with linux/amd64 platform..."
    docker build --platform=linux/amd64 -f backend/Dockerfile -t gcr.io/baldmaninc/torale/api:latest ./backend
    docker tag gcr.io/baldmaninc/torale/api:latest gcr.io/baldmaninc/torale/worker:latest
    docker build --platform=linux/amd64 -f frontend/Dockerfile -t gcr.io/baldmaninc/torale/frontend:latest ./frontend
    docker push gcr.io/baldmaninc/torale/api:latest
    docker push gcr.io/baldmaninc/torale/worker:latest
    docker push gcr.io/baldmaninc/torale/frontend:latest
    echo "✓ All images built and pushed successfully!"

# === Kubernetes (GKE ClusterKit) ===

# Get cluster credentials
k8s-auth:
    gcloud container clusters get-credentials clusterkit \
      --region us-central1 --project baldmaninc

# One-time setup: Create Cloud SQL instance and IAM
k8s-setup:
    ./scripts/k8s-setup-cloudsql.sh

# Create Kubernetes secrets from .env
k8s-secrets:
    ./scripts/k8s-create-secrets.sh

# Deploy Temporal to cluster
k8s-deploy-temporal:
    helmfile sync --selector tier=temporal

# Deploy Torale application
k8s-deploy-app:
    helmfile sync --selector tier=app

# Deploy everything (Temporal + Torale)
k8s-deploy-all:
    helmfile sync

# Check deployment status
k8s-status:
    ./scripts/k8s-check-status.sh

# View API logs in k8s
k8s-logs-api:
    kubectl logs -n torale -l app.kubernetes.io/component=api -f --tail=100

# View worker logs in k8s
k8s-logs-workers:
    kubectl logs -n torale -l app.kubernetes.io/component=worker -f --tail=100

# View frontend logs in k8s
k8s-logs-frontend:
    kubectl logs -n torale -l app.kubernetes.io/component=frontend -f --tail=100

# View Temporal logs
k8s-logs-temporal:
    kubectl logs -n temporal -l app.kubernetes.io/name=temporal -f --tail=100

# Port-forward API to localhost:8000
k8s-port-forward-api:
    kubectl port-forward -n torale svc/torale-api 8000:80

# Port-forward Temporal UI to localhost:8080
k8s-port-forward-temporal:
    kubectl port-forward -n temporal svc/temporal-ui 8080:8080

# Get all pods status
k8s-pods:
    @echo "Torale Pods:"
    @kubectl get pods -n torale
    @echo ""
    @echo "Temporal Pods:"
    @kubectl get pods -n temporal

# Restart API deployment
k8s-restart-api:
    kubectl rollout restart deployment/torale-api -n torale

# Restart worker deployment
k8s-restart-workers:
    kubectl rollout restart deployment/torale-worker -n torale

# Restart frontend deployment
k8s-restart-frontend:
    kubectl rollout restart deployment/torale-frontend -n torale

# Delete everything (dangerous!)
k8s-destroy:
    @echo "⚠️  This will delete all Kubernetes resources. Press Ctrl+C to cancel..."
    @sleep 5
    helmfile destroy
