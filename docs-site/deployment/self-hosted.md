# Self-Hosted Deployment

Run Torale on your own infrastructure using Docker Compose.

## Quick Start

```bash
git clone https://github.com/torale-ai/torale
cd torale
cp .env.example .env
# Edit .env with your API keys
just dev
```

## Requirements

- Docker & Docker Compose
- PostgreSQL 16
- Python 3.9+
- Node.js 20+

## Services

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"

  temporal:
    image: temporalio/auto-setup:latest
    ports:
      - "7233:7233"
      - "8080:8080"

  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - temporal

  worker:
    build: ./backend
    command: python -m torale.workers
    depends_on:
      - postgres
      - temporal
```

## Configuration

See `.env.example` for all environment variables.

**Required:**
- `GOOGLE_API_KEY` - Gemini API key
- `CLERK_SECRET_KEY` - Clerk authentication
- `DATABASE_URL` - PostgreSQL connection string

## Next Steps

- Read [Kubernetes Deployment](/deployment/kubernetes)
- View [CI/CD Setup](/deployment/ci-cd)
