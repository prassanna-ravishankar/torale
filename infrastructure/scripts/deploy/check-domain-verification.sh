#!/bin/bash

# Script to check domain verification status and apply terraform when ready

set -e

echo "🔍 Checking domain verification status..."

while true; do
    VERIFIED_DOMAINS=$(gcloud domains list-user-verified --format="value(id)")
    
    APP_VERIFIED=$(echo "$VERIFIED_DOMAINS" | grep -c "app.torale.ai" || echo "0")
    API_VERIFIED=$(echo "$VERIFIED_DOMAINS" | grep -c "api.torale.ai" || echo "0")
    
    echo "Status:"
    echo "  ✅ torale.ai: Verified"
    echo "  $([ $APP_VERIFIED -eq 1 ] && echo "✅" || echo "❌") app.torale.ai: $([ $APP_VERIFIED -eq 1 ] && echo "Verified" || echo "Not verified")"
    echo "  $([ $API_VERIFIED -eq 1 ] && echo "✅" || echo "❌") api.torale.ai: $([ $API_VERIFIED -eq 1 ] && echo "Verified" || echo "Not verified")"
    echo ""
    
    if [ $APP_VERIFIED -eq 1 ] && [ $API_VERIFIED -eq 1 ]; then
        echo "🎉 All domains verified! Applying terraform..."
        echo ""
        
        cd infrastructure/terraform/environments/dev
        export CLOUDFLARE_API_TOKEN="TDkacInRRGMBtEzmG-uZsVHs7l3krIGZkYkQAePq"
        
        terraform apply \
            -var="enable_cloudflare=true" \
            -var="domain=torale.ai" \
            -var="cloudflare_api_token=$CLOUDFLARE_API_TOKEN" \
            -auto-approve
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "🚀 SUCCESS! Domain mappings created:"
            echo "   https://app.torale.ai -> Cloud Run Frontend"
            echo "   https://api.torale.ai -> Cloud Run Backend"
            echo ""
            echo "🕐 SSL certificates are being issued (5-15 minutes)"
            echo "   Your site should be live shortly!"
        fi
        break
    else
        echo "⏳ Waiting for domain verification..."
        echo "   Complete verification in Google Search Console tabs"
        echo "   Checking again in 30 seconds..."
        echo ""
        sleep 30
    fi
done 