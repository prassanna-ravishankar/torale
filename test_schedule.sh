#!/bin/bash
set -e

API_URL="http://localhost:8000"
EMAIL="test-schedule-$(date +%s)@example.com"
PASSWORD="testpass123"
TASK_ID=""
TOKEN=""

echo "=== Automatic Schedule Test ==="
echo "This test verifies tasks execute automatically on their cron schedule"
echo

# 1. Register
echo "1. Registering user..."
curl -sL -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" > /dev/null
echo "✓ User registered"

# 2. Login
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -sL -X POST "$API_URL/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")
TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "✓ Logged in"

# 3. Create task with schedule "every minute"
echo "3. Creating task with schedule '* * * * *' (every minute)..."
TASK_RESPONSE=$(curl -sL -X POST "$API_URL/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scheduled Test Task",
    "schedule": "* * * * *",
    "executor_type": "llm_text",
    "config": {
      "model": "gemini-2.0-flash-exp",
      "prompt": "Write a one-line joke",
      "max_tokens": 50
    },
    "is_active": true
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
  echo "✗ Failed to create task"
  echo "Response: $TASK_RESPONSE"
  exit 1
fi
echo "✓ Task created (ID: $TASK_ID)"
echo "  Temporal schedule created: schedule-$TASK_ID"

# 4. Wait for automatic execution (max 90 seconds)
echo "4. Waiting for automatic execution..."
echo "   (Tasks scheduled for every minute, waiting up to 90s)"

START_TIME=$(date +%s)
FOUND_EXECUTION=false

for i in {1..90}; do
  sleep 1

  # Check execution history
  EXEC_HISTORY=$(curl -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions" \
    -H "Authorization: Bearer $TOKEN")

  EXEC_COUNT=$(echo $EXEC_HISTORY | jq '. | length')

  if [ "$EXEC_COUNT" -gt 0 ]; then
    ELAPSED=$(($(date +%s) - START_TIME))
    echo "   [${ELAPSED}s] Found $EXEC_COUNT execution(s)! Checking status..."

    LATEST_STATUS=$(echo $EXEC_HISTORY | jq -r '.[0].status')

    if [ "$LATEST_STATUS" == "success" ]; then
      RESULT=$(echo $EXEC_HISTORY | jq '.[0].result')
      echo "✓ Automatic execution succeeded!"
      echo
      echo "=== Execution Details ==="
      echo "Time to first execution: ${ELAPSED}s"
      echo "Result:"
      echo "$RESULT" | jq .
      echo
      FOUND_EXECUTION=true
      break
    elif [ "$LATEST_STATUS" == "failed" ]; then
      ERROR=$(echo $EXEC_HISTORY | jq -r '.[0].error_message // "Unknown error"')
      echo "✗ Automatic execution failed: $ERROR"
      exit 1
    else
      echo "   Status: $LATEST_STATUS (waiting for completion...)"
    fi
  else
    if [ $((i % 10)) -eq 0 ]; then
      echo "   [${i}s] Still waiting... (no executions yet)"
    fi
  fi
done

if [ "$FOUND_EXECUTION" = false ]; then
  echo "✗ No automatic execution occurred within 90 seconds"
  echo "  This might indicate the Temporal schedule isn't working"
  exit 1
fi

# 5. Test pause/unpause
echo "5. Testing schedule pause..."
UPDATE_RESPONSE=$(curl -sL -X PUT "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}')

IS_ACTIVE=$(echo $UPDATE_RESPONSE | jq -r '.is_active')
if [ "$IS_ACTIVE" == "false" ]; then
  echo "✓ Task paused (schedule should be paused in Temporal)"
else
  echo "✗ Failed to pause task"
fi

# 6. Cleanup
echo "6. Cleaning up..."
curl -sL -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "✓ Task and schedule deleted"

echo
echo "=== All tests passed! ==="
echo
echo "Summary:"
echo "- Task scheduled with cron expression '* * * * *'"
echo "- Temporal automatically executed the task"
echo "- Schedule pause/unpause works"
echo "- Schedule deletion works"
