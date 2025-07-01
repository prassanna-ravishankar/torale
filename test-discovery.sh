#!/bin/bash
# Quick test script for discovery service

echo "Starting Discovery Service..."

# Start the service in background
cd discovery-service
uv run uvicorn app.main:app --port 8001 &
SERVICE_PID=$!
cd ..

# Wait for service to start
echo "Waiting for service to start..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8001/health)
echo "Health check result: $HEALTH"

if [[ $HEALTH == *"healthy"* ]]; then
    echo "✅ Health check passed!"
    
    # Test discovery endpoint
    echo "Testing discovery endpoint..."
    DISCOVERY=$(curl -s -X POST http://localhost:8001/api/v1/discover \
        -H "Content-Type: application/json" \
        -d '{"raw_query": "latest updates from OpenAI"}')
    
    echo "Discovery result: $DISCOVERY"
    
    if [[ $DISCOVERY == *"monitorable_urls"* ]]; then
        echo "✅ Discovery endpoint working!"
    else
        echo "❌ Discovery endpoint failed"
    fi
else
    echo "❌ Health check failed"
fi

# Cleanup
echo "Stopping service..."
kill $SERVICE_PID
echo "Done!"