# CI/CD with GitHub Actions

Automated CI/CD pipeline for Torale using **GitHub Actions** to deploy to GKE.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [How It Works](#how-it-works)
- [Branch Deployments](#branch-deployments)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

The GitHub Actions pipeline provides automated build, test, and deployment workflows:

- **Production Deployments**: Automatic deployment to `torale` namespace on push to `main`
- **Branch Deployments**: Isolated test environments for feature branches
- **Security Scanning**: Trivy vulnerability scanning
- **Parallel Builds**: Fast builds with matrix strategy
- **Health Checks**: Automated post-deployment verification

### Pipeline Jobs

```
Validate → Build (3 parallel) → Scan (3 parallel) → Deploy
   ↓           ↓                     ↓                ↓
Check      API, Worker,         Trivy Scan      Production
Files      Frontend                              or Branch
```

### Workflow Files

- **Production**: `.github/workflows/production.yml`
- **Branch**: `.github/workflows/branch.yml`
- **PR Checks**: `.github/workflows/pr.yml`
- **Build/Scan**: `.github/workflows/build.yml` (reusable)
- **Runtime**: ~5-10 minutes

---

## Setup

### Prerequisites

- GKE cluster (`clusterkit`) running
- `gcloud` CLI installed and authenticated
- GitHub repository

### Keyless Authentication

This setup uses **Workload Identity Federation** for keyless authentication - no service account keys needed!

**Benefits:**
- ✅ No long-lived credentials
- ✅ No key rotation required
- ✅ Automatic short-lived tokens via OIDC
- ✅ More secure than service account keys

### Step 1: Run Setup Script

```bash
./scripts/setup-github-wif.sh
```

This script will:
1. Enable required GCP APIs
2. Create Workload Identity Pool
3. Create Workload Identity Provider
4. Create service account with GKE/GCR permissions
5. Configure Workload Identity binding
6. Output GitHub secrets to add

**Manual setup** (if you prefer):

See the [setup script](../scripts/setup-github-wif.sh) for the full commands.

### Step 2: Add GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **three secrets** (output from setup script):

1. **`GCP_PROJECT_ID`** - Your GCP project ID
2. **`GCP_SERVICE_ACCOUNT`** - Service account email
3. **`GCP_WORKLOAD_IDENTITY_PROVIDER`** - WIF provider path

**Quick add via GitHub CLI:**
```bash
gh secret set GCP_PROJECT_ID --body 'your-project-id'
gh secret set GCP_SERVICE_ACCOUNT --body 'github-actions@your-project.iam.gserviceaccount.com'
gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body 'projects/123/locations/global/...'
```

### Step 3: Done!

That's it! Every push now triggers keyless authenticated deployments.

**Learn more:**
- [Workload Identity Federation](https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions)

---

## How It Works

### Production Deployment (main branch)

```bash
git checkout main
git commit -m "feat: new feature"
git push origin main
```

This triggers:
1. ✅ Validate project structure
2. ✅ Build API, Worker, Frontend images (parallel)
3. ✅ Scan for vulnerabilities with Trivy
4. ✅ Deploy to `torale` namespace via Helmfile
5. ✅ Verify rollout and health checks
6. ✅ Update https://torale.ai

### Branch Deployment (feature branches)

```bash
git checkout -b feat/user-auth
git commit -m "feat: implement auth"
git push origin feat/user-auth
```

This triggers:
1. ✅ Build and scan images
2. ✅ Deploy to `torale-feat-user-auth` namespace
3. ✅ Create isolated test environment
4. ✅ Minimal resources (1 replica, no autoscaling)

### Pull Requests

Pull requests trigger **validation and build only** (no deployment):
- ✅ Validate project structure
- ✅ Build all images
- ✅ Security scanning

---

## Branch Deployments

Branch deployments provide isolated environments for testing.

### Features

- **Isolated Namespace**: `torale-{branch-slug}`
- **Cost Efficient**: 1 replica, no autoscaling
- **No Public Access**: Access via port-forward
- **Auto-labeled**: `type=branch-deployment`

### List Branch Deployments

```bash
just list-branches
```

Output:
```
Branch Deployments:
torale-feat-auth      feat-auth   2025-01-15T10:30:00Z
torale-fix-bug-123    fix-bug-123 2025-01-14T15:20:00Z
```

### Access Branch Deployment

```bash
# Get namespace name from list-branches
NAMESPACE=torale-feat-auth

# Port-forward API
kubectl port-forward -n $NAMESPACE svc/torale-api 8000:80

# Port-forward Frontend
kubectl port-forward -n $NAMESPACE svc/torale-frontend 8080:80
```

Then visit:
- API: http://localhost:8000
- Frontend: http://localhost:8080

### View Branch Logs

```bash
kubectl logs -n torale-feat-auth -l app.kubernetes.io/component=api -f
```

### Cleanup Branch Deployment

```bash
# Delete specific branch
just cleanup-branch feat-auth

# Delete all branches older than 7 days
just cleanup-old-branches
```

---

## Monitoring

### View Workflow Runs

**GitHub UI**: Repository → Actions tab

**CLI** (using gh):
```bash
# List recent runs
gh run list

# View specific run
gh run view <run-id>

# Watch live run
gh run watch
```

### Check Deployment Status

```bash
# Production
kubectl get pods -n torale
kubectl get ingress -n torale

# Branch
kubectl get pods -n torale-{branch-slug}
```

### View Build Logs

In GitHub Actions UI:
1. Go to Actions tab
2. Click on workflow run
3. Click on job (e.g., "Build api")
4. View logs for each step

---

## Troubleshooting

### Build Fails: "Permission denied to push to GCR"

**Issue**: Service account lacks permissions

**Solution**:
```bash
PROJECT_ID=your-project-id

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

---

### Deployment Fails: "Error from server (Forbidden)"

**Issue**: Service account can't access GKE

**Solution**:
```bash
PROJECT_ID=your-project-id

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.developer"
```

---

### Branch Deployment: "secret torale-secrets not found"

**Issue**: Production secrets don't exist yet

**Solution**:
```bash
# Create secrets in production namespace first
just k8s-secrets

# Then redeploy branch
git commit --allow-empty -m "trigger: redeploy"
git push
```

---

### Pods Not Starting: ImagePullBackOff

**Issue**: Image doesn't exist or wrong tag

**Solution**:
```bash
# Check if image exists
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Check pod details
kubectl describe pod <pod-name> -n torale

# Verify image tag
kubectl get deployment torale-api -n torale -o yaml | grep image:
```

---

### Health Check Timeout

**Issue**: Deployment takes longer than 5 minutes

**Solution**: Increase timeout in workflow:
```yaml
# .github/workflows/production.yml or .github/workflows/branch.yml
kubectl rollout status deployment/torale-api -n torale --timeout=10m
```

---

## Advanced Usage

### Manual Workflow Trigger

Via GitHub UI:
1. Go to Actions tab
2. Select "Deploy to GKE" workflow
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

Via CLI:
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

Add `[skip ci]` to commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

### Deploy Specific Image Tag

Edit workflow file to use specific tag instead of `${{ github.sha }}`:
```yaml
env:
  IMAGE_TAG: abc123def  # Or use a specific commit SHA
```

---

## Configuration

### Workflow Triggers

Edit `.github/workflows/production.yml` or `.github/workflows/branch.yml`:

```yaml
on:
  push:
    branches:
      - main
      - 'feat/**'    # Feature branches
      - 'fix/**'     # Bug fix branches
      - 'staging'    # Add staging branch
```

### Branch Deployment Resources

Edit branch deployment step to adjust resources:

```yaml
--set api.resources.requests.cpu=100m \
--set api.resources.requests.memory=256Mi
```

### Namespace Naming

Branch namespaces use sanitized branch names:
- `feat/user-auth` → `torale-feat-user-auth`
- `fix/bug-123` → `torale-fix-bug-123`
- Max 30 characters for branch slug

---

## Cost Optimization

### GitHub Actions Minutes

- Public repos: **Unlimited** free
- Private repos: 2,000 minutes/month free
- Typical build: ~10 minutes
- Estimated cost: **$0** for public repos

### GKE Resources

**Production** (torale namespace):
- API: 1-10 replicas (HPA enabled)
- Worker: 1-10 replicas (HPA enabled)
- Frontend: 1-10 replicas (HPA enabled)
- **Cost**: ~$12-19/month with Spot pods

**Branch deployments**:
- API: 1 replica (no autoscaling)
- Worker: 1 replica (no autoscaling)
- Frontend: 1 replica (no autoscaling)
- **Cost**: ~$1-2/month each

### Tips

1. **Delete old branches**: Use `just cleanup-old-branches`
2. **Use Spot pods**: Already configured in Helm values
3. **Right-size resources**: Monitor with `kubectl top pods`
4. **Limit branch deploys**: Only deploy branches you actively test

---

## Security Best Practices

1. **Never commit GCP keys** to git
2. **Use GitHub secrets** for all sensitive data
3. **Limit service account permissions** to minimum required
4. **Regularly review IAM permissions** to ensure they follow the principle of least privilege
5. **Enable branch protection** on main branch
6. **Require PR reviews** before merging
7. **Use Trivy scanning** for vulnerability detection

---

## Quick Reference

### Common Commands

```bash
# Branch management
just list-branches              # List all branch deployments
just cleanup-branch feat-auth   # Delete specific branch
just cleanup-old-branches       # Delete branches >7 days old

# Kubernetes
kubectl get pods -n torale      # Production pods
kubectl get pods -n torale-{branch-slug}  # Branch pods
kubectl logs -n torale -l app=torale-api -f  # API logs

# GitHub CLI
gh run list                     # List workflow runs
gh run watch                    # Watch current run
gh workflow run production.yml  # Trigger manually
```

### Useful Links

- **Actions**: https://github.com/prassanna-ravishankar/torale/actions
- **Container Registry**: https://console.cloud.google.com/gcr
- **GKE Workloads**: https://console.cloud.google.com/kubernetes/workload
