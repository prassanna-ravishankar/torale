---
description: Deploy Torale on Kubernetes. Helm charts, Gateway API configuration, persistent storage, and production-ready Kubernetes deployment.
---

# Kubernetes Deployment

Deploy Torale to production Kubernetes environments.

## Prerequisites

- Kubernetes cluster
- PostgreSQL database (managed or self-hosted)
- DNS configuration for domains

## GKE Quick Start

```bash
# One-time cluster setup
just k8s-setup

# Deploy all services
just k8s-deploy-all

# Verify deployment
just k8s-status
```

## Helm Configuration

Main configuration in `helm/torale/values.yaml`:

```yaml
domains:
  frontend: torale.ai
  api: api.torale.ai
  docs: docs.torale.ai

api:
  replicaCount: 2
  autoscaling:
    minReplicas: 2
    maxReplicas: 10
```

Override for production in `values-production.yaml`.

## Deployment Components

**API Deployment** - FastAPI + APScheduler with Cloud SQL Proxy sidecar, HPA for scaling

**Frontend & Docs** - nginx serving static assets, lightweight HPA

**Gateway API** - GKE Gateway with HTTPRoute for routing and automatic SSL

**Migration Job** - Helm pre-install/pre-upgrade hook runs Alembic migrations

## Deploy

```bash
IMAGE_TAG=latest helmfile sync --selector tier=app
```

Verify rollout:

```bash
kubectl rollout status deployment/torale-api -n torale
kubectl rollout status deployment/torale-worker -n torale
kubectl rollout status deployment/torale-frontend -n torale
kubectl rollout status deployment/torale-docs -n torale
```

## Secrets Management

Create secrets manually before deployment:

```bash
kubectl create secret generic torale-secrets -n torale \
  --from-literal=GEMINI_API_KEY="..." \
  --from-literal=PERPLEXITY_API_KEY="..." \
  --from-literal=CLERK_SECRET_KEY="..." \
  --from-literal=DB_PASSWORD="..."
```

Or use the helper script:

```bash
just k8s-create-secrets
```

## Cost Optimization

All services use Spot VMs:
- 60-91% cost savings
- Automatic pod migration on preemption
- nodeSelector and tolerations configured in Helm

Resource requests are right-sized:
- API/Workers: 100m CPU, 256Mi RAM
- Frontend/Docs: 50m CPU, 64Mi RAM

## Next Steps

- Understand [Architecture](/self-hosted/architecture)
- Configure [Environment Variables](/self-hosted/configuration)
- Read [Migrations Guide](/self-hosted/migrations)
- Set up [Docker Compose](/self-hosted/docker-compose) for local development
