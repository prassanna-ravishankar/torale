#!/bin/bash
set -e

echo "==============================================="
echo "Torale - Cloud SQL Setup for GKE"
echo "==============================================="
echo ""

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-baldmaninc}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
INSTANCE_NAME="torale-db"
DATABASE_NAME="torale"
DB_USER="torale"
SA_NAME="cloudsql-proxy"
K8S_NAMESPACE="torale"
K8S_SA_NAME="torale-sa"

echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Instance Name: $INSTANCE_NAME"
echo ""

# Check if instance already exists
if gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "✓ Cloud SQL instance '$INSTANCE_NAME' already exists"
    CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" --format='value(connectionName)')
else
    echo "Creating Cloud SQL PostgreSQL instance (this takes ~5-10 minutes)..."
    gcloud sql instances create "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --database-version=POSTGRES_16 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --backup \
        --availability-type=zonal \
        --storage-type=SSD \
        --storage-size=10GB \
        --no-assign-ip

    CONNECTION_NAME=$(gcloud sql instances describe "$INSTANCE_NAME" --project="$PROJECT_ID" --format='value(connectionName)')
    echo "✓ Cloud SQL instance created: $CONNECTION_NAME"
fi

echo ""
echo "Connection name: $CONNECTION_NAME"
echo ""

# Set database password
echo "Setting database password..."
echo "Enter a secure password for the '$DB_USER' user:"
read -s DB_PASSWORD

if [ -z "$DB_PASSWORD" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

gcloud sql users set-password "$DB_USER" \
    --instance="$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --password="$DB_PASSWORD" 2>/dev/null || \
gcloud sql users create "$DB_USER" \
    --instance="$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --password="$DB_PASSWORD"

echo "✓ Database user configured"
echo ""

# Create database
echo "Creating database '$DATABASE_NAME'..."
gcloud sql databases create "$DATABASE_NAME" \
    --instance="$INSTANCE_NAME" \
    --project="$PROJECT_ID" 2>/dev/null || echo "✓ Database already exists"

echo "✓ Database '$DATABASE_NAME' ready"
echo ""

# Setup IAM for Cloud SQL Proxy
echo "Setting up IAM service account for Cloud SQL Proxy..."

# Create GCP service account
gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Cloud SQL Proxy for Torale" \
    --project="$PROJECT_ID" 2>/dev/null || echo "✓ Service account already exists"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" \
    --condition=None \
    > /dev/null

echo "✓ IAM service account configured"
echo ""

# Setup Workload Identity
echo "Setting up Workload Identity..."

# Enable Workload Identity binding
gcloud iam service-accounts add-iam-policy-binding \
    "${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="serviceAccount:${PROJECT_ID}.svc.id.goog[${K8S_NAMESPACE}/${K8S_SA_NAME}]" \
    --project="$PROJECT_ID" \
    > /dev/null

echo "✓ Workload Identity configured"
echo ""

# Save connection info to file
cat > .cloud-sql-info << EOF
# Cloud SQL Connection Information
# Generated: $(date)

CONNECTION_NAME=$CONNECTION_NAME
DATABASE_NAME=$DATABASE_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=5432
EOF

echo "==============================================="
echo "✓ Cloud SQL Setup Complete!"
echo "==============================================="
echo ""
echo "Connection details saved to: .cloud-sql-info"
echo ""
echo "Next steps:"
echo "  1. Run: ./scripts/k8s-create-secrets.sh"
echo "  2. Update helm/torale/values-production.yaml with:"
echo "     database.connectionName: $CONNECTION_NAME"
echo "  3. Deploy: just k8s-deploy-all"
echo ""
