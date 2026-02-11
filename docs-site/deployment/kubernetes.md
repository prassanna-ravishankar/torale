---
description: Kubernetes deployment with Helm charts. Production-grade configuration, scaling, health checks, and Kubernetes best practices.
---

# Kubernetes Deployment

Deploy Torale to GKE with full production setup.

## Prerequisites

- GKE cluster
- Cloud SQL PostgreSQL
- Domain with DNS access

## Quick Deploy

```bash
# One-time setup
just k8s-setup

# Deploy
just k8s-deploy-all

# Check status
just k8s-status
```

## Architecture

- **GKE Autopilot** - Managed Kubernetes
- **Cloud SQL** - Managed PostgreSQL  
- **GCE Load Balancer** - Ingress with SSL
- **Spot VMs** - 60-91% cost savings

## Helm Configuration

See `helm/torale/values.yaml` for all configuration options.

## Next Steps

- Read [CI/CD Setup](/deployment/ci-cd)
- View [Production Best Practices](/deployment/production)
