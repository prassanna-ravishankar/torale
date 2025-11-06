#!/bin/bash
# Setup Workload Identity Federation for GitHub Actions
# Enables keyless authentication to GCP without service account keys
#
# Run once: ./scripts/setup-github-wif.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    log_error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

log_info "Setting up Workload Identity Federation for GitHub Actions"
echo ""
log_info "Project ID: $PROJECT_ID"
log_info "Project Number: $PROJECT_NUMBER"
echo ""

# Get GitHub repository info
read -p "Enter GitHub repository owner (e.g., your-username): " GITHUB_OWNER
read -p "Enter GitHub repository name (e.g., torale): " GITHUB_REPO

REPO_FULL="${GITHUB_OWNER}/${GITHUB_REPO}"

echo ""
log_info "Repository: $REPO_FULL"
echo ""

# ============================================================================
# Step 1: Enable required APIs
# ============================================================================

log_info "Step 1: Enabling required APIs..."

APIS=(
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iamcredentials.googleapis.com"
    "sts.googleapis.com"
)

for api in "${APIS[@]}"; do
    log_info "  Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID"
done

log_success "APIs enabled"
echo ""

# ============================================================================
# Step 2: Create Workload Identity Pool
# ============================================================================

log_info "Step 2: Creating Workload Identity Pool..."

POOL_NAME="github-actions-pool"
POOL_DISPLAY_NAME="GitHub Actions Pool"

# Check if pool exists
if gcloud iam workload-identity-pools describe "$POOL_NAME" \
    --location=global \
    --project="$PROJECT_ID" &>/dev/null; then
    log_warning "Pool '$POOL_NAME' already exists, skipping..."
else
    log_info "  Creating pool '$POOL_NAME'..."
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --location=global \
        --display-name="$POOL_DISPLAY_NAME" \
        --project="$PROJECT_ID"

    log_success "Pool created"
fi

echo ""

# ============================================================================
# Step 3: Create Workload Identity Provider
# ============================================================================

log_info "Step 3: Creating Workload Identity Provider..."

PROVIDER_NAME="github-provider"
PROVIDER_DISPLAY_NAME="GitHub Provider"

# Check if provider exists
if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --workload-identity-pool="$POOL_NAME" \
    --location=global \
    --project="$PROJECT_ID" &>/dev/null; then
    log_warning "Provider '$PROVIDER_NAME' already exists, skipping..."
else
    log_info "  Creating provider '$PROVIDER_NAME'..."
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --workload-identity-pool="$POOL_NAME" \
        --location=global \
        --issuer-uri="https://token.actions.githubusercontent.com" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
        --attribute-condition="assertion.repository_owner == '$GITHUB_OWNER'" \
        --project="$PROJECT_ID"

    log_success "Provider created"
fi

echo ""

# ============================================================================
# Step 4: Create Service Account
# ============================================================================

log_info "Step 4: Creating Service Account..."

SA_NAME="github-actions"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account exists
if gcloud iam service-accounts describe "$SA_EMAIL" \
    --project="$PROJECT_ID" &>/dev/null; then
    log_warning "Service account '$SA_EMAIL' already exists, skipping..."
else
    log_info "  Creating service account '$SA_NAME'..."
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions" \
        --project="$PROJECT_ID"

    log_success "Service account created"
fi

echo ""

# ============================================================================
# Step 5: Grant IAM Roles
# ============================================================================

log_info "Step 5: Granting IAM roles to service account..."

ROLES=(
    "roles/container.developer"
    "roles/storage.objectAdmin"
    "roles/iam.serviceAccountUser"
)

for role in "${ROLES[@]}"; do
    log_info "  Granting $role..."
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --condition=None \
        --quiet
done

log_success "IAM roles granted"
echo ""

# ============================================================================
# Step 6: Allow Workload Identity
# ============================================================================

log_info "Step 6: Configuring Workload Identity binding..."

# Allow the repository to impersonate the service account
log_info "  Allowing repository to impersonate service account..."

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO_FULL}" \
    --project="$PROJECT_ID"

log_success "Workload Identity binding configured"
echo ""

# ============================================================================
# Step 7: Generate GitHub Secrets
# ============================================================================

log_info "Step 7: Generating GitHub secrets..."
echo ""

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"

log_success "=========================================="
log_success "Setup Complete!"
log_success "=========================================="
echo ""
log_info "Add these secrets to your GitHub repository:"
echo ""
echo "Repository → Settings → Secrets and variables → Actions → New repository secret"
echo ""
log_success "GCP_PROJECT_ID"
echo "$PROJECT_ID"
echo ""
log_success "GCP_SERVICE_ACCOUNT"
echo "$SA_EMAIL"
echo ""
log_success "GCP_WORKLOAD_IDENTITY_PROVIDER"
echo "$WIF_PROVIDER"
echo ""
log_info "Quick add via GitHub CLI:"
echo ""
echo "  gh secret set GCP_PROJECT_ID --body '$PROJECT_ID'"
echo "  gh secret set GCP_SERVICE_ACCOUNT --body '$SA_EMAIL'"
echo "  gh secret set GCP_WORKLOAD_IDENTITY_PROVIDER --body '$WIF_PROVIDER'"
echo ""
log_info "Documentation:"
echo "  https://cloud.google.com/blog/products/identity-security/enabling-keyless-authentication-from-github-actions"
echo ""
