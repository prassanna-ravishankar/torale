# Deploying Torale to GKE ClusterKit

This guide explains how to deploy Torale (API + Workers + Frontend + Temporal) to the ClusterKit GKE Autopilot cluster.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [One-Time Setup](#one-time-setup)
- [Deployment](#deployment)
- [Verification](#verification)
- [DNS Configuration](#dns-configuration)
- [Managing the Deployment](#managing-the-deployment)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install kubectl
gcloud components install kubectl

# Install helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install helmfile (macOS)
brew install helmfile

# Install helmfile (Linux)
wget https://github.com/helmfile/helmfile/releases/download/v0.158.0/helmfile_linux_amd64
chmod +x helmfile_linux_amd64
sudo mv helmfile_linux_amd64 /usr/local/bin/helmfile

# Authenticate with GCP
gcloud auth login
gcloud config set project baldmaninc
```

### Cluster Access

Get cluster credentials:

```bash
just k8s-auth

# Or directly:
gcloud container clusters get-credentials clusterkit \
  --region us-central1 \
  --project baldmaninc
```

Verify access:

```bash
kubectl get nodes
kubectl get namespaces
```

---

## Architecture Overview

```
torale.ai (frontend - React + nginx)
    ↓
api.torale.ai (API - FastAPI)
    ↓
├── Cloud SQL PostgreSQL (managed database)
├── Self-hosted Temporal (via Helm)
└── Workers (Temporal client)
```

### Components

1. **Frontend**: React SPA served by nginx (Spot pods, auto-scaling)
2. **API**: FastAPI with Cloud SQL Proxy sidecar + init container for migrations
3. **Workers**: Temporal workers with Cloud SQL Proxy sidecar
4. **Temporal**: Self-hosted Temporal server + UI (via official Helm charts)
5. **Database**: Cloud SQL PostgreSQL 16 (managed, zonal for cost)

### Cost Optimization

- **Spot Pods**: All pods use Spot nodes (60-91% savings)
- **Right-sized Resources**: Conservative CPU/memory requests (100m CPU, 256Mi RAM)
- **HPA**: Auto-scale based on CPU (min 2, max 10 replicas)
- **Zonal DB**: Cloud SQL uses zonal (not regional) availability

---

## One-Time Setup

### 1. Create Cloud SQL Instance

Run the automated setup script:

```bash
just k8s-setup

# Or manually run:
./scripts/k8s-setup-cloudsql.sh
```

This script will:
- Create Cloud SQL PostgreSQL instance (db-f1-micro, ~$7/month)
- Set database password
- Create `torale` database
- Setup IAM service account for Cloud SQL Proxy
- Configure Workload Identity for GKE

The script will save connection details to `.cloud-sql-info` (gitignored).

**Manual steps** (if not using script):

```bash
# Create Cloud SQL instance
gcloud sql instances create torale-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --backup \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB \
  --no-assign-ip

# Set password
gcloud sql users set-password torale \
  --instance=torale-db \
  --password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create torale \
  --instance=torale-db

# Get connection name
gcloud sql instances describe torale-db --format='value(connectionName)'
# Output: baldmaninc:us-central1:torale-db
```

### 2. Setup Workload Identity

**If using the script**, this is done automatically. Otherwise:

```bash
# Create GCP service account
gcloud iam service-accounts create cloudsql-proxy \
  --display-name="Cloud SQL Proxy for Torale"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding baldmaninc \
  --member="serviceAccount:cloudsql-proxy@baldmaninc.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Enable Workload Identity binding
gcloud iam service-accounts add-iam-policy-binding \
  cloudsql-proxy@baldmaninc.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:baldmaninc.svc.id.goog[production/torale-sa]"
```

### 3. Create Kubernetes Secrets

```bash
just k8s-secrets

# Or manually run:
./scripts/k8s-create-secrets.sh
```

This script will:
- Read from your `.env` file
- Prompt for missing required values (GOOGLE_API_KEY, SECRET_KEY, DB_PASSWORD)
- Create Kubernetes secret in `production` namespace

Required secrets:
- `GOOGLE_API_KEY` (required) - Google AI Studio API key
- `SECRET_KEY` (required) - JWT secret (generate with `openssl rand -hex 32`)
- `DB_PASSWORD` (required) - Database password from Cloud SQL setup
- `CLERK_SECRET_KEY` (required) - Clerk authentication
- `OPENAI_API_KEY` (optional) - Fallback AI provider
- `ANTHROPIC_API_KEY` (optional) - Fallback AI provider
- `NOTIFICATION_API_KEY` (optional) - Future notification service

### 4. Configure Production Values

Create `helm/torale/values-production.yaml` (gitignored):

```yaml
# Override default values for production

global:
  projectId: baldmaninc
  region: us-central1

domains:
  frontend: torale.ai
  api: api.torale.ai

image:
  tag: latest  # Will be overridden by Cloud Build with commit SHA

# Update with your actual Cloud SQL connection name
database:
  connectionName: "baldmaninc:us-central1:torale-db"
  name: torale
  user: torale

# Point to self-hosted Temporal in cluster
temporal:
  host: temporal.temporal.svc.cluster.local:7233
  namespace: default

# Or point to Temporal Cloud (if you switch later)
# temporal:
#   host: your-namespace.tmprl.cloud:7233
#   namespace: your-namespace

# Production resource sizing (start conservative, scale up if needed)
api:
  replicaCount: 2
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

worker:
  replicaCount: 2
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1Gi

frontend:
  replicaCount: 2
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi
```

---

## Deployment

### Deploy Everything

```bash
# Deploy Temporal + Torale application
just k8s-deploy-all

# Or via helmfile directly:
helmfile sync
```

### Deploy Selectively

```bash
# Deploy only Temporal
just k8s-deploy-temporal

# Deploy only Torale app
just k8s-deploy-app
```

### What Happens During Deployment

1. **Temporal Deployment** (~2-3 minutes):
   - Creates `temporal` namespace
   - Deploys Temporal server with embedded PostgreSQL
   - Deploys Temporal UI
   - Deploys Temporal admin tools

2. **Torale Deployment** (~5-10 minutes):
   - Creates `production` namespace
   - Creates ServiceAccount with Workload Identity annotation
   - Creates ConfigMap with non-sensitive config
   - Deploys API (with init container for migrations)
   - Deploys Workers
   - Deploys Frontend
   - Creates GCE Ingress
   - Provisions GKE Managed Certificate (takes 10-15 minutes)

---

## Verification

### Check Deployment Status

```bash
just k8s-status

# Or manually check:
kubectl get pods -n production
kubectl get pods -n temporal
kubectl get ingress -n production
kubectl get managedcertificate -n production
```

Expected output:
```
✓ API pods: 2/2 ready
✓ Worker pods: 2/2 ready
✓ Frontend pods: 2/2 ready
✓ Temporal pods: Running
✓ Ingress IP: 34.120.xxx.xxx
⚠ Certificate status: Provisioning (takes 10-15 minutes)
```

### Check Logs

```bash
# API logs
just k8s-logs-api

# Worker logs
just k8s-logs-workers

# Frontend logs
just k8s-logs-frontend

# Temporal logs
just k8s-logs-temporal
```

### Port Forward for Local Access

```bash
# Access API locally
just k8s-port-forward-api
# Now available at http://localhost:8000

# Access Temporal UI locally
just k8s-port-forward-temporal
# Now available at http://localhost:8080
```

---

## DNS Configuration

### Get Ingress IP

```bash
kubectl get ingress -n production
```

Note the `ADDRESS` field (e.g., `34.120.xxx.xxx`).

### Add DNS Records

Add these A records to your domain (torale.ai) in Cloudflare or your DNS provider:

```
torale.ai     →  34.120.xxx.xxx
api.torale.ai →  34.120.xxx.xxx
```

### Verify DNS Propagation

```bash
dig torale.ai +short
dig api.torale.ai +short
```

Both should return your ingress IP.

### SSL Certificate Provisioning

After DNS is configured, the GKE Managed Certificate will provision automatically.

**Check certificate status:**

```bash
kubectl describe managedcertificate torale-cert -n production
```

**Certificate states:**
- `Provisioning` - Certificate being created (normal, takes 10-15 minutes)
- `FailedNotVisible` - DNS not pointing to ingress yet (check DNS records)
- `Active` - Certificate ready and serving! ✓

**Once Active**, your sites will be accessible at:
- **Frontend**: https://torale.ai
- **API**: https://api.torale.ai

---

## Managing the Deployment

### Update Application

When you push to GitHub, Cloud Build automatically:
1. Builds new Docker images
2. Pushes to GCR
3. Deploys via Helmfile with new image tag

**Manual deployment:**

```bash
# Rebuild and deploy
gcloud builds submit --config=cloudbuild.yaml

# Or just redeploy existing images
just k8s-deploy-app
```

### Scale Deployments

```bash
# Scale API manually
kubectl scale deployment torale-api -n production --replicas=5

# Scale workers
kubectl scale deployment torale-worker -n production --replicas=3

# Or update values-production.yaml and redeploy
```

### Restart Deployments

```bash
# Restart API (triggers rolling update)
just k8s-restart-api

# Restart workers
just k8s-restart-workers

# Restart frontend
just k8s-restart-frontend
```

### View Resource Usage

```bash
# Check pod resource usage
kubectl top pods -n production

# Check node usage
kubectl top nodes
```

### Update Configuration

1. Edit `helm/torale/values-production.yaml`
2. Redeploy: `just k8s-deploy-app`

### Update Secrets

```bash
# Recreate secrets
just k8s-secrets

# Or update specific secret value
kubectl create secret generic torale-secrets \
  --from-literal=GOOGLE_API_KEY=new-key \
  --dry-run=client -o yaml | kubectl apply -n production -f -

# Restart pods to pick up new secrets
just k8s-restart-api
just k8s-restart-workers
```

---

## Cost Optimization

### Current Configuration

| Component | Replicas | CPU (request) | Memory (request) | Monthly Cost |
|-----------|----------|---------------|------------------|--------------|
| API | 2 | 200m | 512Mi | ~$8 |
| Workers | 2 | 200m | 512Mi | ~$8 |
| Frontend | 2 | 100m | 128Mi | ~$4 |
| Temporal | 1 | 200m | 512Mi | ~$4 |
| Cloud SQL | 1 | db-f1-micro | 10GB | ~$7 |
| **Total** | | | | **~$31/month** |

**With Spot pods:** ~$12-19/month (60-91% savings on compute)

### Optimization Tips

1. **Use Spot Pods**: Already configured! All pods use Spot nodes.

2. **Right-size Resources**: Start small, monitor with `kubectl top pods`, adjust as needed.

3. **HPA is Enabled**: Automatically scales based on CPU (min 2, max 10).

4. **Reduce Replicas** (for dev/staging):
   ```yaml
   # helm/torale/values-production.yaml
   api:
     replicaCount: 1
   worker:
     replicaCount: 1
   frontend:
     replicaCount: 1
   ```

5. **Upgrade Cloud SQL** (if needed for production traffic):
   ```bash
   gcloud sql instances patch torale-db \
     --tier=db-g1-small  # ~$25/month
   ```

6. **Switch to Temporal Cloud** (to reduce cluster resources):
   - Sign up at temporal.io
   - Update `values-production.yaml`:
     ```yaml
     temporal:
       host: your-namespace.tmprl.cloud:7233
     ```
   - Delete Temporal from cluster: `helmfile destroy --selector tier=temporal`

### Monitor Costs

```bash
# Check resource requests (this is what you pay for in Autopilot)
kubectl describe pods -n production | grep -A 2 "Requests:"

# Total resource usage
kubectl top nodes
```

---

## Troubleshooting

### Pods Won't Start

**Check pod status:**

```bash
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
```

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `ImagePullBackOff` | Image doesn't exist in GCR | Run Cloud Build: `gcloud builds submit` |
| `CrashLoopBackOff` | App crashes on startup | Check logs: `just k8s-logs-api` |
| `Pending` | No nodes available | Check resource requests are reasonable |
| `OOMKilled` | Out of memory | Increase memory limit in values.yaml |

### Can't Access Application

**Check service:**

```bash
kubectl get service -n production
kubectl get endpoints torale-api -n production
```

If endpoints are empty, check that pod labels match service selector.

**Check ingress:**

```bash
kubectl get ingress -n production
kubectl describe ingress torale -n production
```

**Check DNS:**

```bash
dig torale.ai +short
dig api.torale.ai +short
```

Should return the ingress IP.

### SSL Certificate Not Working

**Check certificate status:**

```bash
kubectl describe managedcertificate torale-cert -n production
```

**Common status meanings:**

- `Provisioning` → Wait 10-15 minutes
- `FailedNotVisible` → DNS doesn't point to ingress IP yet
- `Active` → Working!

**Debug steps:**

```bash
# 1. Verify Ingress has IP
kubectl get ingress torale -n production

# 2. Verify DNS points to that IP
dig torale.ai +short

# 3. Wait for DNS propagation (5-10 mins)

# 4. Check certificate again
kubectl describe managedcertificate torale-cert -n production
```

### Database Connection Issues

**Check Cloud SQL Proxy logs:**

```bash
kubectl logs <pod-name> -n production -c cloud-sql-proxy
```

**Common issues:**

- **Connection refused**: Check Workload Identity is configured
- **Permission denied**: Verify GCP service account has `roles/cloudsql.client`
- **Instance not found**: Check `database.connectionName` in values-production.yaml

**Test connection manually:**

```bash
# Port forward to test database
kubectl port-forward deployment/torale-api -n production 5432:5432

# Connect via psql
psql -h localhost -U torale -d torale
```

### Workers Not Processing Tasks

**Check worker logs:**

```bash
just k8s-logs-workers
```

**Check Temporal connection:**

```bash
# Port forward Temporal UI
just k8s-port-forward-temporal

# Visit http://localhost:8080 and check:
# - Are workers registered?
# - Are tasks being scheduled?
# - Are there any workflow errors?
```

**Verify TEMPORAL_HOST env var:**

```bash
kubectl exec deployment/torale-worker -n production -- env | grep TEMPORAL
```

### High Costs

**Check resource usage:**

```bash
# See what's using resources
kubectl top nodes
kubectl top pods --all-namespaces

# Check pod requests
kubectl describe pods -n production | grep -A 2 "Requests:"
```

**Optimization checklist:**

- [ ] Using Spot pods? (check `nodeSelector` in deployments)
- [ ] Resource requests match actual usage? (compare with `kubectl top pods`)
- [ ] Using HPA to scale down during low traffic?
- [ ] Idle pods/deployments deleted?
- [ ] Using ClusterIP + Ingress instead of multiple LoadBalancers?

---

## Delete Everything

**Warning**: This will delete all resources and data!

```bash
# Delete Torale app only
helmfile destroy --selector tier=app

# Delete everything (Temporal + Torale)
just k8s-destroy

# Also delete Cloud SQL instance
gcloud sql instances delete torale-db
```

---

## Getting Help

**Useful commands:**

```bash
# View all resources
kubectl get all -n production
kubectl get all -n temporal

# View events
kubectl get events -n production --sort-by='.lastTimestamp'

# Describe resource
kubectl describe <resource-type> <resource-name> -n production

# Get shell in pod
kubectl exec -it <pod-name> -n production -- /bin/sh

# View full deployment config
helm get values torale -n production
```

**Check the logs:**

- API logs: `just k8s-logs-api`
- Worker logs: `just k8s-logs-workers`
- Temporal UI: `just k8s-port-forward-temporal` → http://localhost:8080

**Still stuck?** Check:
- GCP Cloud Build logs (build failures)
- GKE Workloads dashboard (resource issues)
- Cloud SQL Operations log (database issues)
