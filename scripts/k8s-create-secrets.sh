#!/bin/bash
set -e

echo "==============================================="
echo "Torale - Kubernetes Secrets Setup"
echo "==============================================="
echo ""

K8S_NAMESPACE="torale"
SECRET_NAME="torale-secrets"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "Please create .env from .env.example first"
    exit 1
fi

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)

# Check if Cloud SQL info exists
if [ -f .cloud-sql-info ]; then
    echo "✓ Found Cloud SQL connection info"
    export $(grep -v '^#' .cloud-sql-info | xargs)
else
    echo "⚠️  Cloud SQL info not found. Using .env values for DB_PASSWORD"
fi

# Function to prompt for missing values
prompt_if_missing() {
    local var_name=$1
    local prompt_text=$2
    local is_secret=$3

    if [ -z "${!var_name}" ]; then
        echo "$prompt_text"
        if [ "$is_secret" = "true" ]; then
            read -s value
        else
            read value
        fi
        export $var_name="$value"
    fi
}

# Check required secrets
echo "Checking required secrets..."
echo ""

prompt_if_missing "GOOGLE_API_KEY" "Enter your Google AI API key (required):" "true"
prompt_if_missing "SECRET_KEY" "Enter your JWT secret key (generate with: openssl rand -hex 32):" "true"
prompt_if_missing "DB_PASSWORD" "Enter your database password:" "true"
prompt_if_missing "CLERK_SECRET_KEY" "Enter your Clerk secret key (required):" "true"
prompt_if_missing "TEMPORAL_API_KEY" "Enter your Temporal API key (required for Temporal Cloud):" "true"

# Optional secrets
if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "OpenAI API key not set (optional). Press Enter to skip or paste key:"
    read -s OPENAI_API_KEY
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "Anthropic API key not set (optional). Press Enter to skip or paste key:"
    read -s ANTHROPIC_API_KEY
fi

if [ -z "$NOTIFICATION_API_KEY" ]; then
    echo ""
    echo "Notification API key not set (optional). Press Enter to skip or paste key:"
    read -s NOTIFICATION_API_KEY
fi

echo ""
echo ""

# Create namespace if it doesn't exist
kubectl create namespace "$K8S_NAMESPACE" 2>/dev/null || echo "✓ Namespace '$K8S_NAMESPACE' exists"

# Delete existing secret if it exists
kubectl delete secret "$SECRET_NAME" -n "$K8S_NAMESPACE" 2>/dev/null || true

# Create secret
echo "Creating Kubernetes secret..."
kubectl create secret generic "$SECRET_NAME" \
    --namespace="$K8S_NAMESPACE" \
    --from-literal=GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    --from-literal=SECRET_KEY="$SECRET_KEY" \
    --from-literal=DB_PASSWORD="$DB_PASSWORD" \
    --from-literal=CLERK_SECRET_KEY="$CLERK_SECRET_KEY" \
    --from-literal=TEMPORAL_API_KEY="$TEMPORAL_API_KEY" \
    --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    --from-literal=ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
    --from-literal=NOTIFICATION_API_KEY="${NOTIFICATION_API_KEY:-}"

echo "✓ Secret '$SECRET_NAME' created in namespace '$K8S_NAMESPACE'"
echo ""

# Verify secret
echo "Verifying secret..."
kubectl get secret "$SECRET_NAME" -n "$K8S_NAMESPACE" -o yaml | grep -E "name:|namespace:" | head -2

echo ""
echo "==============================================="
echo "✓ Secrets Setup Complete!"
echo "==============================================="
echo ""
echo "Next steps:"
echo "  1. Deploy application: just k8s-deploy-all"
echo "  2. Check status: just k8s-status"
echo ""
