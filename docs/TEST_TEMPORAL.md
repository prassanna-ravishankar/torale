# Testing Temporal Integration

## Quick Start

### Option 1: Full Docker Stack
```bash
# Start everything
docker compose up -d

# Wait for services to be ready (30s)
sleep 30

# Run e2e test
./test_temporal_e2e.sh
```

### Option 2: Hybrid (Infra in Docker, API/Workers Local)
```bash
# Start infrastructure only
docker compose up -d postgres temporal temporal-ui

# Run migrations
uv run alembic upgrade head

# Terminal 1: Start API
uv run uvicorn torale.api.main:app --reload

# Terminal 2: Start Workers
uv run python -m torale.workers

# Terminal 3: Run test
./test_temporal_e2e.sh
```

## What the Test Does

The `test_temporal_e2e.sh` script validates the complete workflow:

1. **Register** user account
2. **Login** and get JWT token
3. **Create** task with LLM executor
4. **Execute** task (triggers Temporal workflow)
5. **Poll** execution status until completion
6. **Verify** LLM result is returned
7. **Cleanup** task

**Expected output:**
```
=== Temporal E2E Test ===

1. Registering user...
✓ User registered
2. Logging in...
✓ Logged in (token: eyJhbGciOiJIUzI1NiIs...)
3. Creating task...
✓ Task created (ID: 8f3e4d2a-...)
4. Executing task (triggering Temporal workflow)...
✓ Execution started (ID: 1a2b3c4d-..., initial status: pending)
5. Polling for execution completion (max 60s)...
   [1s] Status: pending (waiting...)
   [2s] Status: running (waiting...)
   [8s] Status: success ✓
✓ Execution completed successfully!

=== Result ===
{
  "text": "Code tests running,\nBugs hiding in the shadows,\nSuccess blooms at last.",
  "model": "gemini-2.0-flash-exp",
  "usage": {...}
}

6. Cleaning up...
✓ Task deleted

=== All tests passed! ===
```

## Monitoring

### Temporal UI
Visit http://localhost:8080 to see:
- Workflow executions
- Activity logs
- Retry attempts
- Execution history

### Worker Logs
```bash
# If using Docker
docker compose logs -f workers

# If running locally
# See output in Terminal 2
```

### API Logs
```bash
# If using Docker
docker compose logs -f api

# If running locally
# See output in Terminal 1
```

## Debugging

### Workflow doesn't start
```bash
# Check Temporal is running
curl http://localhost:7233

# Check worker is connected
docker compose logs workers | grep "Starting Temporal worker"
```

### Execution stuck in pending
```bash
# Check worker logs for errors
docker compose logs workers

# Check Temporal UI for workflow status
open http://localhost:8080
```

### Execution fails
```bash
# Check execution history
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks/$TASK_ID/executions | jq
```

## Architecture

```
Test Script
    │
    ↓
API (FastAPI)
    │
    ├─→ Create execution record (DB)
    │
    └─→ Start workflow (Temporal Client)
            │
            ↓
        Temporal Server
            │
            ↓
        Worker (listening on queue)
            │
            ├─→ execute_task activity
            │   ├─→ Update status to "running"
            │   ├─→ Call LLMTextExecutor
            │   └─→ Update result/status
            │
            └─→ send_notification activity
                └─→ TODO: NotificationAPI
```

## Cleanup

```bash
# Stop all services
docker compose down

# Remove volumes
docker compose down -v
```
