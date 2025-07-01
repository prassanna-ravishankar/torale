#!/bin/bash

# Bootstrap script for Torale infrastructure deployment
# This script handles the chicken-and-egg problem of images vs Cloud Run services

set -e

echo "🚀 Starting Torale infrastructure bootstrap..."

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    echo "❌ Error: terraform.tfvars file not found"
    echo "💡 Create it by copying terraform.tfvars.example and filling in your values"
    exit 1
fi

# Extract project_id from terraform.tfvars for display purposes
PROJECT_ID=$(grep '^project_id' terraform.tfvars | cut -d'"' -f2)
GITHUB_OWNER=$(grep '^github_owner' terraform.tfvars | cut -d'"' -f2 2>/dev/null || echo "not set")
GITHUB_REPO=$(grep '^github_repo' terraform.tfvars | cut -d'"' -f2 2>/dev/null || echo "not set")

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: project_id not found in terraform.tfvars"
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"
echo "📋 GitHub: $GITHUB_OWNER/$GITHUB_REPO"

# Step 1: Deploy basic infrastructure (APIs, Artifact Registry, etc.)
echo "🏗️  Step 1: Deploying basic infrastructure..."
terraform init
terraform plan -target=google_project_service.required_apis \
               -target=google_artifact_registry_repository.docker_repo \
               -target=time_sleep.wait_for_cloudbuild_sa \
               -target=google_project_iam_member.cloudbuild_run_admin \
               -target=google_project_iam_member.cloudbuild_sa_user \
               -target=google_artifact_registry_repository_iam_member.cloudbuild_push \
               -target=google_compute_network.vpc \
               -target=google_compute_subnetwork.vpc_connector_subnet \
               -target=google_vpc_access_connector.connector

read -p "🤔 Do you want to apply the basic infrastructure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -target=google_project_service.required_apis \
                   -target=google_artifact_registry_repository.docker_repo \
                   -target=time_sleep.wait_for_cloudbuild_sa \
                   -target=google_project_iam_member.cloudbuild_run_admin \
                   -target=google_project_iam_member.cloudbuild_sa_user \
                   -target=google_artifact_registry_repository_iam_member.cloudbuild_push \
                   -target=google_compute_network.vpc \
                   -target=google_compute_subnetwork.vpc_connector_subnet \
                   -target=google_vpc_access_connector.connector \
                   -auto-approve
else
    echo "❌ Aborted by user"
    exit 1
fi

# Step 2: Skip Cloud Build trigger for now (requires manual GitHub App setup)
echo "⏭️  Step 2: Skipping Cloud Build trigger (requires manual GitHub App connection)"
echo "ℹ️  We'll set up CI/CD manually after the initial deployment"

# Step 3: Build and push initial images
echo "🐳 Step 3: Building and pushing initial Docker images..."
echo "ℹ️  This will trigger the Cloud Build pipeline to create the necessary images."

# Get the artifact registry URL
REGISTRY_URL=$(terraform output -raw artifact_registry_url)
echo "📦 Registry URL: $REGISTRY_URL"

# Configure Docker authentication for Artifact Registry
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Build images locally and push (fallback if Cloud Build trigger doesn't work immediately)
echo "🔨 Building images locally as fallback..."

# Navigate to project root
cd ..

# Extract Supabase variables from terraform.tfvars for frontend build
SUPABASE_URL=$(grep '^supabase_url' terraform/terraform.tfvars | cut -d'"' -f2)
SUPABASE_ANON_KEY=$(grep '^supabase_anon_key' terraform/terraform.tfvars | cut -d'"' -f2)

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: Supabase URL or anon key not found in terraform.tfvars"
    echo "💡 Make sure supabase_url and supabase_anon_key are set in terraform/terraform.tfvars"
    exit 1
fi

# Build and push frontend
echo "🌐 Building frontend..."
docker build -t $REGISTRY_URL/frontend:latest \
  --build-arg NEXT_PUBLIC_SUPABASE_URL="$SUPABASE_URL" \
  --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
  -f frontend/Dockerfile.production ./frontend
docker push $REGISTRY_URL/frontend:latest

# Build and push backend
echo "⚙️  Building main backend..."
docker build -t $REGISTRY_URL/backend:latest -f backend/Dockerfile ./backend
docker push $REGISTRY_URL/backend:latest

# Build and push microservices
echo "🔍 Building discovery service..."
docker build -t $REGISTRY_URL/discovery-service:latest -f discovery-service/Dockerfile ./discovery-service
docker push $REGISTRY_URL/discovery-service:latest

echo "👁️  Building monitoring service..."
docker build -t $REGISTRY_URL/content-monitoring-service:latest -f content-monitoring-service/Dockerfile ./content-monitoring-service
docker push $REGISTRY_URL/content-monitoring-service:latest

echo "📧 Building notification service..."
docker build -t $REGISTRY_URL/notification-service:latest -f notification-service/Dockerfile ./notification-service
docker push $REGISTRY_URL/notification-service:latest

# Navigate back to terraform directory
cd terraform

# Step 4: Deploy Cloud Run services
echo "☁️  Step 4: Deploying Cloud Run services..."
terraform plan

read -p "🤔 Do you want to deploy the Cloud Run services? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -auto-approve
else
    echo "❌ Aborted by user"
    exit 1
fi

echo "✅ Bootstrap complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set up GitHub App connection for CI/CD:"
echo "   - Go to Cloud Build > Triggers in GCP Console"
echo "   - Click 'Connect Repository' and follow GitHub App setup"
echo "   - After setup, set create_github_trigger = true in terraform.tfvars"
echo "   - Run: terraform apply"
echo ""
echo "2. Configure your domain DNS if using custom domain"
echo "3. Test your services using the URLs below"
echo ""
echo "🔗 Useful commands:"
echo "  terraform output                    # View all outputs"
echo "  gcloud run services list --region=\$(terraform output -raw region || echo 'us-central1')  # List Cloud Run services"
echo ""
echo "⚡ Fast iteration (no VPC rebuild - saves ~10 mins):"
echo "  ./quick-deploy.sh                   # Rebuild and redeploy all services (~3-5 mins)"
echo "  ./deploy-service.sh frontend        # Deploy just the frontend (~1-2 mins)"
echo "  ./deploy-service.sh backend         # Deploy just the backend (~1-2 mins)" 