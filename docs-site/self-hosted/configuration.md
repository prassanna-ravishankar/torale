---
description: Configure self-hosted Torale instance. Environment variables, database settings, API keys, and feature flags for custom deployments.
---

# Configuration

Environment variables for self-hosted Torale deployments.

## Required Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/torale

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...

# Agent
# Local dev (running agent directly): http://localhost:8001
AGENT_URL=http://localhost:8001

# AI (required for monitoring agent)
GEMINI_API_KEY=your-gemini-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
MEM0_API_KEY=your-mem0-api-key
```

## Optional Variables

```bash
# Fallback LLM providers
OPENAI_API_KEY=sk-...

# Frontend configuration
VITE_API_BASE_URL=http://localhost:8000
```

## Development Mode

Disable authentication for local development:

```bash
TORALE_NOAUTH=1
VITE_TORALE_NOAUTH=1
```

## Docker Compose Values

Pre-configured in `docker-compose.yml`:

```yaml
DATABASE_URL: postgresql://torale:torale@postgres:5432/torale
AGENT_URL: http://agent:8000
```

## Kubernetes Values

Configured in Helm values and secrets:

**values.yaml** - Non-sensitive configuration

**Kubernetes secrets** - API keys and passwords

Deploy secrets before Helm:

```bash
kubectl create secret generic torale-secrets -n torale \
  --from-literal=GEMINI_API_KEY="..." \
  --from-literal=PERPLEXITY_API_KEY="..." \
  --from-literal=CLERK_SECRET_KEY="..." \
  --from-literal=DB_PASSWORD="..."
```

## Next Steps

- Set up [Docker Compose](/self-hosted/docker-compose)
- Deploy to [Kubernetes](/self-hosted/kubernetes)
- Read [Migrations Guide](/self-hosted/migrations)
