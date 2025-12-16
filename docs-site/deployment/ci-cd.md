# CI/CD with GitHub Actions

Automated CI/CD pipeline using GitHub Actions with Workload Identity Federation for keyless GCP authentication.

## Overview

The GitHub Actions pipeline provides:

- **Production Deployments**: Auto-deploy to `torale` namespace on push to `main`
- **Staging Deployments**: Deploy to `torale-staging` via label or manual trigger
- **Security Scanning**: Trivy vulnerability detection
- **Parallel Builds**: Fast builds with matrix strategy
- **Keyless Auth**: Workload Identity Federation (no service account keys)

### Pipeline Flow

```
Validate → Build (3 parallel) → Scan → Deploy → Verify
   ↓           ↓                  ↓       ↓        ↓
Check      API/Worker/         Trivy   Helmfile  Health
Files      Frontend                     Sync     Checks
```

### Workflow Files

- **Production**: `.github/workflows/production.yml`
- **Staging**: `.github/workflows/staging.yml`
- **Runtime**: ~2-4 minutes (optimized with parallel builds and Docker cache)

## Setup

### Prerequisites

- GKE cluster running
- `gcloud` CLI authenticated
- GitHub repository access

### Keyless Authentication (Workload Identity Federation)

**Benefits:**
- ✅ No long-lived credentials
- ✅ No key rotation required
- ✅ Automatic short-lived tokens via OIDC
- ✅ More secure than service account keys

**Setup:**

```bash
./scripts/setup-github-wif.sh
```

This creates:
1. Workload Identity Pool
2. Workload Identity Provider
3. Service account with GKE/GCR permissions
4. Workload Identity binding

**Add GitHub Secrets:**

Go to repository Settings → Secrets and variables → Actions:

```bash
gh secret set GCP_PROJECT_ID --body 'your-project-id'
gh secret set GCP_SERVICE_ACCOUNT --body 'github-actions@PROJECT.iam.gserviceaccount.com'
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body 'projects/123/locations/global/...'
```

## Environment Flow

```
Local Development → Staging → Production
```

## Production Workflow

Triggers on push to `main`:

```bash
git push origin main
```

**Steps:**
1. ✅ Validate project structure
2. ✅ Build API, Worker, Frontend images (parallel)
3. ✅ Scan for vulnerabilities with Trivy
4. ✅ Deploy to `torale` namespace via Helmfile
5. ✅ Verify rollout and health checks
6. ✅ Update https://torale.ai

## Staging Workflow

Triggers on `deploy` label or manual dispatch.

**Deploy via Label:**
1. Add `deploy` label to any PR
2. Workflow runs once
3. To redeploy after new commits: remove and re-add label

**Deploy Manually:**
```bash
# Via GitHub UI: Actions → "Deploy to Staging" → Run workflow
# Via CLI:
gh workflow run staging.yml
```

### Staging Environment

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
| Domains | staging.torale.ai | torale.ai |

**Lifecycle:**
- Staging persists indefinitely
- Each deploy updates existing environment
- No automatic teardown on PR close/merge
- Manual teardown: `helm uninstall torale -n torale-staging`

## Monitoring

### View Workflow Runs

**GitHub UI**: Repository → Actions tab

**CLI**:
```bash
gh run list                # List recent runs
gh run view <run-id>       # View specific run
gh run watch               # Watch live run
```

### Check Deployment Status

```bash
# Production
kubectl get pods -n torale
kubectl get ingress -n torale

# Staging
kubectl get pods -n torale-staging
kubectl get ingress -n torale-staging
```

### View Logs

```bash
# Production
kubectl logs -n torale -l app.kubernetes.io/component=api -f

# Staging
kubectl logs -n torale-staging -l app.kubernetes.io/component=api -f
```

## Troubleshooting

### Build Fails: "Permission denied to push to GCR"

**Solution:**
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### Deployment Fails: "Error from server (Forbidden)"

**Solution:**
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.developer"
```

### Pods Not Starting: ImagePullBackOff

**Check if image exists:**
```bash
gcloud container images list --repository=gcr.io/$PROJECT_ID
kubectl describe pod <pod-name> -n torale
kubectl get deployment torale-api -n torale -o yaml | grep image:
```

### Health Check Timeout

Increase timeout in workflow:
```bash
kubectl rollout status deployment/torale-api -n torale --timeout=10m
```

## Advanced Usage

### Manual Workflow Trigger

```bash
gh workflow run production.yml --ref main
```

### Rollback Deployment

```bash
# Rollback to previous version
kubectl rollout undo deployment/torale-api -n torale

# View rollout history
kubectl rollout history deployment/torale-api -n torale

# Rollback to specific revision
kubectl rollout undo deployment/torale-api -n torale --to-revision=3
```

### Skip CI for Commit

```bash
git commit -m "docs: update README [skip ci]"
```

## Security Best Practices

1. **Never commit GCP keys** to git
2. **Use GitHub secrets** for sensitive data
3. **Limit service account permissions** to minimum required
4. **Enable branch protection** on main
5. **Require PR reviews** before merging
6. **Use Trivy scanning** for vulnerability detection

## Cost Optimization

**GitHub Actions:**
- Public repos: **Unlimited** free minutes
- Private repos: 2,000 minutes/month free
- Typical build: ~3-4 minutes (optimized)

**GKE Resources:**
- Production: ~$12-19/month with Spot pods
- Staging: ~$12-19/month with Spot pods (same resources)

**Docker Build Optimizations:**
1. **Cache mounts**: npm and uv package caches persist across builds
2. **Registry cache**: Falls back to GCR when GitHub Actions cache misses
3. **Parallel builds**: API and frontend build simultaneously via matrix strategy
4. **.dockerignore**: Reduces build context by excluding tests/, research/, etc.
5. **Multi-stage builds**: Frontend and docs use minimal nginx runtime images

**Tips:**
1. Use Spot pods (already configured)
2. Right-size resources: `kubectl top pods`
3. Monitor with GKE dashboard

## Quick Reference

```bash
# Workflow management
gh run list                     # List workflow runs
gh run watch                    # Watch current run
gh workflow run production.yml  # Trigger manually

# Kubernetes
kubectl get pods -n torale               # Production pods
kubectl get pods -n torale-staging       # Staging pods
kubectl logs -n torale -l app=torale-api -f  # API logs

# Deployment
git push origin main                     # Deploy to production
# Add 'deploy' label to PR              # Deploy to staging
```

## Next Steps

- View [Kubernetes Deployment](/deployment/kubernetes)
- Read [Production Best Practices](/deployment/production)
- See [Cost Optimization](/deployment/cost-optimization)
