#!/bin/bash
# Cleanup script for branch deployments
# Usage: ./scripts/k8s-cleanup-branch.sh <branch-slug>
# Example: ./scripts/k8s-cleanup-branch.sh feat-auth

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

# Check arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <branch-slug>"
    echo ""
    echo "Available branch deployments:"
    kubectl get namespaces -l type=branch-deployment --no-headers -o custom-columns=":metadata.name"
    exit 1
fi

BRANCH_SLUG="$1"
NAMESPACE="torale-$BRANCH_SLUG"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log_error "Namespace '$NAMESPACE' not found"
    echo ""
    echo "Available branch deployments:"
    kubectl get namespaces -l type=branch-deployment --no-headers -o custom-columns=":metadata.name"
    exit 1
fi

# Confirm deletion
log_warning "This will delete the entire '$NAMESPACE' namespace and all resources within it."
read -p "Are you sure? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    log_info "Deletion cancelled"
    exit 0
fi

# Delete namespace
log_info "Deleting namespace '$NAMESPACE'..."
kubectl delete namespace "$NAMESPACE" --timeout=5m

log_success "Branch deployment '$BRANCH_SLUG' cleaned up successfully!"

# Show remaining branch deployments
REMAINING=$(kubectl get namespaces -l type=branch-deployment --no-headers | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo ""
    log_info "Remaining branch deployments:"
    kubectl get namespaces -l type=branch-deployment --no-headers -o custom-columns=":metadata.name,:metadata.labels.branch"
else
    log_success "No remaining branch deployments"
fi
