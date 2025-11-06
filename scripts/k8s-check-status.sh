#!/bin/bash

echo "==============================================="
echo "Torale - Kubernetes Deployment Status"
echo "==============================================="
echo ""

K8S_NAMESPACE="torale"
TEMPORAL_NAMESPACE="temporal"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check pod status
check_pods() {
    local namespace=$1
    local label=$2

    echo "Checking $label pods in namespace '$namespace'..."

    pods=$(kubectl get pods -n "$namespace" -l "$label" -o json 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$pods" ]; then
        echo -e "${RED}✗ No pods found${NC}"
        return
    fi

    ready=$(echo "$pods" | jq -r '.items[] | select(.status.phase=="Running" and (.status.conditions[] | select(.type=="Ready" and .status=="True"))) | .metadata.name' | wc -l)
    total=$(echo "$pods" | jq -r '.items | length')

    if [ "$ready" -eq "$total" ] && [ "$total" -gt 0 ]; then
        echo -e "${GREEN}✓ $ready/$total pods ready${NC}"
    elif [ "$ready" -gt 0 ]; then
        echo -e "${YELLOW}⚠ $ready/$total pods ready${NC}"
    else
        echo -e "${RED}✗ 0/$total pods ready${NC}"
    fi

    kubectl get pods -n "$namespace" -l "$label" 2>/dev/null || true
    echo ""
}

# Check Temporal pods
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEMPORAL SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_pods "$TEMPORAL_NAMESPACE" "app.kubernetes.io/name=temporal"

# Check Torale pods
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TORALE APPLICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_pods "$K8S_NAMESPACE" "app.kubernetes.io/component=api"
check_pods "$K8S_NAMESPACE" "app.kubernetes.io/component=worker"
check_pods "$K8S_NAMESPACE" "app.kubernetes.io/component=frontend"

# Check services
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SERVICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
kubectl get svc -n "$K8S_NAMESPACE" 2>/dev/null || echo "No services found"
echo ""

# Check ingress
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "INGRESS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ingress_ip=$(kubectl get ingress -n "$K8S_NAMESPACE" -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' 2>/dev/null)

if [ -n "$ingress_ip" ]; then
    echo -e "${GREEN}✓ Ingress IP: $ingress_ip${NC}"
else
    echo -e "${YELLOW}⚠ Ingress IP not yet assigned (this can take 5-10 minutes)${NC}"
fi

kubectl get ingress -n "$K8S_NAMESPACE" 2>/dev/null || echo "No ingress found"
echo ""

# Check SSL certificate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SSL CERTIFICATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cert_status=$(kubectl get managedcertificate -n "$K8S_NAMESPACE" -o jsonpath='{.items[0].status.certificateStatus}' 2>/dev/null)

if [ "$cert_status" = "Active" ]; then
    echo -e "${GREEN}✓ Certificate status: Active${NC}"
elif [ "$cert_status" = "Provisioning" ]; then
    echo -e "${YELLOW}⚠ Certificate status: Provisioning (takes 10-15 minutes)${NC}"
elif [ -n "$cert_status" ]; then
    echo -e "${YELLOW}⚠ Certificate status: $cert_status${NC}"
else
    echo -e "${YELLOW}⚠ Certificate not found${NC}"
fi

kubectl get managedcertificate -n "$K8S_NAMESPACE" 2>/dev/null || true
echo ""

# DNS instructions
if [ -n "$ingress_ip" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "DNS CONFIGURATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Add these DNS A records to your domain (torale.ai):"
    echo ""
    echo "  torale.ai     →  $ingress_ip"
    echo "  api.torale.ai →  $ingress_ip"
    echo ""
    echo "Check DNS propagation:"
    echo "  dig torale.ai +short"
    echo "  dig api.torale.ai +short"
    echo ""
fi

# Application URLs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "APPLICATION ACCESS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$cert_status" = "Active" ]; then
    echo -e "${GREEN}Frontend: https://torale.ai${NC}"
    echo -e "${GREEN}API:      https://api.torale.ai${NC}"
else
    if [ -n "$ingress_ip" ]; then
        echo "Frontend: http://$ingress_ip (HTTPS available once cert is active)"
        echo "API:      http://$ingress_ip (HTTPS available once cert is active)"
    else
        echo "Waiting for ingress IP assignment..."
    fi
fi

echo ""
echo "Port forwarding (for local access):"
echo "  API:        just k8s-port-forward-api"
echo "  Temporal:   just k8s-port-forward-temporal"
echo ""

echo "==============================================="
echo "Status Check Complete"
echo "==============================================="
