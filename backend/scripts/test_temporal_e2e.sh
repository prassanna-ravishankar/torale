#!/bin/bash
set -e

API_URL="http://localhost:8000"
TASK_ID=""
EXECUTION_ID=""

# Check if running in no-auth mode
NOAUTH_MODE=${TORALE_NOAUTH:-0}

echo "=== Temporal E2E Test ==="
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
        echo "Example:"
        echo "  export CLERK_TEST_TOKEN='your-clerk-session-token'"
        echo "  ./backend/scripts/test_temporal_e2e.sh"
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

# 1. Create task
echo "1. Creating grounded search task..."
TASK_RESPONSE=$(curl_auth -sL -X POST "$API_URL/api/v1/tasks" \
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

# 2. Execute task
echo "2. Executing task (triggering Temporal workflow)..."
EXEC_RESPONSE=$(curl_auth -sL -X POST "$API_URL/api/v1/tasks/$TASK_ID/execute")

EXECUTION_ID=$(echo $EXEC_RESPONSE | jq -r '.id')
EXEC_STATUS=$(echo $EXEC_RESPONSE | jq -r '.status')

if [ "$EXECUTION_ID" == "null" ] || [ -z "$EXECUTION_ID" ]; then
  echo "✗ Failed to start execution"
  echo "Response: $EXEC_RESPONSE"
  exit 1
fi
echo "✓ Execution started (ID: $EXECUTION_ID, initial status: $EXEC_STATUS)"

# 3. Poll for completion
echo "3. Polling for execution completion (max 60s)..."
for i in {1..60}; do
  sleep 1
  EXEC_HISTORY=$(curl_auth -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions")

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

# 4. Cleanup
echo "4. Cleaning up..."
curl_auth -sL -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" > /dev/null
echo "✓ Task deleted"

echo
echo "=== All tests passed! ==="
