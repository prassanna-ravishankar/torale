#!/bin/bash

# Deploy a single service for ultra-fast iteration
# Usage: ./deploy-service.sh [frontend|backend|discovery|monitoring|notification]

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 [frontend|backend|discovery|monitoring|notification]"
    echo ""
    echo "Examples:"
    echo "  $0 frontend    # Build and deploy just the frontend"
    echo "  $0 backend     # Build and deploy just the main backend"
    echo "  $0 discovery   # Build and deploy just the discovery service"
    exit 1
fi

SERVICE=$1

# Validate service name
case $SERVICE in
    frontend|backend|discovery|monitoring|notification)
        ;;
    *)
        echo "❌ Invalid service: $SERVICE"
        echo "Valid services: frontend, backend, discovery, monitoring, notification"
        exit 1
        ;;
esac

echo "🚀 Deploying single service: $SERVICE"

# Get registry URL
REGISTRY_URL=$(terraform output -raw artifact_registry_url)

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

cd ..

case $SERVICE in
    frontend)
        SUPABASE_URL=$(grep '^supabase_url' terraform/terraform.tfvars | cut -d'"' -f2)
        SUPABASE_ANON_KEY=$(grep '^supabase_anon_key' terraform/terraform.tfvars | cut -d'"' -f2)
        
        echo "🌐 Building frontend..."
        docker build --platform=linux/amd64 -t $REGISTRY_URL/frontend:latest \
          --build-arg NEXT_PUBLIC_SUPABASE_URL="$SUPABASE_URL" \
          --build-arg NEXT_PUBLIC_SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
          -f frontend/Dockerfile.production ./frontend
        docker push $REGISTRY_URL/frontend:latest
        
        cd terraform
        terraform apply -target=google_cloud_run_v2_service.frontend -auto-approve
        ;;
    
    backend)
        echo "⚙️  Building main backend..."
        docker build --platform=linux/amd64 -t $REGISTRY_URL/backend:latest -f backend/Dockerfile ./backend
        docker push $REGISTRY_URL/backend:latest
        
        cd terraform
        terraform apply -target=google_cloud_run_v2_service.main_backend -auto-approve
        ;;
    
    discovery)
        echo "🔍 Building discovery service..."
        docker build --platform=linux/amd64 -t $REGISTRY_URL/discovery-service:latest -f discovery-service/Dockerfile ./discovery-service
        docker push $REGISTRY_URL/discovery-service:latest
        
        cd terraform
        terraform apply -target=google_cloud_run_v2_service.discovery -auto-approve
        ;;
    
    monitoring)
        echo "👁️  Building monitoring service..."
        docker build --platform=linux/amd64 -t $REGISTRY_URL/content-monitoring-service:latest -f content-monitoring-service/Dockerfile ./content-monitoring-service
        docker push $REGISTRY_URL/content-monitoring-service:latest
        
        cd terraform
        terraform apply -target=google_cloud_run_v2_service.monitoring -auto-approve
        ;;
    
    notification)
        echo "📧 Building notification service..."
        docker build --platform=linux/amd64 -t $REGISTRY_URL/notification-service:latest -f notification-service/Dockerfile ./notification-service
        docker push $REGISTRY_URL/notification-service:latest
        
        cd terraform
        terraform apply -target=google_cloud_run_v2_service.notification -auto-approve
        ;;
esac

echo "✅ $SERVICE deployed!"
echo ""
echo "🔗 Service URL:"
case $SERVICE in
    frontend) terraform output frontend_url ;;
    backend) terraform output main_backend_url ;;
    discovery) terraform output discovery_service_url ;;
    monitoring) terraform output monitoring_service_url ;;
    notification) terraform output notification_service_url ;;
esac 