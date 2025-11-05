# CI/CD Pipeline Documentation

Comprehensive CI/CD pipeline for Torale using Google Cloud Build and GKE.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Usage](#usage)
- [Branch Deployments](#branch-deployments)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## Overview

The Torale CI/CD pipeline provides automated build, test, and deployment workflows with support for:

- **Production Deployments**: Automatic deployment to `torale` namespace on push to `main` branch
- **Branch Deployments**: Isolated environments for feature branches (e.g., `torale-feat-auth` namespace)
- **Security Scanning**: Trivy vulnerability scanning for all Docker images
- **Parallel Builds**: Fast builds using Kaniko with layer caching
- **Health Checks**: Automated post-deployment verification
- **Cost Optimization**: Efficient resource usage with Spot pods and HPA

### Pipeline Stages

```
┌──────────────┐
│  Validate    │ Check project structure, generate metadata
└──────┬───────┘
       │
┌──────▼───────┐
│  Build       │ Build API, Worker, Frontend images (parallel)
└──────┬───────┘
       │
┌──────▼───────┐
│  Scan        │ Security scan with Trivy (parallel)
└──────┬───────┘
       │
┌──────▼───────┐
│  Deploy      │ Deploy to GKE via Helmfile
└──────┬───────┘
       │
┌──────▼───────┐
│  Verify      │ Health checks and rollout verification
└──────────────┘
```

---

## Architecture

### Components

```
GitHub Push → Cloud Build → GCR → GKE Cluster
                    │                  │
                    ├─ Trivy Scan     └─ torale (production)
                    │                  └─ torale-{branch} (branches)
                    └─ Build Artifacts (GCS)
```

### Files

- **`cloudbuild.yaml`**: Production deployment pipeline (main branch)
- **`cloudbuild-branch.yaml`**: Branch deployment pipeline (feature branches)
- **`cloudbuild/`**: Custom builder images and configurations
  - `helm-deploy.Dockerfile`: Custom image with Helm, Helmfile, kubectl
  - `build-helm-image.yaml`: Builds the custom helm-deploy image
- **`scripts/`**: CI/CD helper scripts
  - `ci-setup.sh`: One-time setup for Cloud Build
  - `k8s-cleanup-branch.sh`: Cleanup branch deployments

### Triggers

1. **Production Trigger**: Deploys to `torale` namespace
   - **Trigger**: Push to `main` branch
   - **Config**: `cloudbuild.yaml`
   - **Namespace**: `torale`
   - **Domain**: `torale.ai`, `api.torale.ai`

2. **Branch Trigger**: Deploys to isolated branch namespaces
   - **Trigger**: Push to any branch (except `main`)
   - **Config**: `cloudbuild-branch.yaml`
   - **Namespace**: `torale-{branch-slug}`
   - **Access**: Port-forward or custom subdomain

---

## Setup

### Prerequisites

- GCP project with billing enabled
- GitHub repository connected to Cloud Build
- GKE cluster (`clusterkit`) running
- `gcloud` CLI installed and authenticated

### One-Time Setup

Run the automated setup script:

```bash
just ci-setup
```

This script will:
1. Enable required GCP APIs
2. Grant Cloud Build service account permissions
3. Build custom `helm-deploy` image
4. Create Cloud Build triggers
5. Create GCS bucket for build artifacts

**Manual Setup Steps** (if not using script):

```bash
# 1. Enable APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  container.googleapis.com \
  artifactregistry.googleapis.com

# 2. Grant permissions
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUDBUILD_SA" \
  --role="roles/iam.serviceAccountUser"

# 3. Build helm-deploy image
just ci-build-helm-image

# 4. Create triggers (see Cloud Console)
```

### Connect GitHub Repository

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **Connect Repository**
3. Select **GitHub** and authorize
4. Select your `torale` repository
5. Triggers will be automatically created by `ci-setup.sh`

---

## Usage

### Automatic Deployments

**Production deployment** (main branch):
```bash
git checkout main
git add .
git commit -m "feat: add new feature"
git push origin main
```

This will:
- Trigger `cloudbuild.yaml`
- Build and scan images
- Deploy to `torale` namespace
- Update `torale.ai` and `api.torale.ai`

**Branch deployment** (feature branch):
```bash
git checkout -b feat/user-auth
git add .
git commit -m "feat: implement user auth"
git push origin feat/user-auth
```

This will:
- Trigger `cloudbuild-branch.yaml`
- Build and scan images
- Deploy to `torale-feat-user-auth` namespace
- Create isolated test environment

### Manual Deployments

**Trigger production build manually:**
```bash
just ci-build-prod
```

**Trigger branch build manually:**
```bash
just ci-build-branch
```

**Build specific image:**
```bash
# Build API image
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_IMAGE_NAME=api

# Build frontend image
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_IMAGE_NAME=frontend
```

### View Build Logs

**Recent builds:**
```bash
just ci-logs
```

**Specific build:**
```bash
just ci-logs-build abc123-def456-ghi789
```

**In Cloud Console:**
https://console.cloud.google.com/cloud-build/builds

---

## Branch Deployments

Branch deployments provide isolated environments for testing features before merging to production.

### Features

- **Isolated Namespace**: Each branch gets its own namespace (`torale-{branch-slug}`)
- **Resource Efficient**: Smaller resource requests, no autoscaling
- **No Ingress**: Access via port-forward (or configure custom subdomain)
- **Automatic Cleanup**: Delete old deployments after testing

### Accessing Branch Deployments

**List all branch deployments:**
```bash
just ci-list-branches
```

Output:
```
Branch Deployments:
torale-feat-auth      feat-auth   2025-01-15T10:30:00Z
torale-fix-bug-123    fix-bug-123 2025-01-14T15:20:00Z
```

**Access via port-forward:**
```bash
# API
kubectl port-forward -n torale-feat-auth svc/torale-api 8000:80
# Visit: http://localhost:8000

# Frontend
kubectl port-forward -n torale-feat-auth svc/torale-frontend 8080:80
# Visit: http://localhost:8080
```

**View branch deployment resources:**
```bash
kubectl get all -n torale-feat-auth
```

**View logs:**
```bash
kubectl logs -n torale-feat-auth -l app.kubernetes.io/component=api -f
```

### Cleanup

**Delete specific branch deployment:**
```bash
just ci-cleanup-branch feat-auth
```

**Delete all branches older than 7 days:**
```bash
just ci-cleanup-old-branches
```

**Manual cleanup:**
```bash
kubectl delete namespace torale-feat-auth
```

### Branch Deployment Configuration

Branch deployments use reduced resources for cost optimization:

| Component | Replicas | CPU | Memory | Autoscaling |
|-----------|----------|-----|--------|-------------|
| API | 1 | 50m | 128Mi | Disabled |
| Worker | 1 | 25m | 128Mi | Disabled |
| Frontend | 1 | 25m | 64Mi | Disabled |

Compare to production (see `helm/torale/values-production.yaml`):

| Component | Replicas | CPU | Memory | Autoscaling |
|-----------|----------|-----|--------|-------------|
| API | 1-10 | 50m-500m | 256Mi-512Mi | Enabled |
| Worker | 1-10 | 25m-200m | 128Mi-256Mi | Enabled |
| Frontend | 1-10 | 25m-200m | 64Mi-128Mi | Enabled |

---

## Monitoring

### Build Status

**Cloud Build Dashboard:**
https://console.cloud.google.com/cloud-build/dashboard

**Recent builds:**
```bash
gcloud builds list --limit=20
```

**Build logs:**
```bash
gcloud builds log <BUILD_ID> --stream
```

### Deployment Status

**Check deployment:**
```bash
# Production
kubectl get pods -n torale
kubectl get ingress -n torale

# Branch
kubectl get pods -n torale-{branch-slug}
```

**Check rollout status:**
```bash
kubectl rollout status deployment/torale-api -n torale
```

**View events:**
```bash
kubectl get events -n torale --sort-by='.lastTimestamp'
```

### Artifacts

Build artifacts are stored in GCS:
```
gs://{PROJECT_ID}-build-artifacts/
  ├── production/
  │   └── {BUILD_ID}/
  │       └── build-metadata.env
  └── branches/
      └── {BRANCH_NAME}/
          └── {BUILD_ID}/
              └── build-metadata.env
```

---

## Troubleshooting

### Build Failures

**Issue**: Build fails at image build stage

**Solution**:
```bash
# Check Dockerfile syntax
docker build -f backend/Dockerfile backend/

# View full build logs
gcloud builds log <BUILD_ID> --stream
```

---

**Issue**: Security scan finds critical vulnerabilities

**Solution**:
```bash
# Run Trivy locally to debug
trivy image gcr.io/$PROJECT_ID/torale-api:latest

# Update base image or dependencies
# Note: Scan failures don't block deployment (exit-code=0)
```

---

**Issue**: Deployment step fails

**Solution**:
```bash
# Check cluster access
gcloud container clusters get-credentials clusterkit \
  --region us-central1

# Verify secrets exist
kubectl get secret torale-secrets -n torale

# Check Helm values
helm get values torale -n torale

# Manual deployment
helmfile sync --selector tier=app
```

---

### Deployment Issues

**Issue**: Pods not starting (ImagePullBackOff)

**Solution**:
```bash
# Verify image exists
gcloud container images list --repository=gcr.io/$PROJECT_ID

# Check pod events
kubectl describe pod <POD_NAME> -n torale

# Verify image tag in deployment
kubectl get deployment torale-api -n torale -o yaml | grep image:
```

---

**Issue**: Health checks failing

**Solution**:
```bash
# Check pod logs
kubectl logs <POD_NAME> -n torale

# Check health endpoint manually
kubectl port-forward <POD_NAME> -n torale 8000:8000
curl http://localhost:8000/health

# Check database connection
kubectl logs <POD_NAME> -n torale -c cloud-sql-proxy
```

---

**Issue**: Branch deployment not accessible

**Solution**:
```bash
# Verify namespace exists
kubectl get namespace torale-{branch-slug}

# Check services
kubectl get svc -n torale-{branch-slug}

# Port-forward to test
kubectl port-forward -n torale-{branch-slug} \
  deployment/torale-api 8000:8000
```

---

### Permission Issues

**Issue**: Cloud Build can't access GKE

**Solution**:
```bash
# Grant container.developer role
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/container.developer"
```

---

**Issue**: Cloud Build can't push to GCR

**Solution**:
```bash
# This should be default, but verify:
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/storage.admin"
```

---

## Cost Optimization

### Build Cost Optimization

- **Machine Type**: `E2_HIGHCPU_8` for production (faster), `E2_HIGHCPU_4` for branches
- **Disk Size**: 100GB for production, 50GB for branches
- **Build Timeout**: 30 min for production, 20 min for branches
- **Layer Caching**: Kaniko cache enabled (168h TTL) for faster rebuilds

### Deployment Cost Optimization

- **Spot Pods**: All production pods use Spot nodes (60-91% savings)
- **Right-sized Resources**: Conservative CPU/memory requests
- **HPA**: Auto-scale based on actual load
- **Branch Deployments**: Minimal resources, no autoscaling

### Cost Estimates

**Cloud Build**:
- First 120 build-minutes/day: Free
- Additional: $0.003/build-minute
- Typical build: ~10 minutes = $0.03

**Storage (GCR)**:
- $0.026/GB/month
- ~10 images @ 500MB each = ~$0.13/month

**GKE** (see [k8s-deployment.md](./k8s-deployment.md) for full breakdown):
- Production: ~$12-19/month with Spot pods
- Branch deployments: ~$1-2/month each

### Cleanup Strategy

```bash
# Delete old images
gcloud container images list-tags gcr.io/$PROJECT_ID/torale-api \
  --filter="timestamp.datetime < $(date -d '30 days ago' --iso-8601)" \
  --format="get(digest)" | \
  xargs -I {} gcloud container images delete \
    "gcr.io/$PROJECT_ID/torale-api@{}" --quiet

# Delete old branch deployments
just ci-cleanup-old-branches

# Delete old build artifacts (lifecycle policy: 30 days)
# This is automatic, configured in ci-setup.sh
```

---

## Advanced Features

### Custom Substitutions

Override default values when triggering builds:

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_ENVIRONMENT=staging,_NAMESPACE=torale-staging
```

### Build Notifications

Set up Pub/Sub notifications for build status:

```bash
# Create Pub/Sub topic
gcloud pubsub topics create cloud-builds

# Create subscription
gcloud pubsub subscriptions create build-notifications \
  --topic=cloud-builds

# Configure notification
gcloud builds notification-configs create \
  --topic=cloud-builds \
  --filter="status=SUCCESS OR status=FAILURE"
```

### Rollback Deployments

**Quick rollback:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/torale-api -n torale

# Rollback to specific revision
kubectl rollout undo deployment/torale-api -n torale --to-revision=3

# Check rollout history
kubectl rollout history deployment/torale-api -n torale
```

**Deploy specific image tag:**
```bash
helmfile sync --selector tier=app --set image.tag=abc123def
```

### Blue/Green Deployments

For zero-downtime deployments, use namespace-based blue/green:

```bash
# Deploy to green namespace
helmfile sync --selector tier=app \
  --set global.namespace=torale-green \
  --set image.tag=NEW_VERSION

# Test green deployment
kubectl port-forward -n torale-green svc/torale-api 8000:80

# Switch traffic (update ingress or DNS)
# Then delete old blue deployment
kubectl delete namespace torale-blue
```

---

## Security Best Practices

1. **Never commit secrets** to git (use Kubernetes secrets)
2. **Use Workload Identity** for GCP service authentication
3. **Enable Binary Authorization** for signed images (optional)
4. **Scan images regularly** with Trivy or Container Analysis
5. **Limit Cloud Build SA permissions** to minimum required
6. **Use private GKE cluster** with authorized networks (optional)
7. **Rotate secrets regularly** (API keys, DB passwords)

---

## References

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [GKE Deployment Guide](./k8s-deployment.md)
- [Helm Chart Configuration](../helm/torale/README.md)
- [Justfile Commands](../justfile)

---

## Quick Reference

### Common Commands

```bash
# Setup
just ci-setup                    # One-time CI/CD setup
just ci-build-helm-image         # Build custom helm-deploy image

# Builds
just ci-build-prod               # Trigger production build
just ci-build-branch             # Trigger branch build
just ci-logs                     # View recent builds
just ci-triggers                 # List Cloud Build triggers

# Branch Deployments
just ci-list-branches            # List all branch deployments
just ci-cleanup-branch feat-auth # Delete specific branch
just ci-cleanup-old-branches     # Delete branches >7 days old

# Monitoring
kubectl get pods -n torale       # Production pods
kubectl logs -n torale -l app=torale-api -f  # API logs
kubectl get ingress -n torale    # Ingress status
```

### Useful Links

- **Cloud Build**: https://console.cloud.google.com/cloud-build
- **GKE Workloads**: https://console.cloud.google.com/kubernetes/workload
- **Container Registry**: https://console.cloud.google.com/gcr
- **Build Artifacts**: `gs://{PROJECT_ID}-build-artifacts/`
