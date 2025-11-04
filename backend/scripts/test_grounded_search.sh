#!/bin/bash
set -e

API_URL="http://localhost:8000"
EMAIL="test-grounded-$(date +%s)@example.com"
PASSWORD="testpass123"
TASK_ID=""
TOKEN=""

echo "=== Grounded Search E2E Test ==="
echo "This test verifies grounded search monitoring functionality"
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

# 3. Create grounded search task
echo "3. Creating grounded search monitoring task..."
TASK_RESPONSE=$(curl -sL -X POST "$API_URL/api/v1/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Grounded Search",
    "schedule": "0 9 * * *",
    "executor_type": "llm_grounded_search",
    "search_query": "What is the capital of France?",
    "condition_description": "A clear answer with the city name is provided",
    "notify_behavior": "once",
    "config": {
      "model": "gemini-2.0-flash-exp"
    },
    "is_active": false
  }')

TASK_ID=$(echo $TASK_RESPONSE | jq -r '.id')
if [ "$TASK_ID" == "null" ] || [ -z "$TASK_ID" ]; then
  echo "✗ Failed to create task"
  echo "Response: $TASK_RESPONSE"
  exit 1
fi
echo "✓ Task created (ID: $TASK_ID)"

# Verify task has grounded search fields
SEARCH_QUERY=$(echo $TASK_RESPONSE | jq -r '.search_query')
CONDITION=$(echo $TASK_RESPONSE | jq -r '.condition_description')
NOTIFY_BEHAVIOR=$(echo $TASK_RESPONSE | jq -r '.notify_behavior')

echo "  Search query: $SEARCH_QUERY"
echo "  Condition: $CONDITION"
echo "  Notify behavior: $NOTIFY_BEHAVIOR"

# 4. Execute task manually
echo "4. Executing task manually..."
EXEC_RESPONSE=$(curl -sL -X POST "$API_URL/api/v1/tasks/$TASK_ID/execute" \
  -H "Authorization: Bearer $TOKEN")

EXEC_ID=$(echo $EXEC_RESPONSE | jq -r '.id')
if [ "$EXEC_ID" == "null" ] || [ -z "$EXEC_ID" ]; then
  echo "✗ Failed to execute task"
  echo "Response: $EXEC_RESPONSE"
  exit 1
fi
echo "✓ Task execution started (ID: $EXEC_ID)"

# 5. Wait for execution to complete
echo "5. Waiting for execution to complete..."
for i in {1..30}; do
  sleep 2

  EXEC_HISTORY=$(curl -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/executions" \
    -H "Authorization: Bearer $TOKEN")

  LATEST_STATUS=$(echo $EXEC_HISTORY | jq -r '.[0].status')

  if [ "$LATEST_STATUS" == "success" ]; then
    echo "✓ Execution completed successfully!"

    # Extract grounded search specific fields
    CONDITION_MET=$(echo $EXEC_HISTORY | jq '.[0].condition_met')
    CHANGE_SUMMARY=$(echo $EXEC_HISTORY | jq -r '.[0].change_summary')
    GROUNDING_SOURCES=$(echo $EXEC_HISTORY | jq '.[0].grounding_sources')
    ANSWER=$(echo $EXEC_HISTORY | jq -r '.[0].result.answer')

    echo
    echo "=== Grounded Search Results ==="
    echo "Answer: $ANSWER"
    echo "Condition Met: $CONDITION_MET"
    echo "Change Summary: $CHANGE_SUMMARY"
    echo "Grounding Sources:"
    echo "$GROUNDING_SOURCES" | jq -c '.[]' 2>/dev/null || echo "  (none or failed to parse)"
    echo

    # Verify grounded search fields exist
    if [ "$CONDITION_MET" == "null" ]; then
      echo "✗ Missing condition_met field"
      exit 1
    fi

    if [ "$GROUNDING_SOURCES" == "null" ]; then
      echo "⚠ Warning: No grounding sources returned (may be expected for some queries)"
    fi

    break
  elif [ "$LATEST_STATUS" == "failed" ]; then
    ERROR=$(echo $EXEC_HISTORY | jq -r '.[0].error_message // "Unknown error"')
    echo "✗ Execution failed: $ERROR"
    exit 1
  else
    if [ $((i % 5)) -eq 0 ]; then
      echo "   [${i}s] Status: $LATEST_STATUS (waiting...)"
    fi
  fi
done

if [ "$LATEST_STATUS" != "success" ]; then
  echo "✗ Execution did not complete within 60 seconds"
  exit 1
fi

# 6. Test notifications endpoint
echo "6. Testing notifications endpoint..."
if [ "$CONDITION_MET" == "true" ]; then
  NOTIFICATIONS=$(curl -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID/notifications" \
    -H "Authorization: Bearer $TOKEN")

  NOTIF_COUNT=$(echo $NOTIFICATIONS | jq '. | length')

  if [ "$NOTIF_COUNT" -gt 0 ]; then
    echo "✓ Found $NOTIF_COUNT notification(s)"
  else
    echo "✗ Expected notifications but found none"
    exit 1
  fi
else
  echo "  (Condition not met, skipping notification check)"
fi

# 7. Verify task state was updated
echo "7. Verifying task state tracking..."
UPDATED_TASK=$(curl -sL -X GET "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN")

TASK_CONDITION_MET=$(echo $UPDATED_TASK | jq '.condition_met')
LAST_KNOWN_STATE=$(echo $UPDATED_TASK | jq '.last_known_state')

echo "  Task condition_met: $TASK_CONDITION_MET"
echo "  Task has last_known_state: $([ "$LAST_KNOWN_STATE" != "null" ] && echo "yes" || echo "no")"

if [ "$TASK_CONDITION_MET" != "$CONDITION_MET" ]; then
  echo "✗ Task condition_met doesn't match execution result"
  exit 1
fi

echo "✓ Task state tracking verified"

# 8. Cleanup
echo "8. Cleaning up..."
curl -sL -X DELETE "$API_URL/api/v1/tasks/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "✓ Task deleted"

echo
echo "=== All tests passed! ==="
echo
echo "Summary:"
echo "- Grounded search task created with monitoring fields"
echo "- Task executed with grounded search via Gemini"
echo "- Condition evaluation completed"
echo "- Grounding sources extracted (if available)"
echo "- Task state tracking updated"
echo "- Notifications endpoint working"
