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

  api:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
```

## Configuration

See `.env.example` for all environment variables.

**Required:**
- `GEMINI_API_KEY` - Powers the monitoring agent
- `PERPLEXITY_API_KEY` - Agent search provider
- `MEM0_API_KEY` - Agent cross-run memory
- `CLERK_SECRET_KEY` - Clerk authentication
- `DATABASE_URL` - PostgreSQL connection string

## Next Steps

- Read [Kubernetes Deployment](/deployment/kubernetes)
- View [CI/CD Setup](/deployment/ci-cd)
