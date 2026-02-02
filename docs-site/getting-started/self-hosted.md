# Self-Hosted

Run Torale on your own infrastructure.

## Docker Compose (Recommended)

The fastest way to run Torale locally or on a single server.

### Clone Repository

```bash
git clone https://github.com/torale-ai/torale
cd torale
```

### Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
MEM0_API_KEY=your-mem0-api-key
CLERK_SECRET_KEY=your-clerk-secret
CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key

# Database (pre-configured for Docker Compose)
DATABASE_URL=postgresql://torale:torale@postgres:5432/torale
```

### Start Services

```bash
just dev
```

This starts:
- PostgreSQL database
- API server with APScheduler (port 8000)
- Frontend (port 5173)

### Verify

```bash
# Check API
curl http://localhost:8000/health

# Check frontend
open http://localhost:5173
```

## Kubernetes

For production deployments on GKE or other Kubernetes clusters.

See the [Kubernetes Deployment Guide](/self-hosted/kubernetes) for complete setup instructions.

**Requirements:**
- Kubernetes cluster
- PostgreSQL database (Cloud SQL or self-hosted)
- Domain with DNS access

## Configuration

### Required API Keys

**Gemini** - Powers the monitoring agent
```bash
GEMINI_API_KEY=...
```

**Perplexity** - Agent search provider
```bash
PERPLEXITY_API_KEY=...
```

**Mem0** - Agent cross-run memory
```bash
MEM0_API_KEY=...
```

**Clerk** - User auth management
```bash
CLERK_SECRET_KEY=...
CLERK_PUBLISHABLE_KEY=...
```

Sign up at: [https://clerk.com](https://clerk.com)

## Next Steps

- Read [Docker Compose Setup](/self-hosted/docker-compose) for detailed instructions
- Learn about [Architecture](/self-hosted/architecture)
- Configure [Environment Variables](/self-hosted/configuration)
- Set up [Kubernetes Deployment](/self-hosted/kubernetes)
