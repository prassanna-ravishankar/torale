---
description: Production deployment guide for Torale. GKE setup, CI/CD, monitoring, and cost optimization.
---

# Production Deployment

Deploy and manage Torale in production environments.

## Deployment Guides

**[Production Setup](./production)** - GKE deployment, monitoring, and security best practices

**[Kubernetes Guide](./kubernetes)** - Helm charts, HPA scaling, and resource management

**[Self-Hosted Deployment](./self-hosted)** - Alternative deployment options

## Infrastructure Management

**[CI/CD Pipeline](./ci-cd)** - GitHub Actions workflows and automation

**[Cost Optimization](./cost-optimization)** - Spot VMs, resource right-sizing, and autoscaling

## Key Features

- **Kubernetes-native**: Deployed on GKE with Helm charts
- **Auto-scaling**: HPA with min 2, max 10 replicas
- **Cost-optimized**: Spot VMs and efficient resource allocation
- **Monitoring**: APScheduler health checks and execution error tracking

## Getting Started

For production deployment on GKE, start with the [Production Setup](./production) guide. For cost optimization strategies, see [Cost Optimization](./cost-optimization).
