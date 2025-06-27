#!/bin/bash
# Test script for the Notification Service

echo "Testing Torale Notification Service"
echo "==================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8003"

# Test health endpoint
echo -e "\n1. Testing health endpoint..."
response=$(curl -s -w "\n%{http_code}" $BASE_URL/health)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $body"
else
    echo -e "${RED}✗ Health check failed (HTTP $http_code)${NC}"
    echo "Response: $body"
fi

# Test notification send endpoint
echo -e "\n2. Testing notification send endpoint..."
notification_data='{
    "user_email": "test@example.com",
    "query": "AI news updates",
    "target_url": "https://example.com/ai-news",
    "content": "Breaking: New AI model achieves groundbreaking performance on multiple benchmarks.",
    "alert_id": "12345678-1234-5678-1234-567812345678"
}'

response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$notification_data" \
    $BASE_URL/api/v1/notify)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓ Notification send test passed${NC}"
    echo "Response: $body"
else
    echo -e "${RED}✗ Notification send test failed (HTTP $http_code)${NC}"
    echo "Response: $body"
fi

# Test preferences endpoint
echo -e "\n3. Testing notification preferences endpoint..."
user_id="test-user-123"
response=$(curl -s -w "\n%{http_code}" $BASE_URL/api/v1/preferences/$user_id)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" == "200" ] || [ "$http_code" == "404" ]; then
    echo -e "${GREEN}✓ Preferences fetch test passed${NC}"
    echo "Response: $body"
else
    echo -e "${RED}✗ Preferences fetch test failed (HTTP $http_code)${NC}"
    echo "Response: $body"
fi

# Test queue status endpoint
echo -e "\n4. Testing queue status endpoint..."
response=$(curl -s -w "\n%{http_code}" $BASE_URL/api/v1/queue/status)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" == "200" ]; then
    echo -e "${GREEN}✓ Queue status test passed${NC}"
    echo "Response: $body"
else
    echo -e "${RED}✗ Queue status test failed (HTTP $http_code)${NC}"
    echo "Response: $body"
fi

echo -e "\n==================================="
echo "Notification service tests completed"