# Deploying Applications to ClusterKit

This guide explains how to deploy your applications to the ClusterKit GKE Autopilot cluster.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Patterns](#deployment-patterns)
- [Helm Deployments](#helm-deployments)
- [Database Configuration](#database-configuration)
- [Exposing Your Application](#exposing-your-application)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Cost Optimization](#cost-optimization)
- [Best Practices](#best-practices)
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

# Authenticate with GCP
gcloud auth login
gcloud config set project baldmaninc
```

### Cluster Access

Get cluster credentials:

```bash
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

## Quick Start

### 1. Deploy a Simple Application

```bash
# Create deployment
kubectl create deployment my-app \
  --image=nginx:latest \
  --replicas=2

# Expose as LoadBalancer
kubectl expose deployment my-app \
  --port=80 \
  --target-port=80 \
  --type=LoadBalancer
```

### 2. Wait for External IP

```bash
kubectl get service my-app --watch
```

### 3. Access Your App

Once you see an `EXTERNAL-IP`, visit it in your browser:

```bash
curl http://<EXTERNAL-IP>
```

### 4. Clean Up

```bash
kubectl delete service my-app
kubectl delete deployment my-app
```

---

## Deployment Patterns

### Pattern 1: Simple Deployment with Service

**Use for:** Web applications, APIs, microservices

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      # Enable Spot Pods for 60-91% cost savings
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: gcr.io/baldmaninc/my-app:latest
        ports:
        - containerPort: 8080
        # Right-size resources for cost optimization
        resources:
          requests:
            cpu: 100m      # 0.1 vCPU
            memory: 128Mi
          limits:
            cpu: 500m      # 0.5 vCPU
            memory: 512Mi
        # Health checks
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

Apply:

```bash
kubectl apply -f deployment.yaml
```

### Pattern 2: Ingress with Custom Domain

**Use for:** Production apps with custom domains (e.g., app.yourdomain.com)

```yaml
# app-with-ingress.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: gcr.io/baldmaninc/my-app:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 1000m
            memory: 1Gi
---
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    # DNS will be automatically managed by ExternalDNS
    external-dns.alpha.kubernetes.io/hostname: my-app.yourdomain.com
spec:
  type: ClusterIP  # Internal only, exposed via Ingress
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    # Use GKE Ingress
    kubernetes.io/ingress.class: "gce"
    # Enable automatic SSL certificate
    networking.gke.io/managed-certificates: "my-app-cert"
    # Optional: Force HTTPS redirect
    networking.gke.io/v1beta1.FrontendConfig: "ssl-redirect"
spec:
  rules:
  - host: my-app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
---
# Managed SSL Certificate (auto-provisioned by Google)
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: my-app-cert
spec:
  domains:
  - my-app.yourdomain.com
---
# Optional: Force HTTPS redirect
apiVersion: networking.gke.io/v1beta1
kind: FrontendConfig
metadata:
  name: ssl-redirect
spec:
  redirectToHttps:
    enabled: true
```

Apply:

```bash
kubectl apply -f app-with-ingress.yaml
```

**What happens automatically:**

1. **GKE Ingress** creates a Google Cloud Load Balancer
2. **ExternalDNS** creates a Cloudflare DNS A record pointing to the load balancer
3. **GKE Managed Certificate** provisions a Let's Encrypt SSL certificate
4. Your app is accessible at `https://my-app.yourdomain.com`

**Check status:**

```bash
# Wait for certificate provisioning (takes ~10-15 minutes)
kubectl describe managedcertificate my-app-cert

# Check DNS record was created
dig my-app.yourdomain.com

# Get Ingress IP
kubectl get ingress my-app
```

### Pattern 3: Multiple Apps with Path-Based Routing

**Use for:** Microservices on shared domain

```yaml
# multi-app-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-app
  annotations:
    kubernetes.io/ingress.class: "gce"
    networking.gke.io/managed-certificates: "multi-app-cert"
spec:
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 80
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 80
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: product-service
            port:
              number: 80
---
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: multi-app-cert
spec:
  domains:
  - api.yourdomain.com
```

---

## Helm Deployments

**Helm** is the package manager for Kubernetes. Use it to deploy complex applications with pre-configured charts.

### Install Helm

```bash
# Install Helm CLI
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installation
helm version
```

### Pattern 1: Deploy Public Charts

**Example: Deploy PostgreSQL**

```bash
# Add Bitnami repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install my-postgres bitnami/postgresql \
  --namespace database \
  --create-namespace \
  --set auth.postgresPassword=supersecret \
  --set primary.persistence.size=10Gi \
  --set primary.resources.requests.cpu=100m \
  --set primary.resources.requests.memory=256Mi \
  --set primary.nodeSelector."cloud\.google\.com/gke-spot"=true \
  --set primary.tolerations[0].key=cloud.google.com/gke-spot \
  --set primary.tolerations[0].operator=Equal \
  --set primary.tolerations[0].value=true \
  --set primary.tolerations[0].effect=NoSchedule

# Check status
helm status my-postgres -n database

# Get connection info
kubectl get secret --namespace database my-postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d
```

**Example: Deploy Redis**

```bash
# Install Redis
helm install my-redis bitnami/redis \
  --namespace cache \
  --create-namespace \
  --set master.resources.requests.cpu=50m \
  --set master.resources.requests.memory=64Mi \
  --set master.nodeSelector."cloud\.google\.com/gke-spot"=true \
  --set master.tolerations[0].key=cloud.google.com/gke-spot \
  --set master.tolerations[0].operator=Equal \
  --set master.tolerations[0].value=true \
  --set master.tolerations[0].effect=NoSchedule

# Get password
export REDIS_PASSWORD=$(kubectl get secret --namespace cache my-redis -o jsonpath="{.data.redis-password}" | base64 -d)

# Connect from within cluster
redis-cli -h my-redis-master.cache.svc.cluster.local -a $REDIS_PASSWORD
```

### Pattern 2: Custom Helm Charts

**Create your own chart:**

```bash
# Create chart structure
helm create my-app

# Directory structure
my-app/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default configuration
├── charts/             # Chart dependencies
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── _helpers.tpl
```

**values.yaml (with Spot pods and cost optimization):**

```yaml
replicaCount: 2

image:
  repository: gcr.io/baldmaninc/my-app
  tag: "1.0.0"
  pullPolicy: IfNotPresent

# Cost optimization: Use Spot pods
nodeSelector:
  cloud.google.com/gke-spot: "true"

tolerations:
- key: cloud.google.com/gke-spot
  operator: Equal
  value: "true"
  effect: NoSchedule

# Right-size resources
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: gce
  annotations:
    networking.gke.io/managed-certificates: "my-app-cert"
  hosts:
  - host: my-app.yourdomain.com
    paths:
    - path: /
      pathType: Prefix

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

# Database connection (Cloud SQL)
database:
  enabled: true
  host: 127.0.0.1  # Cloud SQL Proxy
  port: 5432
  name: myapp_production
  user: postgres
  passwordSecret: db-credentials
  passwordKey: password

# Cloud SQL Proxy sidecar
cloudsql:
  enabled: true
  connectionName: baldmaninc:us-central1:clusterkit-db
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
```

**templates/deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - name: http
          containerPort: {{ .Values.service.targetPort }}
        {{- if .Values.database.enabled }}
        env:
        - name: DB_HOST
          value: {{ .Values.database.host }}
        - name: DB_PORT
          value: "{{ .Values.database.port }}"
        - name: DB_NAME
          value: {{ .Values.database.name }}
        - name: DB_USER
          value: {{ .Values.database.user }}
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ .Values.database.passwordSecret }}
              key: {{ .Values.database.passwordKey }}
        {{- end }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
      {{- if .Values.cloudsql.enabled }}
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
        args:
        - "--structured-logs"
        - "--port={{ .Values.database.port }}"
        - "{{ .Values.cloudsql.connectionName }}"
        resources:
          {{- toYaml .Values.cloudsql.resources | nindent 12 }}
      {{- end }}
```

**Install your chart:**

```bash
# Test rendering
helm template my-app ./my-app

# Dry-run install
helm install my-app ./my-app --dry-run --debug

# Actually install
helm install my-app ./my-app \
  --namespace production \
  --create-namespace

# Upgrade existing release
helm upgrade my-app ./my-app \
  --namespace production

# Rollback if needed
helm rollback my-app -n production
```

### Pattern 3: Using Helmfile (Multiple Charts)

**Install Helmfile:**

```bash
# macOS
brew install helmfile

# Linux
wget https://github.com/helmfile/helmfile/releases/download/v0.158.0/helmfile_linux_amd64
chmod +x helmfile_linux_amd64
sudo mv helmfile_linux_amd64 /usr/local/bin/helmfile
```

**helmfile.yaml (deploy multiple apps):**

```yaml
repositories:
- name: bitnami
  url: https://charts.bitnami.com/bitnami

releases:
# PostgreSQL
- name: postgres
  namespace: database
  chart: bitnami/postgresql
  version: 13.2.0
  values:
  - auth:
      postgresPassword: supersecret
    primary:
      persistence:
        size: 20Gi
      resources:
        requests:
          cpu: 200m
          memory: 512Mi
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule

# Redis
- name: redis
  namespace: cache
  chart: bitnami/redis
  version: 18.4.0
  values:
  - master:
      resources:
        requests:
          cpu: 50m
          memory: 128Mi
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule

# Your app
- name: my-app
  namespace: production
  chart: ./my-app
  values:
  - replicaCount: 3
    image:
      tag: "v1.2.3"
```

**Deploy everything:**

```bash
# Install/upgrade all releases
helmfile sync

# Only install specific release
helmfile -l name=postgres sync

# Diff before applying
helmfile diff
```

### Useful Helm Commands

```bash
# List installed releases
helm list --all-namespaces

# Get release values
helm get values my-app -n production

# View release history
helm history my-app -n production

# Uninstall release
helm uninstall my-app -n production

# Search for charts
helm search hub redis
helm search repo bitnami/

# Show chart info
helm show chart bitnami/postgresql
helm show values bitnami/postgresql

# Download chart
helm pull bitnami/postgresql --untar
```

---

## Database Configuration

### Recommended: Cloud SQL (Managed PostgreSQL/MySQL)

**For most projects, use Google Cloud SQL** instead of running databases in Kubernetes.

**Why Cloud SQL:**
- ✅ Automatic backups and point-in-time recovery
- ✅ High availability and failover
- ✅ Automatic patches and upgrades
- ✅ No Spot pod interruptions
- ✅ Professional monitoring and support
- ✅ Better performance (optimized hardware)

### Setup Cloud SQL PostgreSQL

**1. Create Cloud SQL instance:**

```bash
# Create PostgreSQL instance (small, zonal)
gcloud sql instances create clusterkit-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --backup \
  --availability-type=zonal \
  --storage-type=SSD \
  --storage-size=10GB

# For production HA (costs ~2x):
gcloud sql instances create clusterkit-db-prod \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=us-central1 \
  --backup \
  --availability-type=regional \
  --storage-type=SSD \
  --storage-size=20GB
```

**2. Set database password:**

```bash
# Set postgres user password
gcloud sql users set-password postgres \
  --instance=clusterkit-db \
  --password=YOUR_SECURE_PASSWORD_HERE

# Or generate secure password
export DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users set-password postgres \
  --instance=clusterkit-db \
  --password=$DB_PASSWORD
```

**3. Create application database:**

```bash
# Create database
gcloud sql databases create myapp_production \
  --instance=clusterkit-db

# Get connection name (needed for Cloud SQL Proxy)
export CONNECTION_NAME=$(gcloud sql instances describe clusterkit-db --format='value(connectionName)')
echo $CONNECTION_NAME
# Output: baldmaninc:us-central1:clusterkit-db
```

**4. Setup IAM for Cloud SQL Proxy:**

```bash
# Create GCP service account
gcloud iam service-accounts create cloudsql-proxy \
  --display-name="Cloud SQL Proxy for GKE"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding baldmaninc \
  --member="serviceAccount:cloudsql-proxy@baldmaninc.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Enable Workload Identity binding
gcloud iam service-accounts add-iam-policy-binding \
  cloudsql-proxy@baldmaninc.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:baldmaninc.svc.id.goog[default/cloudsql-proxy]"

# Create Kubernetes service account
kubectl create serviceaccount cloudsql-proxy

# Annotate for Workload Identity
kubectl annotate serviceaccount cloudsql-proxy \
  iam.gke.io/gcp-service-account=cloudsql-proxy@baldmaninc.iam.gserviceaccount.com
```

**5. Deploy app with Cloud SQL Proxy sidecar:**

```yaml
# app-with-cloudsql.yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  password: YOUR_SECURE_PASSWORD_HERE
  username: postgres
  database: myapp_production
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      # Use Workload Identity service account
      serviceAccountName: cloudsql-proxy

      # Cost optimization
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule

      containers:
      # Application container
      - name: app
        image: gcr.io/baldmaninc/my-app:latest
        ports:
        - containerPort: 8080
        env:
        # Database connection via Cloud SQL Proxy (localhost)
        - name: DB_HOST
          value: "127.0.0.1"
        - name: DB_PORT
          value: "5432"
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: database
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        # Connection string format (for some apps)
        - name: DATABASE_URL
          value: "postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)"
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi

      # Cloud SQL Proxy sidecar
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
        args:
        - "--structured-logs"
        - "--port=5432"
        - "baldmaninc:us-central1:clusterkit-db"
        securityContext:
          runAsNonRoot: true
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
```

**Deploy:**

```bash
# Create secret with actual password
kubectl create secret generic db-credentials \
  --from-literal=username=postgres \
  --from-literal=password=YOUR_SECURE_PASSWORD \
  --from-literal=database=myapp_production

# Deploy app
kubectl apply -f app-with-cloudsql.yaml

# Test connection
kubectl exec -it deployment/my-app -- env | grep DB_
```

### Cost Comparison

| Instance Type | vCPUs | RAM | Storage | Monthly Cost | Use Case |
|---------------|-------|-----|---------|--------------|----------|
| db-f1-micro | Shared | 0.6GB | 10GB | ~$7 | Dev/Test |
| db-g1-small | Shared | 1.7GB | 20GB | ~$25 | Small production |
| db-n1-standard-1 | 1 | 3.75GB | 50GB | ~$50 | Medium production |
| db-n1-standard-2 | 2 | 7.5GB | 100GB | ~$100 | Large production |

**Add regional HA:** Multiply cost by ~2x for `--availability-type=regional`

### Alternative: Redis for Caching (In-Cluster)

**For ephemeral data** (sessions, cache), Redis in-cluster is fine:

```yaml
# redis-cache.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: cache
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 50m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 512Mi
        command:
        - redis-server
        - --appendonly
        - "no"
        - --maxmemory
        - "256mb"
        - --maxmemory-policy
        - "allkeys-lru"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: cache
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

**Connect from app:**

```yaml
env:
- name: REDIS_HOST
  value: "redis.cache.svc.cluster.local"
- name: REDIS_PORT
  value: "6379"
```

### Database Migrations

**Using Kubernetes Jobs:**

```yaml
# migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-v1-2-3
spec:
  template:
    spec:
      serviceAccountName: cloudsql-proxy
      restartPolicy: Never

      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule

      containers:
      # Migration container
      - name: migrate
        image: gcr.io/baldmaninc/my-app:latest
        command: ["npm", "run", "migrate"]
        env:
        - name: DB_HOST
          value: "127.0.0.1"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password

      # Cloud SQL Proxy
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
        args:
        - "--structured-logs"
        - "--port=5432"
        - "baldmaninc:us-central1:clusterkit-db"
```

**Run migration:**

```bash
# Run migration job
kubectl apply -f migration-job.yaml

# Watch progress
kubectl logs job/db-migration-v1-2-3 -f

# Clean up after success
kubectl delete job db-migration-v1-2-3
```

### Backup and Recovery

**Cloud SQL automatic backups:**

```bash
# Enable backups (already enabled if created with --backup)
gcloud sql instances patch clusterkit-db --backup-start-time=03:00

# List backups
gcloud sql backups list --instance=clusterkit-db

# Restore from backup
gcloud sql backups restore BACKUP_ID \
  --backup-instance=clusterkit-db \
  --backup-id=BACKUP_ID

# Create on-demand backup
gcloud sql backups create --instance=clusterkit-db
```

**Export database:**

```bash
# Export to Cloud Storage
gcloud sql export sql clusterkit-db gs://baldmaninc-backups/myapp-$(date +%Y%m%d).sql \
  --database=myapp_production

# Import from Cloud Storage
gcloud sql import sql clusterkit-db gs://baldmaninc-backups/myapp-20250104.sql \
  --database=myapp_production
```

### Database Best Practices

1. **Always use Cloud SQL Proxy** - Never expose database directly
2. **Use secrets for credentials** - Never hardcode passwords
3. **Enable automated backups** - Minimum 7-day retention
4. **Run migrations as Jobs** - Not in app startup
5. **Use connection pooling** - PgBouncer for high-traffic apps
6. **Monitor query performance** - Enable Cloud SQL Insights
7. **Test disaster recovery** - Practice restoring from backups

### When NOT to Use Cloud SQL

**Use in-cluster operators if:**
- You have dedicated ops team (24/7)
- Need extreme customization
- Cost is absolutely critical
- Running 100+ database instances

**For ClusterKit's use case:** Cloud SQL is strongly recommended.

---

## Exposing Your Application

### Option 1: LoadBalancer Service (Simple)

**Pros:**
- Simple, direct access
- Gets a dedicated external IP
- Good for non-HTTP services

**Cons:**
- Each service gets its own IP (costs ~$3/month per IP)
- No automatic SSL
- No path-based routing

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    # ExternalDNS will create DNS record
    external-dns.alpha.kubernetes.io/hostname: my-app.yourdomain.com
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

### Option 2: Ingress + Managed Certificates (Recommended)

**Pros:**
- Automatic SSL certificates
- Share single load balancer across apps
- Path-based routing
- Lower cost (one IP for all apps)

**Cons:**
- HTTP/HTTPS only
- Takes 10-15 minutes to provision

**See Pattern 2 above for full example.**

---

## SSL/TLS Configuration

### Automatic SSL with GKE Managed Certificates

**ClusterKit uses GKE Managed Certificates** (automatic Let's Encrypt):

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: my-cert
spec:
  domains:
  - my-app.yourdomain.com
  - www.my-app.yourdomain.com  # Multiple domains supported
```

Reference in Ingress:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    networking.gke.io/managed-certificates: "my-cert"
spec:
  # ... ingress rules
```

**Check certificate status:**

```bash
kubectl describe managedcertificate my-cert
```

**Certificate provisioning status:**

- `Provisioning` - Certificate being created (10-15 mins)
- `FailedNotVisible` - DNS not pointing to ingress yet
- `Active` - Certificate ready and serving

**Common issues:**

- **DNS not propagating:** Wait 5-10 minutes for Cloudflare DNS
- **Certificate stuck:** Verify Ingress has an IP and DNS points to it

---

## Cost Optimization

### Use Spot Pods (60-91% Cheaper)

**Always add these to your deployments:**

```yaml
spec:
  template:
    spec:
      # Schedule on Spot nodes
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      # Tolerate Spot node evictions
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule
```

**When to avoid Spot:**
- Critical services that can't tolerate interruptions
- Stateful workloads without proper backup

**For most apps:** Spot pods are perfect! They're preemptible but GKE gives 30 seconds warning and auto-reschedules.

### Right-Size Resources

**Use resource requests/limits:**

```yaml
resources:
  requests:
    cpu: 100m      # Minimum needed
    memory: 128Mi
  limits:
    cpu: 500m      # Maximum allowed
    memory: 512Mi
```

**Common sizes:**

| App Type | CPU Request | Memory Request |
|----------|-------------|----------------|
| Static site | 50m | 64Mi |
| Small API | 100m | 128Mi |
| Medium API | 250m | 512Mi |
| Large API | 500m | 1Gi |
| Background job | 100m | 256Mi |

**Why this matters:**
- Autopilot charges based on resource **requests**
- Over-requesting = wasted money
- Under-requesting = throttling/OOM kills

**Find the right size:**

```bash
# Check actual usage
kubectl top pod <pod-name>

# Compare to requests
kubectl describe pod <pod-name> | grep -A 5 "Requests:"
```

### Horizontal Pod Autoscaling

**Auto-scale based on load:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Benefits:**
- Pay only for what you need
- Handles traffic spikes automatically
- Reduces costs during low traffic

---

## Best Practices

### 1. Always Use Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 2. Use Namespaces for Organization

```bash
# Create namespace for your team/project
kubectl create namespace my-team

# Deploy to namespace
kubectl apply -f deployment.yaml -n my-team

# Set default namespace
kubectl config set-context --current --namespace=my-team
```

### 3. Use ConfigMaps for Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-app-config
data:
  DATABASE_URL: "postgres://..."
  API_KEY: "..."
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        envFrom:
        - configMapRef:
            name: my-app-config
```

### 4. Use Secrets for Sensitive Data

```bash
# Create secret
kubectl create secret generic my-app-secrets \
  --from-literal=db-password='supersecret' \
  --from-literal=api-key='abc123'
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: my-app:latest
        env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: my-app-secrets
              key: db-password
```

### 5. Use Labels for Organization

```yaml
metadata:
  labels:
    app: my-app
    team: platform
    environment: production
    version: v1.2.3
```

**Query by labels:**

```bash
kubectl get pods -l app=my-app
kubectl get pods -l team=platform
kubectl get pods -l environment=production
```

---

## Troubleshooting

### Pod Won't Start

**Check pod status:**

```bash
kubectl get pods
kubectl describe pod <pod-name>
```

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `ImagePullBackOff` | Image doesn't exist | Check image name/tag |
| `CrashLoopBackOff` | App crashes on startup | Check logs: `kubectl logs <pod>` |
| `Pending` | No nodes available | Check resource requests are reasonable |
| `OOMKilled` | Out of memory | Increase memory limit |

### Can't Access Application

**Check service:**

```bash
kubectl get service my-app
kubectl describe service my-app
```

**Check endpoints:**

```bash
kubectl get endpoints my-app
```

If endpoints are empty, check pod labels match service selector.

**Check ingress:**

```bash
kubectl get ingress
kubectl describe ingress my-app
```

**Check DNS:**

```bash
dig my-app.yourdomain.com
```

Should point to Ingress IP.

### SSL Certificate Not Working

**Check certificate status:**

```bash
kubectl describe managedcertificate my-cert
```

**Common status meanings:**

- `Provisioning` → Wait 10-15 minutes
- `FailedNotVisible` → DNS doesn't point to ingress IP yet
- `Active` → Working!

**Debug steps:**

```bash
# 1. Verify Ingress has IP
kubectl get ingress my-app

# 2. Verify DNS points to that IP
dig my-app.yourdomain.com

# 3. Wait for DNS propagation (5-10 mins)

# 4. Check certificate again
kubectl describe managedcertificate my-cert
```

### High Costs

**Check resource usage:**

```bash
# See what's using resources
kubectl top nodes
kubectl top pods --all-namespaces

# Check pod requests
kubectl describe pods -A | grep -A 2 "Requests:"
```

**Optimization checklist:**

- [ ] Using Spot pods? (`nodeSelector: cloud.google.com/gke-spot: "true"`)
- [ ] Resource requests match actual usage?
- [ ] Using HPA to scale down during low traffic?
- [ ] Idle pods/deployments deleted?
- [ ] Using ClusterIP + Ingress instead of multiple LoadBalancers?

### Need Help?

**Useful commands:**

```bash
# View logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # Previous crash

# Get shell in pod
kubectl exec -it <pod-name> -- /bin/sh

# Port forward to local
kubectl port-forward <pod-name> 8080:8080

# View events
kubectl get events --sort-by='.lastTimestamp'

# Full cluster status
kubectl get all --all-namespaces
```

---

## Example: Complete Production Deployment

**Directory structure:**

```
my-app/
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── certificate.yaml
│   └── hpa.yaml
└── README.md
```

**deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      # Cost optimization: Use Spot pods
      nodeSelector:
        cloud.google.com/gke-spot: "true"
      tolerations:
      - key: cloud.google.com/gke-spot
        operator: Equal
        value: "true"
        effect: NoSchedule
      containers:
      - name: app
        image: gcr.io/baldmaninc/my-app:v1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: my-app-config
              key: db-host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: my-app-secrets
              key: db-password
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  annotations:
    external-dns.alpha.kubernetes.io/hostname: my-app.yourdomain.com
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
```

**ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app
  annotations:
    kubernetes.io/ingress.class: "gce"
    networking.gke.io/managed-certificates: "my-app-cert"
    networking.gke.io/v1beta1.FrontendConfig: "ssl-redirect"
spec:
  rules:
  - host: my-app.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
---
apiVersion: networking.gke.io/v1beta1
kind: FrontendConfig
metadata:
  name: ssl-redirect
spec:
  redirectToHttps:
    enabled: true
```

**certificate.yaml:**

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: my-app-cert
spec:
  domains:
  - my-app.yourdomain.com
```

**hpa.yaml:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Deploy everything:**

```bash
# Create config
kubectl create configmap my-app-config \
  --from-literal=db-host=postgres.example.com

# Create secrets
kubectl create secret generic my-app-secrets \
  --from-literal=db-password='supersecret'

# Deploy app
kubectl apply -f k8s/

# Watch deployment
kubectl rollout status deployment/my-app

# Get URL
kubectl get ingress my-app
```

---

## Summary

**For most applications:**

1. ✅ Use Spot pods (`nodeSelector: cloud.google.com/gke-spot: "true"`)
2. ✅ Right-size resources (start small, monitor, adjust)
3. ✅ Use Ingress + Managed Certificates for HTTPS
4. ✅ Add health checks
5. ✅ Use HPA for auto-scaling

**Your app will be:**
- ✅ Cost-optimized (~60-91% cheaper)
- ✅ Secure (automatic SSL)
- ✅ Scalable (HPA)
- ✅ Reliable (health checks + multiple replicas)

**Questions?** Check the main [README.md](./README.md) or contact the platform team.
