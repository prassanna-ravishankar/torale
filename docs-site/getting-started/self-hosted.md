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
GOOGLE_API_KEY=your-gemini-api-key
CLERK_SECRET_KEY=your-clerk-secret
CLERK_PUBLISHABLE_KEY=your-clerk-publishable-key

# Database (pre-configured for Docker Compose)
DATABASE_URL=postgresql://torale:torale@postgres:5432/torale

# Temporal (pre-configured for Docker Compose)
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=default
```

### Start Services

```bash
just dev
```

This starts:
- PostgreSQL database
- Temporal server
- API server (port 8000)
- Temporal worker
- Frontend (port 5173)

### Verify

```bash
# Check API
curl http://localhost:8000/health

# Check Temporal UI
open http://localhost:8080

# Check frontend
open http://localhost:5173
```

## Kubernetes

For production deployments on GKE or other Kubernetes clusters.

See the [Kubernetes Deployment Guide](/self-hosted/kubernetes) for complete setup instructions.

**Requirements:**
- Kubernetes cluster
- PostgreSQL database (Cloud SQL or self-hosted)
- Temporal Cloud account or self-hosted Temporal
- Domain with DNS access

## Configuration

### Required API Keys

**Gemini API** - Primary search provider
```bash
GOOGLE_API_KEY=...
```

Get your key at: [https://ai.google.dev](https://ai.google.dev)

**Clerk Authentication** - User auth management
```bash
CLERK_SECRET_KEY=...
CLERK_PUBLISHABLE_KEY=...
```

Sign up at: [https://clerk.com](https://clerk.com)

### Optional API Keys

**OpenAI** - Fallback LLM
```bash
OPENAI_API_KEY=...
```

**Anthropic** - Fallback LLM
```bash
ANTHROPIC_API_KEY=...
```

## Next Steps

- Read [Docker Compose Setup](/self-hosted/docker-compose) for detailed instructions
- Learn about [Architecture](/self-hosted/architecture)
- Configure [Environment Variables](/self-hosted/configuration)
- Set up [Kubernetes Deployment](/self-hosted/kubernetes)
