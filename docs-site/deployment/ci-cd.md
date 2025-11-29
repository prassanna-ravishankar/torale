# CI/CD Setup

GitHub Actions workflows for automated deployments.

## Environment Flow

```
Local Development → Staging → Production
```

## Production Workflow

`.github/workflows/production.yml` - Triggers on push to `main`:

1. **Validate** - Check project structure
2. **Build** - Build and push Docker images to GCR
3. **Deploy** - Deploy via Helmfile
4. **Verify** - Check rollout status

## Staging Workflow

`.github/workflows/staging.yml` - Triggers on `deploy` label or manual dispatch:

1. **Build** - Build and push Docker images with commit SHA tag
2. **Deploy** - Deploy via `helmfile -e staging sync`
3. **Verify** - Check rollout status
4. **Comment** - Post deployment URL to PR

### Deploying to Staging

**Option 1: Label trigger**
- Add the `deploy` label to any PR
- Workflow runs once on label add
- To redeploy after new commits: remove and re-add the label

**Option 2: Manual dispatch**
- Go to Actions → "Deploy to Staging" → Run workflow

### Staging Lifecycle

- Staging environment persists indefinitely
- Each deploy updates the existing environment
- No automatic teardown on PR close/merge
- Manual teardown: `helm uninstall torale -n torale-staging`

### What's Shared vs Isolated

| Resource | Staging | Production |
|----------|---------|------------|
| GKE Cluster | Shared | Shared |
| Namespace | `torale-staging` | `torale` |
| Database | Shared | Shared |
| Clerk App | Shared | Shared |
| Temporal Namespace | Shared | Shared |
| Temporal Task Queue | `torale-staging` | `torale-tasks` |
| Static IP | Separate | Separate |
| SSL Certificate | Separate | Separate |

## Setup Requirements

1. Configure Workload Identity Federation for GCP authentication
2. Add required secrets to GitHub repository
3. Create `staging` environment in GitHub Settings → Environments

## Next Steps

- View [Kubernetes Deployment](/deployment/kubernetes)
- Read [Production Best Practices](/deployment/production)
