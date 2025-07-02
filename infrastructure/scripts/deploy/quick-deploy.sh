#!/bin/bash

# Quick deployment script for fast iteration using modular infrastructure
# This deploys services using the new module structure

set -e

echo "🚀 Quick Deploy - Fast iteration mode (Modular Infrastructure)..."

# Navigate to the dev environment directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_DIR="$SCRIPT_DIR/../../terraform/environments/dev"
PROJECT_ROOT="$SCRIPT_DIR/../../../"

cd "$DEV_DIR"

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars file not found in $DEV_DIR"
    echo "💡 Create it by copying from shared/terraform.tfvars.example and filling in your values"
    exit 1
fi

# Extract project info
PROJECT_ID=$(grep '^project_id' terraform.tfvars | cut -d'"' -f2)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: project_id not found in terraform.tfvars"
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"

# Check if basic infrastructure exists
echo "🔍 Checking if basic infrastructure exists..."
terraform init > /dev/null

if ! terraform show | grep -q "module.artifact_registry"; then
    echo "❌ Error: Artifact Registry module not found. Run terraform apply first to create basic infrastructure."
    exit 1
fi

# Get the artifact registry URL
REGISTRY_URL=$(terraform output -raw artifact_registry_url)
echo "📦 Registry URL: $REGISTRY_URL"

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Extract Supabase variables for frontend build
SUPABASE_URL=$(grep '^supabase_url' terraform.tfvars | cut -d'"' -f2)
SUPABASE_ANON_KEY=$(grep '^supabase_anon_key' terraform.tfvars | cut -d'"' -f2)

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: Supabase URL or anon key not found in terraform.tfvars"
    exit 1
fi

# Navigate to project root
cd "$PROJECT_ROOT"

echo "🐳 Building and pushing Docker images..."

# Build and push frontend
echo "🌐 Building frontend..."
docker build --platform=linux/amd64 -t $REGISTRY_URL/frontend:latest \
  --build-arg NEXT_PUBLIC_SUPABASE_URL="$SUPABASE_URL" \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  -f frontend/Dockerfile.production ./frontend
docker push $REGISTRY_URL/frontend:latest

# Build and push backend
echo "⚙️  Building main backend..."
docker build --platform=linux/amd64 -t $REGISTRY_URL/backend:latest -f backend/Dockerfile ./backend
docker push $REGISTRY_URL/backend:latest

# Build and push microservices
echo "🔍 Building discovery service..."
docker build --platform=linux/amd64 -t $REGISTRY_URL/discovery-service:latest -f discovery-service/Dockerfile ./discovery-service
docker push $REGISTRY_URL/discovery-service:latest

echo "👁️  Building monitoring service..."
docker build --platform=linux/amd64 -t $REGISTRY_URL/content-monitoring-service:latest -f content-monitoring-service/Dockerfile ./content-monitoring-service
docker push $REGISTRY_URL/content-monitoring-service:latest

echo "📧 Building notification service..."
docker build --platform=linux/amd64 -t $REGISTRY_URL/notification-service:latest -f notification-service/Dockerfile ./notification-service
docker push $REGISTRY_URL/notification-service:latest

# Navigate back to dev environment directory
cd "$DEV_DIR"

# Deploy Cloud Run services using the modular structure
echo "☁️  Deploying Cloud Run services..."
terraform apply \
  -target=module.cloud_run \
  -auto-approve

echo "✅ Quick deploy complete!"
echo ""
echo "🔗 Service URLs:"
terraform output

echo ""
echo "💡 For even faster iteration:"
echo "   ./quick-deploy.sh    # Rebuild and redeploy all services"
echo "   terraform output     # View service URLs" 