# CI/CD Setup

GitHub Actions workflow for automated deployments.

## Workflow

`.github/workflows/production.yml`:

1. **Validate** - Check project structure
2. **Build** - Build and push Docker images
3. **Deploy** - Deploy via Helmfile
4. **Verify** - Check rollout status

## Setup

1. Configure Workload Identity Federation
2. Add secrets to GitHub
3. Push to main branch → auto-deploy

## Next Steps

- View [Kubernetes Deployment](/deployment/kubernetes)
- Read [Production Best Practices](/deployment/production)
