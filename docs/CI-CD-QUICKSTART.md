# CI/CD Quick Start Guide

Get your Torale CI/CD pipeline up and running in 10 minutes.

## Prerequisites

- GCP project with billing enabled
- GitHub repository for Torale
- GKE cluster (`clusterkit`) already deployed
- `gcloud` CLI installed and authenticated

## Step 1: Run Setup Script

```bash
# This script does all the heavy lifting
just ci-setup
```

When prompted, enter:
- Your GitHub username/organization
- Your repository name (e.g., `torale`)
- Your main branch name (default: `main`)

The script will:
1. ✅ Enable required GCP APIs
2. ✅ Grant Cloud Build permissions
3. ✅ Build custom helm-deploy image
4. ✅ Create Cloud Build triggers
5. ✅ Create GCS bucket for artifacts

## Step 2: Connect GitHub Repository

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. You should see two triggers already created:
   - `torale-production-deploy` - Deploys on push to main
   - `torale-branch-deploy` - Deploys branches to test environments
3. Click on each trigger and click **"Connect Repository"** if needed
4. Authorize GitHub access
5. Select your `torale` repository

## Step 3: Test Production Deployment

```bash
# Manually trigger a build to test
just ci-build-prod

# Or push to main branch
git checkout main
git commit --allow-empty -m "test: trigger CI/CD"
git push origin main
```

Watch the build:
```bash
just ci-logs
```

Or in the console: https://console.cloud.google.com/cloud-build/builds

## Step 4: Test Branch Deployment

```bash
# Create a test branch
git checkout -b feat/test-ci
git commit --allow-empty -m "test: branch deployment"
git push origin feat/test-ci

# Watch build
just ci-logs

# After build completes, check deployment
just ci-list-branches

# Access your branch deployment
kubectl port-forward -n torale-feat-test-ci svc/torale-api 8000:80
```

## Step 5: Cleanup Test Branch

```bash
# Delete the test branch deployment
just ci-cleanup-branch feat-test-ci

# Delete the git branch
git branch -D feat/test-ci
git push origin --delete feat/test-ci
```

## What Happens Next?

### Automatic Production Deployments
Every push to `main` will:
1. Build Docker images for API, Worker, Frontend
2. Scan for vulnerabilities with Trivy
3. Deploy to production (`torale` namespace)
4. Run health checks
5. Update https://torale.ai

### Automatic Branch Deployments
Every push to any other branch will:
1. Build Docker images
2. Scan for vulnerabilities
3. Deploy to `torale-{branch-name}` namespace
4. Provide isolated test environment
5. Auto-cleanup after 7 days

## Common Commands

```bash
# View recent builds
just ci-logs

# View specific build
just ci-logs-build abc123

# List all branch deployments
just ci-list-branches

# Cleanup old branches
just ci-cleanup-old-branches

# Manual production build
just ci-build-prod

# Manual branch build
just ci-build-branch
```

## Troubleshooting

### Build fails with "Permission denied"
Run `just ci-setup` again to grant proper permissions.

### Branch deployment not accessible
Use port-forward to access:
```bash
kubectl port-forward -n torale-{branch} svc/torale-api 8000:80
```

### Images not pushing to GCR
Check Cloud Build service account has `storage.admin` role.

### Deployment fails
Check secrets exist:
```bash
kubectl get secret torale-secrets -n torale
```

If missing, run:
```bash
just k8s-secrets
```

## Next Steps

- Read the full [CI/CD Documentation](./CI-CD.md)
- Set up [GitHub Actions](./.github/workflows/deploy.yml) as alternative
- Configure [build notifications](./CI-CD.md#build-notifications)
- Set up [automated cleanup](./CI-CD.md#cleanup-strategy)

## Support

- View builds: https://console.cloud.google.com/cloud-build/builds
- View logs: `just ci-logs`
- Check triggers: `just ci-triggers`
- Full docs: [CI-CD.md](./CI-CD.md)
