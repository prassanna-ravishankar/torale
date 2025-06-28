# Torale Project Management
# Run `just` or `just --list` to see available commands

# Default recipe - show help
default:
    @just --list

# =============================================================================
# Docker Compose Commands
# =============================================================================

# Build and start all services with Docker Compose
up: check-env
    docker compose up --build

# Build and start all services without frontend (for quick backend testing)
up-backend: check-env
    docker compose up --build discovery-service content-monitoring-service notification-service backend

# Start all services in background
up-detached: check-env
    docker compose up --build -d

# Stop all services
down:
    docker compose down

# Stop all services and remove volumes
down-clean:
    docker compose down -v

# View logs for all services
logs:
    docker compose logs -f

# View logs for a specific service
logs-service service:
    docker compose logs -f {{service}}

# Rebuild specific service
rebuild service:
    docker compose build {{service}}

# =============================================================================
# Development Commands
# =============================================================================

# Start all microservices for development
dev-services: check-env
    ./start-microservices.sh

# Start only frontend for development
dev-frontend:
    cd frontend && npm run dev

# Start only backend for development
dev-backend: check-env
    cd backend && uv run python -m uvicorn app.main:app --reload --port 8000

# =============================================================================
# Setup Commands
# =============================================================================

# Setup project from scratch
setup: install-deps check-env
    @echo "✅ Project setup complete!"
    @echo "Next steps:"
    @echo "1. Configure your .env file with API keys"
    @echo "2. Run 'just up' to start all services"

# Install dependencies for all services
install-deps:
    @echo "Installing dependencies..."
    cd backend && uv sync
    cd discovery-service && uv sync
    cd content-monitoring-service && uv sync
    cd notification-service && uv sync
    cd frontend && npm install

# Generate lockfiles for all Python services
lock:
    @echo "Generating lockfiles..."
    cd backend && uv lock
    cd discovery-service && uv lock
    cd content-monitoring-service && uv lock
    cd notification-service && uv lock

# Fix Docker build issues (regenerate lockfiles and build)
fix-docker: lock
    @echo "Fixing Docker build issues..."
    docker compose build --no-cache

# =============================================================================
# Testing Commands
# =============================================================================

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
    cd backend && uv run pytest

# Run frontend tests
test-frontend:
    cd frontend && npm test

# Run tests with coverage
test-coverage:
    cd backend && uv run pytest --cov=app --cov-report=term-missing
    cd frontend && npm run coverage

# =============================================================================
# Code Quality Commands
# =============================================================================

# Format all code
format:
    @echo "Formatting Python code..."
    cd backend && uv run ruff format .
    cd discovery-service && uv run ruff format .
    cd content-monitoring-service && uv run ruff format .
    cd notification-service && uv run ruff format .
    @echo "Formatting frontend code..."
    cd frontend && npm run format

# Lint all code
lint:
    @echo "Linting Python code..."
    cd backend && uv run ruff check .
    cd discovery-service && uv run ruff check .
    cd content-monitoring-service && uv run ruff check .
    cd notification-service && uv run ruff check .
    @echo "Linting frontend code..."
    cd frontend && npm run lint

# Type check all code
typecheck:
    @echo "Type checking Python code..."
    cd backend && uv run mypy .
    cd discovery-service && uv run mypy .
    cd content-monitoring-service && uv run mypy .
    cd notification-service && uv run mypy .
    @echo "Type checking frontend code..."
    cd frontend && npm run type-check

# Run all quality checks
check: lint typecheck test

# =============================================================================
# Health Check Commands
# =============================================================================

# Check if all services are healthy
health:
    @echo "Checking service health..."
    @curl -s http://localhost:8000/health | jq '.' || echo "❌ Backend unhealthy"
    @curl -s http://localhost:8001/health | jq '.' || echo "❌ Discovery service unhealthy"
    @curl -s http://localhost:8002/api/v1/health | jq '.' || echo "❌ Content monitoring unhealthy"
    @curl -s http://localhost:8003/health | jq '.' || echo "❌ Notification service unhealthy"
    @curl -s http://localhost:3000 >/dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"

# Test notification service specifically
test-notifications:
    ./test-notification.sh

# =============================================================================
# Database Commands
# =============================================================================

# Apply database migrations (requires supabase CLI)
migrate:
    @echo "Apply migrations manually in Supabase dashboard"
    @echo "Or use: supabase db push"

# Generate TypeScript types from database
generate-types:
    @echo "Generating database types..."
    @cd frontend && supabase gen types typescript --local > src/types/supabase.ts || echo "Run 'supabase start' first"

# =============================================================================
# Environment Commands
# =============================================================================

# Check if required environment variables are set
check-env:
    @echo "Checking environment variables..."
    @test -f .env || (echo "❌ .env file not found. Copy from .env.example" && exit 1)
    @grep -q "SUPABASE_URL=" .env || (echo "❌ SUPABASE_URL not set" && exit 1)
    @grep -q "OPENAI_API_KEY=" .env || (echo "❌ OPENAI_API_KEY not set" && exit 1)
    @grep -q "PERPLEXITY_API_KEY=" .env || (echo "❌ PERPLEXITY_API_KEY not set" && exit 1)
    @echo "✅ Environment variables look good"

# Copy environment template
copy-env:
    cp .env.example .env
    @echo "✅ Copied .env.example to .env"
    @echo "📝 Please edit .env with your API keys"

# =============================================================================
# Cleanup Commands
# =============================================================================

# Clean all build artifacts
clean:
    @echo "Cleaning build artifacts..."
    docker compose down --rmi all --volumes --remove-orphans
    cd frontend && rm -rf .next node_modules
    cd backend && rm -rf .venv __pycache__
    cd discovery-service && rm -rf .venv __pycache__
    cd content-monitoring-service && rm -rf .venv __pycache__
    cd notification-service && rm -rf .venv __pycache__

# Clean Docker system (use with caution)
clean-docker:
    docker system prune -af
    docker volume prune -f

# =============================================================================
# Utility Commands
# =============================================================================

# Show all service URLs
urls:
    @echo "🌐 Service URLs:"
    @echo "Frontend:              http://localhost:3000"
    @echo "Backend API:           http://localhost:8000"
    @echo "Discovery Service:     http://localhost:8001"
    @echo "Content Monitoring:    http://localhost:8002"
    @echo "Notification Service:  http://localhost:8003"
    @echo ""
    @echo "📚 API Documentation:"
    @echo "Backend:               http://localhost:8000/docs"
    @echo "Discovery:             http://localhost:8001/docs"
    @echo "Content Monitoring:    http://localhost:8002/docs"
    @echo "Notifications:         http://localhost:8003/docs"

# Open all service URLs in browser (macOS)
open:
    open http://localhost:3000
    open http://localhost:8000/docs
    open http://localhost:8001/docs
    open http://localhost:8002/docs
    open http://localhost:8003/docs

# Show project structure
tree:
    tree -I 'node_modules|.venv|__pycache__|.git|.next|dist|build'

# =============================================================================
# CI/CD Commands
# =============================================================================

# Run CI pipeline locally
ci: check lock lint typecheck test
    @echo "✅ CI pipeline passed!"

# Prepare for production deployment
production-ready: ci
    @echo "✅ Ready for production deployment"
    @echo "Don't forget to:"
    @echo "1. Set production environment variables"
    @echo "2. Configure domain and SSL"
    @echo "3. Set up monitoring and logging"