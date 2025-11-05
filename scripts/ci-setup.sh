#!/bin/bash
# CI/CD Setup Script - Run once to configure Cloud Build for Torale
# This script sets up Cloud Build triggers, service accounts, and permissions

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    log_error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

log_info "Setting up CI/CD for project: $PROJECT_ID"
echo ""

# ============================================================================
# STEP 1: Enable required APIs
# ============================================================================

log_info "Step 1: Enabling required GCP APIs..."

APIS=(
    "cloudbuild.googleapis.com"
    "container.googleapis.com"
    "compute.googleapis.com"
    "sqladmin.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "  Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID"
done

log_success "APIs enabled"
echo ""

# ============================================================================
# STEP 2: Grant Cloud Build permissions
# ============================================================================

log_info "Step 2: Configuring Cloud Build service account permissions..."

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

log_info "  Cloud Build SA: $CLOUDBUILD_SA"

# Grant necessary roles
ROLES=(
    "roles/container.developer"     # Deploy to GKE
    "roles/iam.serviceAccountUser"  # Use service accounts
    "roles/storage.admin"           # Access GCS for build artifacts
)

for role in "${ROLES[@]}"; do
    log_info "  Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$CLOUDBUILD_SA" \
        --role="$role" \
        --condition=None \
        --quiet
done

log_success "Permissions configured"
echo ""

# ============================================================================
# STEP 3: Build custom helm-deploy image
# ============================================================================

log_info "Step 3: Building custom helm-deploy image..."

if [ -f "cloudbuild/build-helm-image.yaml" ]; then
    log_info "  Submitting build..."
    gcloud builds submit \
        --config=cloudbuild/build-helm-image.yaml \
        --project="$PROJECT_ID" \
        cloudbuild/

    log_success "Custom helm-deploy image built: gcr.io/$PROJECT_ID/helm-deploy:latest"
else
    log_error "cloudbuild/build-helm-image.yaml not found"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: Create Cloud Build triggers
# ============================================================================

log_info "Step 4: Creating Cloud Build triggers..."

# Check if triggers already exist
PROD_TRIGGER_EXISTS=$(gcloud builds triggers list \
    --project="$PROJECT_ID" \
    --filter="name:torale-production-deploy" \
    --format="value(name)" | wc -l)

BRANCH_TRIGGER_EXISTS=$(gcloud builds triggers list \
    --project="$PROJECT_ID" \
    --filter="name:torale-branch-deploy" \
    --format="value(name)" | wc -l)

# Production trigger (main branch)
if [ "$PROD_TRIGGER_EXISTS" -gt 0 ]; then
    log_warning "Production trigger already exists, skipping..."
else
    log_info "  Creating production deployment trigger..."

    # Note: Update the github owner/name and branch as needed
    read -p "Enter GitHub repository owner/org (e.g., your-username): " GITHUB_OWNER
    read -p "Enter GitHub repository name (e.g., torale): " GITHUB_REPO
    read -p "Enter main branch name (default: main): " MAIN_BRANCH
    MAIN_BRANCH=${MAIN_BRANCH:-main}

    gcloud builds triggers create github \
        --name="torale-production-deploy" \
        --description="Deploy Torale to production on push to $MAIN_BRANCH" \
        --repo-owner="$GITHUB_OWNER" \
        --repo-name="$GITHUB_REPO" \
        --branch-pattern="^$MAIN_BRANCH\$" \
        --build-config="cloudbuild.yaml" \
        --project="$PROJECT_ID"

    log_success "Production trigger created"
fi

# Branch deployment trigger (all branches except main)
if [ "$BRANCH_TRIGGER_EXISTS" -gt 0 ]; then
    log_warning "Branch deployment trigger already exists, skipping..."
else
    log_info "  Creating branch deployment trigger..."

    gcloud builds triggers create github \
        --name="torale-branch-deploy" \
        --description="Deploy Torale branches to isolated environments" \
        --repo-owner="$GITHUB_OWNER" \
        --repo-name="$GITHUB_REPO" \
        --branch-pattern="^(?!$MAIN_BRANCH\$).*" \
        --build-config="cloudbuild-branch.yaml" \
        --project="$PROJECT_ID"

    log_success "Branch deployment trigger created"
fi

echo ""

# ============================================================================
# STEP 5: Create GCS bucket for build artifacts
# ============================================================================

log_info "Step 5: Creating GCS bucket for build artifacts..."

BUCKET_NAME="${PROJECT_ID}-build-artifacts"

if gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
    log_warning "Bucket gs://$BUCKET_NAME already exists, skipping..."
else
    log_info "  Creating bucket: gs://$BUCKET_NAME"
    gsutil mb -p "$PROJECT_ID" -l us-central1 "gs://$BUCKET_NAME"

    # Set lifecycle policy to auto-delete old artifacts after 30 days
    cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF
    gsutil lifecycle set /tmp/lifecycle.json "gs://$BUCKET_NAME"
    rm /tmp/lifecycle.json

    log_success "Bucket created with 30-day retention policy"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
log_success "=========================================="
log_success "CI/CD Setup Complete!"
log_success "=========================================="
echo ""
log_info "Next steps:"
echo "  1. Connect your GitHub repository to Cloud Build"
echo "     → https://console.cloud.google.com/cloud-build/triggers"
echo ""
echo "  2. Push to main branch to trigger production deployment"
echo "     → Deploys to: torale namespace"
echo ""
echo "  3. Push to any other branch for isolated testing"
echo "     → Deploys to: torale-{branch-name} namespace"
echo ""
echo "  4. View builds:"
echo "     → https://console.cloud.google.com/cloud-build/builds"
echo ""
echo "  5. Manual trigger:"
echo "     → gcloud builds submit --config=cloudbuild.yaml"
echo ""
log_info "For more info, see docs/CI-CD.md"
echo ""
