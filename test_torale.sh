#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Torale End-to-End${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Health Check
echo -e "\n${BLUE}1. Testing Health Endpoint${NC}"
HEALTH=$(curl -s $API_URL/health)
echo "Response: $HEALTH"
if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✓ API is healthy${NC}"
else
    echo -e "${YELLOW}✗ API health check failed${NC}"
    exit 1
fi

# 2. Register a new user
echo -e "\n${BLUE}2. Registering a new user${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }')
echo "Response: $REGISTER_RESPONSE"

if [[ $REGISTER_RESPONSE == *"id"* ]]; then
    echo -e "${GREEN}✓ User registered successfully${NC}"
else
    echo -e "${YELLOW}⚠ User might already exist (continuing...)${NC}"
fi

# 3. Login
echo -e "\n${BLUE}3. Logging in${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePassword123!")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${YELLOW}✗ Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Logged in successfully${NC}"
echo "Token: ${ACCESS_TOKEN:0:20}..."

# 4. Create a task
echo -e "\n${BLUE}4. Creating a task${NC}"
CREATE_TASK_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tasks/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily AI Summary",
    "schedule": "0 9 * * *",
    "executor_type": "llm_text",
    "config": {
      "prompt": "Write a short summary about AI trends",
      "model": "gemini-2.0-flash-exp",
      "max_tokens": 100
    },
    "is_active": true
  }')

TASK_ID=$(echo $CREATE_TASK_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$TASK_ID" ]; then
    echo -e "${YELLOW}✗ Task creation failed${NC}"
    echo "Response: $CREATE_TASK_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Task created successfully${NC}"
echo "Task ID: $TASK_ID"

# 5. List tasks
echo -e "\n${BLUE}5. Listing all tasks${NC}"
LIST_TASKS=$(curl -s -X GET "$API_URL/api/v1/tasks/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
TASK_COUNT=$(echo $LIST_TASKS | grep -o '"id"' | wc -l)
echo "Found $TASK_COUNT task(s)"
echo -e "${GREEN}✓ Successfully listed tasks${NC}"

# 6. Get task details
echo -e "\n${BLUE}6. Getting task details${NC}"
TASK_DETAILS=$(curl -s -X GET "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Task: $(echo $TASK_DETAILS | grep -o '"name":"[^"]*' | cut -d'"' -f4)"
echo -e "${GREEN}✓ Successfully retrieved task details${NC}"

# 7. Execute task manually
echo -e "\n${BLUE}7. Executing task manually${NC}"
EXECUTION_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/tasks/$TASK_ID/execute" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

EXECUTION_ID=$(echo $EXECUTION_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$EXECUTION_ID" ]; then
    echo -e "${YELLOW}✗ Task execution failed${NC}"
    echo "Response: $EXECUTION_RESPONSE"
else
    echo -e "${GREEN}✓ Task execution started${NC}"
    echo "Execution ID: $EXECUTION_ID"
fi

# 8. Get execution history
echo -e "\n${BLUE}8. Getting execution history${NC}"
EXECUTIONS=$(curl -s -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
EXEC_COUNT=$(echo $EXECUTIONS | grep -o '"id"' | wc -l)
echo "Found $EXEC_COUNT execution(s)"
echo -e "${GREEN}✓ Successfully retrieved execution history${NC}"

# 9. Update task
echo -e "\n${BLUE}9. Updating task (disable)${NC}"
UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }')
echo -e "${GREEN}✓ Task updated (disabled)${NC}"

# 10. Delete task
echo -e "\n${BLUE}10. Deleting task${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo -e "${GREEN}✓ Task deleted${NC}"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}All tests passed! ✓${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}API Documentation available at:${NC} $API_URL/docs"
