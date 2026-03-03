#!/bin/bash
# Run all active tasks once (for catching up stale tasks)

# Check for required dependencies
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Install with: brew install jq"
    exit 1
fi

API_URL="${1:-https://api.torale.ai}"

# Read token from environment variable to avoid shell history
if [ -z "$TORALE_BEARER_TOKEN" ]; then
    echo "Error: TORALE_BEARER_TOKEN environment variable not set"
    echo "Usage: TORALE_BEARER_TOKEN=your-token $0 [API_URL]"
    echo "Example: TORALE_BEARER_TOKEN=your-token $0 https://api.torale.ai"
    exit 1
fi
BEARER_TOKEN="$TORALE_BEARER_TOKEN"

echo "Fetching all active tasks from $API_URL..."
TASKS=$(curl -s "$API_URL/admin/queries?active_only=true&limit=500" \
    -H "Authorization: Bearer $BEARER_TOKEN")

# Check if response is an error
if echo "$TASKS" | jq -e '.detail' > /dev/null 2>&1; then
    ERROR=$(echo "$TASKS" | jq -r '.detail')
    echo "Error: $ERROR"
    exit 1
fi

# Extract task IDs (response has format {"queries": [...], "total": N})
TASK_IDS=$(echo "$TASKS" | jq -r '.queries[]?.id' 2>&1)

if [ -z "$TASK_IDS" ]; then
    echo "No active tasks found"
    exit 0
fi

TASK_COUNT=$(echo "$TASK_IDS" | wc -l)
echo "Found $TASK_COUNT active tasks"
echo ""

# Execute each task
COUNTER=0
for TASK_ID in $TASK_IDS; do
    COUNTER=$((COUNTER + 1))
    echo "[$COUNTER/$TASK_COUNT] Executing task $TASK_ID..."

    RESPONSE=$(curl -s -X POST "$API_URL/admin/tasks/$TASK_ID/execute?suppress_notifications=true" \
        -H "Authorization: Bearer $BEARER_TOKEN")

    # Check if successful
    if echo "$RESPONSE" | jq -e '.execution_id' > /dev/null 2>&1; then
        EXEC_ID=$(echo "$RESPONSE" | jq -r '.execution_id')
        echo "  ✓ Started execution $EXEC_ID"
    else
        echo "  ✗ Failed: $RESPONSE"
    fi

    # Small delay to avoid overwhelming the system
    sleep 0.5
done

echo ""
echo "Done! Executed $COUNTER tasks"
