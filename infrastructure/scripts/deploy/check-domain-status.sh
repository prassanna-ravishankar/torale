#!/bin/bash

# Script to monitor domain mapping status and test site availability

set -e

echo "🔍 Monitoring domain mapping status..."
echo "This typically takes 5-15 minutes for SSL certificate provisioning."
echo ""

check_count=0
max_checks=30  # 15 minutes with 30-second intervals

while [ $check_count -lt $max_checks ]; do
    check_count=$((check_count + 1))
    echo "📊 Check $check_count/$max_checks $(date '+%H:%M:%S')"
    
    # Check domain mapping status
    echo "🔗 Domain mappings status:"
    gcloud beta run domain-mappings list --region us-central1 --format="table(name,status.conditions[0].type,status.conditions[0].status)"
    
    echo ""
    echo "🌐 Testing website accessibility:"
    
    # Test app.torale.ai
    APP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.torale.ai 2>/dev/null || echo "000")
    if [ "$APP_STATUS" = "200" ]; then
        echo "✅ app.torale.ai: WORKING! (HTTP $APP_STATUS)"
        APP_READY=true
    else
        echo "⏳ app.torale.ai: HTTP $APP_STATUS (still provisioning...)"
        APP_READY=false
    fi
    
    # Test api.torale.ai  
    API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.torale.ai 2>/dev/null || echo "000")
    if [ "$API_STATUS" = "200" ] || [ "$API_STATUS" = "404" ]; then
        echo "✅ api.torale.ai: WORKING! (HTTP $API_STATUS)"
        API_READY=true
    else
        echo "⏳ api.torale.ai: HTTP $API_STATUS (still provisioning...)"
        API_READY=false
    fi
    
    echo ""
    
    # Check if both are ready
    if [ "$APP_READY" = true ] && [ "$API_READY" = true ]; then
        echo "🎉 SUCCESS! Both domains are now working:"
        echo "   🌐 Frontend: https://app.torale.ai"
        echo "   🔗 API: https://api.torale.ai"
        echo ""
        echo "🚀 Your Torale application is now live on your custom domain!"
        exit 0
    fi
    
    if [ $check_count -lt $max_checks ]; then
        echo "⏱️  Waiting 30 seconds before next check..."
        sleep 30
        echo ""
    fi
done

echo "⚠️  SSL certificate provisioning is taking longer than expected."
echo "   This can sometimes take up to 60 minutes for new domains."
echo "   Your site should become available automatically once certificates are issued."
echo ""
echo "📋 You can continue monitoring with:"
echo "   gcloud beta run domain-mappings list --region us-central1"
echo "   curl -I https://app.torale.ai" 