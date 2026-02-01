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

Docker Compose starts these services:

**postgres** - PostgreSQL 16 database for storing tasks and execution history

**api** - FastAPI server with APScheduler handling REST API and scheduled tasks

**frontend** - React SPA served by Vite dev server

## Environment Configuration

Required variables in `.env`:

```bash
# AI (required for monitoring agent)
ANTHROPIC_API_KEY=your-anthropic-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
MEM0_API_KEY=your-mem0-api-key

# Clerk authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# Database (pre-configured)
DATABASE_URL=postgresql://torale:torale@postgres:5432/torale
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
- PostgreSQL: localhost:5432

## Stopping Services

```bash
docker compose down

# Remove volumes (deletes data)
docker compose down -v
```

## Troubleshooting

**Port conflicts** - Check if ports 5432, 8000, or 5173 are in use

**Database connection failed** - Wait for postgres to be healthy before starting API

See logs:
```bash
docker compose logs api
docker compose logs postgres
```

## Next Steps

- Read [Architecture](/self-hosted/architecture) to understand components
- Configure [Environment Variables](/self-hosted/configuration)
- Set up [Kubernetes](/self-hosted/kubernetes) for production
