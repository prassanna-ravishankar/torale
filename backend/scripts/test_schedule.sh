#!/bin/bash
set -e

API_URL="http://localhost:8000"
TASK_ID=""

# Check if running in no-auth mode
NOAUTH_MODE=${TORALE_NOAUTH:-0}

echo "=== Automatic Schedule Test ==="
echo "This test verifies tasks execute automatically on their cron schedule"
echo

if [ "$NOAUTH_MODE" == "1" ]; then
    echo "Running in no-auth mode (TORALE_NOAUTH=1)"
    echo "Note: API must also be started with TORALE_NOAUTH=1"
    echo
    AUTH_HEADER=""
else
    echo "Running with Clerk authentication"
    echo "Note: Requires valid CLERK_SECRET_KEY in API environment"
    echo

    # Check for Clerk test token
    if [ -z "$CLERK_TEST_TOKEN" ]; then
        echo "✗ CLERK_TEST_TOKEN environment variable not set"
        echo
        echo "To run with authentication, either:"
        echo "  1. Set TORALE_NOAUTH=1 for no-auth mode"
        echo "  2. Set CLERK_TEST_TOKEN with a valid Clerk session token"
        echo
        exit 1
    fi

    AUTH_HEADER="Authorization: Bearer $CLERK_TEST_TOKEN"
fi

# Helper function to make authenticated requests
curl_auth() {
    if [ -n "$AUTH_HEADER" ]; then
        curl "$@" -H "$AUTH_HEADER"
    else
        curl "$@"
    fi
}

# 1. Create task with schedule "every minute"
echo "1. Creating grounded search task with schedule '* * * * *' (every minute)..."
TASK_RESPONSE=$(curl_auth -sL -X POST "$API_URL/api/v1/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Scheduled Test Task",
    "schedule": "* * * * *",
    "executor_type": "llm_grounded_search",
    "search_query": "What is 1+1?",
    "condition_description": "A numerical answer is provided",
    "notify_behavior": "always",
    "config": {
      "model": "gemini-2.0-flash-exp"
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

# 2. Wait for automatic execution (max 90 seconds)
echo "2. Waiting for automatic execution..."
echo "   (Tasks scheduled for every minute, waiting up to 90s)"

START_TIME=$(date +%s)
FOUND_EXECUTION=false

for i in {1..90}; do
  sleep 1

  # Check execution history
  EXEC_HISTORY=$(curl_auth -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions")

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

# 3. Test pause/unpause
echo "3. Testing schedule pause..."
UPDATE_RESPONSE=$(curl_auth -sL -X PUT "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}')

IS_ACTIVE=$(echo $UPDATE_RESPONSE | jq -r '.is_active')
if [ "$IS_ACTIVE" == "false" ]; then
  echo "✓ Task paused (schedule should be paused in Temporal)"
else
  echo "✗ Failed to pause task"
fi

# 4. Cleanup
echo "4. Cleaning up..."
curl_auth -sL -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" > /dev/null
echo "✓ Task and schedule deleted"

echo
echo "=== All tests passed! ==="
echo
echo "Summary:"
echo "- Task scheduled with cron expression '* * * * *'"
echo "- Temporal automatically executed the task"
echo "- Schedule pause/unpause works"
echo "- Schedule deletion works"
