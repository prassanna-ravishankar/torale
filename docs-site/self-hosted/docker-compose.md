# Docker Compose Setup

Run Torale locally with Docker Compose.

## Quick Start

```bash
git clone https://github.com/torale-ai/torale
cd torale
cp .env.example .env
# Edit .env with your API keys
just dev
```

## Services

Docker Compose starts four services:

**postgres** - PostgreSQL 16 database for storing tasks and execution history

**temporal** - Self-hosted Temporal server for workflow orchestration

**api** - FastAPI server handling REST API requests

**worker** - Temporal worker executing scheduled monitoring tasks

**frontend** - React SPA served by Vite dev server

## Environment Configuration

Required variables in `.env`:

```bash
# Gemini API (required)
GOOGLE_API_KEY=your-api-key

# Clerk authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database (pre-configured)
DATABASE_URL=postgresql://torale:torale@postgres:5432/torale

# Temporal (pre-configured)
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=default
```

## Database Migrations

Migrations run automatically via init container before the API starts. The init container waits for PostgreSQL to be healthy, then runs `alembic upgrade head`.

To run migrations manually:

```bash
docker compose exec api alembic upgrade head
```

## Accessing Services

- API: http://localhost:8000
- Frontend: http://localhost:5173
- Temporal UI: http://localhost:8080
- PostgreSQL: localhost:5432

## Stopping Services

```bash
docker compose down

# Remove volumes (deletes data)
docker compose down -v
```

## Troubleshooting

**Port conflicts** - Check if ports 5432, 7233, 8000, 8080, or 5173 are in use

**Database connection failed** - Wait for postgres to be healthy before starting API

**Temporal connection refused** - Ensure temporal service is running

See logs:
```bash
docker compose logs api
docker compose logs worker
docker compose logs postgres
docker compose logs temporal
```

## Next Steps

- Read [Architecture](/self-hosted/architecture) to understand components
- Configure [Environment Variables](/self-hosted/configuration)
- Set up [Kubernetes](/self-hosted/kubernetes) for production
