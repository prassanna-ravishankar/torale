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

# LLM Provider (at least one required)
GOOGLE_API_KEY=your-gemini-api-key

# Temporal
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=default
```

## Optional Variables

```bash
# Fallback LLM providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Temporal Cloud (for production)
TEMPORAL_API_KEY=your-temporal-cloud-api-key
TEMPORAL_UI_URL=https://cloud.temporal.io

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
TEMPORAL_HOST: temporal:7233
TEMPORAL_NAMESPACE: default
```

## Kubernetes Values

Configured in Helm values and secrets:

**values.yaml** - Non-sensitive configuration

**Kubernetes secrets** - API keys and passwords

Deploy secrets before Helm:

```bash
kubectl create secret generic torale-secrets -n torale \
  --from-literal=GOOGLE_API_KEY="..." \
  --from-literal=CLERK_SECRET_KEY="..." \
  --from-literal=DB_PASSWORD="..."
```

## Next Steps

- Set up [Docker Compose](/self-hosted/docker-compose)
- Deploy to [Kubernetes](/self-hosted/kubernetes)
- Read [Migrations Guide](/self-hosted/migrations)
