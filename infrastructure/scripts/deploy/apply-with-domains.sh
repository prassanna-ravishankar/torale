#!/bin/bash

# Script to apply terraform configuration with custom domains enabled
# Make sure to verify your domain in Google Search Console first!

set -e

echo "🔍 Checking if torale.ai is verified..."
VERIFIED_DOMAINS=$(gcloud domains list-user-verified --format="value(id)")

if echo "$VERIFIED_DOMAINS" | grep -q "torale.ai"; then
    echo "✅ torale.ai is verified. Proceeding with terraform apply..."
    
    # Need to get the actual Cloudflare API token
    echo "⚠️  You'll need to provide your Cloudflare API token when prompted"
    echo "   Get it from: https://dash.cloudflare.com/profile/api-tokens"
    echo "   Make sure it has Zone:Read and Zone:Edit permissions for torale.ai"
    echo ""
    
    # Apply terraform with custom domains enabled
    terraform apply \
        -var="enable_cloudflare=true" \
        -var="domain=torale.ai" \
        -var="cloudflare_api_token=${CLOUDFLARE_API_TOKEN:-}"
else
    echo "❌ torale.ai is not verified yet."
    echo ""
    echo "Please complete domain verification first:"
    echo "1. Go to Google Search Console (opened automatically)"
    echo "2. Add and verify torale.ai"
    echo "3. Run this script again"
    echo ""
    echo "To verify now, run: gcloud domains verify torale.ai"
    exit 1
fi 