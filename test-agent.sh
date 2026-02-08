#!/bin/bash
# Test agent A2A protocol

# Send a task to the agent
echo "Sending task to agent..."
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "kind": "message",
        "messageId": "msg-001",
        "role": "user",
        "parts": [{
          "kind": "text",
          "text": "<user-task>Check when the iPhone 16 will be released</user-task>"
        }]
      }
    }
  }' | jq .

echo ""
echo "Get the task ID from above, then poll for result:"
echo ""
echo 'TASK_ID="<paste-task-id-here>"'
echo ""
echo 'curl -X POST http://localhost:8001/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -d "{'
echo '    \"jsonrpc\": \"2.0\",'
echo '    \"id\": \"2\",'
echo '    \"method\": \"tasks/get\",'
echo '    \"params\": {'
echo '      \"id\": \"$TASK_ID\"'
echo '    }'
echo '  }" | jq .'

echo ""
echo "--- OR use this one-liner to send and poll automatically: ---"
echo ""
cat << 'EOF'
TASK_ID=$(curl -s -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "kind": "message",
        "messageId": "msg-001",
        "role": "user",
        "parts": [{
          "kind": "text",
          "text": "<user-task>Test task to trigger 429</user-task>"
        }]
      }
    }
  }' | jq -r '.result.id') && \
sleep 3 && \
curl -s -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": \"2\",
    \"method\": \"tasks/get\",
    \"params\": {
      \"id\": \"$TASK_ID\"
    }
  }" | jq '.result.status'
EOF
