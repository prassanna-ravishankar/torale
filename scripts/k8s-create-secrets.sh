#!/bin/bash
set -e

echo "==============================================="
echo "Torale - Kubernetes Secrets Setup"
echo "==============================================="
echo ""

K8S_NAMESPACE="torale"
SECRET_NAME="torale-secrets"

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod file not found"
    echo "Please create .env.prod with your production secrets"
    echo "This should contain production Clerk keys (sk_live_..., pk_live_...)"
    exit 1
fi

# Load environment variables from .env.prod
export $(grep -v '^#' .env.prod | xargs)

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

prompt_if_missing "ANTHROPIC_API_KEY" "Enter your Anthropic API key (required - powers the monitoring agent):" "true"
prompt_if_missing "PERPLEXITY_API_KEY" "Enter your Perplexity API key (required - agent uses for search):" "true"
prompt_if_missing "SECRET_KEY" "Enter your JWT secret key (generate with: openssl rand -hex 32):" "true"
prompt_if_missing "DB_PASSWORD" "Enter your database password:" "true"
prompt_if_missing "CLERK_SECRET_KEY" "Enter your Clerk SECRET key (sk_live_... for production):" "true"
prompt_if_missing "CLERK_PUBLISHABLE_KEY" "Enter your Clerk PUBLISHABLE key (pk_live_... for production):" "false"
prompt_if_missing "NOVU_SECRET_KEY" "Enter your Novu SECRET key (production):" "true"

# Optional secrets
if [ -z "$MEM0_API_KEY" ]; then
    echo ""
    echo "Mem0 API key not set (optional - agent cross-run memory). Press Enter to skip or paste key:"
    read -s MEM0_API_KEY
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "OpenAI API key not set (optional). Press Enter to skip or paste key:"
    read -s OPENAI_API_KEY
fi

if [ -z "$NOTIFICATION_API_KEY" ]; then
    echo ""
    echo "Notification API key not set (optional). Press Enter to skip or paste key:"
    read -s NOTIFICATION_API_KEY
fi

if [ -z "$LOGFIRE_TOKEN" ]; then
    echo ""
    echo "Logfire token not set (optional - agent observability). Press Enter to skip or paste token:"
    read -s LOGFIRE_TOKEN
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
    --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    --from-literal=PERPLEXITY_API_KEY="$PERPLEXITY_API_KEY" \
    --from-literal=SECRET_KEY="$SECRET_KEY" \
    --from-literal=DB_PASSWORD="$DB_PASSWORD" \
    --from-literal=CLERK_SECRET_KEY="$CLERK_SECRET_KEY" \
    --from-literal=NOVU_SECRET_KEY="$NOVU_SECRET_KEY" \
    --from-literal=MEM0_API_KEY="${MEM0_API_KEY:-}" \
    --from-literal=OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    --from-literal=NOTIFICATION_API_KEY="${NOTIFICATION_API_KEY:-}" \
    --from-literal=LOGFIRE_TOKEN="${LOGFIRE_TOKEN:-}"

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

# Update Helm values with production Clerk publishable key
if [ -n "$CLERK_PUBLISHABLE_KEY" ]; then
    echo "Updating Helm values-production.yaml with Clerk publishable key..."
    sed -i.bak "s|publishableKey:.*|publishableKey: $CLERK_PUBLISHABLE_KEY|" helm/torale/values-production.yaml
    rm helm/torale/values-production.yaml.bak
    echo "✓ Helm values updated"
    echo ""
fi

echo "Next steps:"
echo "  1. Deploy application: just k8s-deploy-all"
echo "  2. Check status: just k8s-status"
echo ""
