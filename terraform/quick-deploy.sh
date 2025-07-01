#!/bin/bash

# Quick deployment script for fast iteration
# This skips VPC and other slow infrastructure setup

set -e

echo "🚀 Quick Deploy - Fast iteration mode..."

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars file not found"
    echo "💡 Create it by copying terraform.tfvars.example and filling in your values"
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

if ! terraform show | grep -q "google_artifact_registry_repository.docker_repo"; then
    echo "❌ Error: Artifact Registry not found. Run ./bootstrap.sh first to create basic infrastructure."
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
cd ..

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

# Navigate back to terraform directory
cd terraform

# Deploy only Cloud Run services (skip VPC and other infrastructure)
echo "☁️  Deploying Cloud Run services..."
terraform apply \
  -target=google_service_account.frontend \
  -target=google_service_account.main_backend \
  -target=google_service_account.discovery \
  -target=google_service_account.monitoring \
  -target=google_service_account.notification \
  -target=google_cloud_run_v2_service.frontend \
  -target=google_cloud_run_v2_service.main_backend \
  -target=google_cloud_run_v2_service.discovery \
  -target=google_cloud_run_v2_service.monitoring \
  -target=google_cloud_run_v2_service.notification \
  -target=google_cloud_run_service_iam_member.frontend_public \
  -target=google_cloud_run_service_iam_member.frontend_invoke_main_backend \
  -target=google_cloud_run_service_iam_member.backend_invoke_discovery \
  -target=google_cloud_run_service_iam_member.backend_invoke_monitoring \
  -target=google_cloud_run_service_iam_member.backend_invoke_notification \
  -auto-approve

echo "✅ Quick deploy complete!"
echo ""
echo "🔗 Service URLs:"
terraform output

echo ""
echo "💡 For even faster iteration:"
echo "   ./quick-deploy.sh    # Rebuild and redeploy all services"
echo "   terraform output     # View service URLs" 