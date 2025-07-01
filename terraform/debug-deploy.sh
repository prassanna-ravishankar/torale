#!/bin/bash

# Debug deployment script - temporarily disables health checks to isolate startup issues
# Usage: ./debug-deploy.sh [service_name]

set -e

SERVICE=${1:-"discovery"}

echo "🐛 Debug deploying $SERVICE service (no health checks)..."

# Temporarily remove health checks from the service
case $SERVICE in
    discovery)
        echo "Deploying discovery service without health checks..."
        terraform apply -target=google_cloud_run_v2_service.discovery -auto-approve -var="debug_mode=true"
        ;;
    monitoring)
        echo "Deploying monitoring service without health checks..."
        terraform apply -target=google_cloud_run_v2_service.monitoring -auto-approve -var="debug_mode=true"
        ;;
    notification)
        echo "Deploying notification service without health checks..."
        terraform apply -target=google_cloud_run_v2_service.notification -auto-approve -var="debug_mode=true"
        ;;
    *)
        echo "❌ Invalid service: $SERVICE"
        echo "Valid services: discovery, monitoring, notification"
        exit 1
        ;;
esac

echo "✅ Debug deployment complete for $SERVICE"
echo ""
echo "🔍 Check service logs:"
echo "gcloud logs read --project=torale-464300 --resource-type=cloud_run_revision --filter=\"resource.labels.service_name=torale-$SERVICE\" --limit=50"
echo ""
echo "🔗 Service status:"
terraform output ${SERVICE}_service_url 