#!/bin/bash
set -e

API_URL="http://localhost:8000"
EMAIL="test-$(date +%s)@example.com"
PASSWORD="testpass123"
TASK_ID=""
EXECUTION_ID=""
TOKEN=""

echo "=== Temporal E2E Test ==="
echo

# 1. Register
echo "1. Registering user..."
curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" > /dev/null
echo "✓ User registered"

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "✓ Logged in (token: ${TOKEN:0:20}...)"

# 3. Create task
echo "3. Creating grounded search task..."
TASK_RESPONSE=$(curl -sL -X POST "$API_URL/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2E Test Task",
    "schedule": "0 9 * * *",
    "executor_type": "llm_grounded_search",
    "search_query": "What is 2+2?",
    "condition_description": "A numerical answer is provided",
    "notify_behavior": "always",
    "config": {
      "model": "gemini-2.0-flash-exp"
    }
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
  echo "✗ Failed to create task"
  echo "Response: $TASK_RESPONSE"
  exit 1
fi
echo "✓ Task created (ID: $TASK_ID)"

# 4. Execute task
echo "4. Executing task (triggering Temporal workflow)..."
EXEC_RESPONSE=$(curl -sL -X POST "$API_URL/api/v1/tasks/$TASK_ID/execute" \
  -H "Authorization: Bearer $TOKEN")

EXECUTION_ID=$(echo $EXEC_RESPONSE | jq -r '.id')
EXEC_STATUS=$(echo $EXEC_RESPONSE | jq -r '.status')

if [ "$EXECUTION_ID" == "null" ] || [ -z "$EXECUTION_ID" ]; then
  echo "✗ Failed to start execution"
  echo "Response: $EXEC_RESPONSE"
  exit 1
fi
echo "✓ Execution started (ID: $EXECUTION_ID, initial status: $EXEC_STATUS)"

# 5. Poll for completion
echo "5. Polling for execution completion (max 60s)..."
for i in {1..60}; do
  sleep 1
  EXEC_HISTORY=$(curl -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions" \
    -H "Authorization: Bearer $TOKEN")

  # Check if response is an array
  IS_ARRAY=$(echo $EXEC_HISTORY | jq -r 'type')
  if [ "$IS_ARRAY" != "array" ]; then
    echo "✗ Unexpected response format: $EXEC_HISTORY"
    exit 1
  fi

  CURRENT_STATUS=$(echo $EXEC_HISTORY | jq -r '.[0].status // "unknown"')
  echo -n "   [${i}s] Status: $CURRENT_STATUS"

  if [ "$CURRENT_STATUS" == "success" ]; then
    echo " ✓"
    RESULT=$(echo $EXEC_HISTORY | jq '.[0].result')
    echo "✓ Execution completed successfully!"
    echo
    echo "=== Result ==="
    echo "$RESULT" | jq .
    echo
    break
  elif [ "$CURRENT_STATUS" == "failed" ]; then
    echo " ✗"
    ERROR=$(echo $EXEC_HISTORY | jq -r '.[0].error_message // "Unknown error"')
    echo "✗ Execution failed: $ERROR"
    exit 1
  else
    echo " (waiting...)"
  fi

  if [ $i -eq 60 ]; then
    echo "✗ Timeout waiting for execution"
    exit 1
  fi
done

# 6. Cleanup
echo "6. Cleaning up..."
curl -sL -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "✓ Task deleted"

echo
echo "=== All tests passed! ==="
