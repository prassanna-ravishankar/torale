# Testing Torale

Comprehensive guide for testing Torale's monitoring platform, covering unit tests, end-to-end workflows, and debugging.

## Quick Start

### Using Just Commands

```bash
# Run all tests
just test

# Run specific test types
just test-unit          # Unit tests with pytest
just test-e2e           # E2E Temporal workflow test
just test-schedule      # Scheduled execution test
just test-grounded      # Grounded search test
```

### Manual Test Execution

```bash
# Unit tests
cd backend && uv run --with pytest --with pytest-asyncio --with pytest-cov pytest

# E2E tests
./backend/scripts/test_temporal_e2e.sh
./backend/scripts/test_schedule.sh
./backend/scripts/test_grounded_search.sh
```

---

## Test Environment Setup

### Option 1: Full Docker Stack (Recommended)

Start all services in Docker:

```bash
# Start everything
just dev

# Or manually
docker compose up -d

# Wait for services to be ready (~30 seconds)
sleep 30

# Run tests
just test-e2e
```

### Option 2: Hybrid (Infrastructure in Docker, API/Workers Local)

Run infrastructure in Docker, but API and workers locally for faster iteration:

```bash
# Start infrastructure only
docker compose up -d postgres temporal temporal-ui

# Run migrations
cd backend && uv run alembic upgrade head

# Terminal 1: Start API
cd backend && uv run uvicorn torale.api.main:app --reload

# Terminal 2: Start Workers
cd backend && uv run python -m torale.workers

# Terminal 3: Run tests
./backend/scripts/test_temporal_e2e.sh
```

---

## Test Types

### Unit Tests

**Location**: `backend/tests/`

**Framework**: pytest with async support

**Run**:
```bash
just test-unit

# Or directly
cd backend && uv run pytest
```

**Coverage**:
```bash
cd backend && uv run pytest --cov=torale --cov-report=html
```

**What's tested**:
- Core executor logic
- Database models and operations
- API endpoint validation
- Temporal workflow logic

### E2E Temporal Workflow Test

**Script**: `backend/scripts/test_temporal_e2e.sh`

**What it tests**:
1. User authentication (Clerk)
2. Task creation via API
3. Manual task execution (triggers Temporal workflow)
4. Workflow execution and completion
5. Result verification
6. Cleanup

**Run**:
```bash
just test-e2e

# Or directly
./backend/scripts/test_temporal_e2e.sh
```

**Expected output**:
```
=== Temporal E2E Test ===

1. Registering user...
✓ User registered
2. Logging in...
✓ Logged in
3. Creating task...
✓ Task created (ID: 8f3e4d2a-...)
4. Executing task...
✓ Execution started (ID: 1a2b3c4d-...)
5. Polling for completion (max 60s)...
   [8s] Status: success ✓
✓ Execution completed successfully!

=== Result ===
{
  "answer": "...",
  "current_state": {...},
  "grounding_sources": [...]
}

6. Cleaning up...
✓ Task deleted

=== All tests passed! ===
```

### Scheduled Execution Test

**Script**: `backend/scripts/test_schedule.sh`

**What it tests**:
- Temporal cron schedule creation
- Automatic execution at scheduled time
- Schedule management (pause, resume, delete)

**Run**:
```bash
just test-schedule

# Or directly
./backend/scripts/test_schedule.sh
```

**Note**: This test creates a task with `* * * * *` (every minute) schedule and waits ~60 seconds for automatic execution.

### Grounded Search Test

**Script**: `backend/scripts/test_grounded_search.sh`

**What it tests**:
- Google Search via Gemini grounding
- LLM condition evaluation
- State extraction and comparison
- Grounding source attribution

**Run**:
```bash
just test-grounded

# Or directly
./backend/scripts/test_grounded_search.sh
```

**Requirements**:
- `GOOGLE_API_KEY` must be set in `.env`
- Internet connectivity for Google Search

---

## Monitoring & Debugging

### Temporal UI

**Access**: http://localhost:8080

**What you can see**:
- All workflow executions
- Activity logs and parameters
- Retry attempts and failures
- Execution history timeline
- Task queue status

**Useful for**:
- Understanding why a workflow failed
- Seeing actual parameters passed to activities
- Tracking retry behavior
- Debugging workflow logic

### Service Logs

**API logs**:
```bash
# Docker
just logs-api

# Or
docker compose logs -f api
```

**Worker logs**:
```bash
# Docker
just logs-workers

# Or
docker compose logs -f workers
```

**Temporal logs**:
```bash
just logs-temporal

# Or
docker compose logs -f temporal
```

**All logs**:
```bash
just logs
```

### Database Inspection

**Connect to PostgreSQL**:
```bash
# Via just
just psql

# Or directly
docker compose exec postgres psql -U torale -d torale
```

**Useful queries**:
```sql
-- List all tasks
SELECT id, name, is_active, created_at FROM tasks;

-- View recent executions
SELECT id, task_id, status, started_at, completed_at
FROM task_executions
ORDER BY started_at DESC
LIMIT 10;

-- Check notifications (condition_met = true)
SELECT id, task_id, condition_met, change_summary, started_at
FROM task_executions
WHERE condition_met = true
ORDER BY started_at DESC;

-- View task state
SELECT id, name, condition_met, last_known_state, last_notified_at
FROM tasks
WHERE is_active = true;
```

---

## Troubleshooting

### Workflow Doesn't Start

**Check Temporal is running**:
```bash
curl http://localhost:7233
```

**Check worker is connected**:
```bash
docker compose logs workers | grep "Starting Temporal worker"
```

**Check API can reach Temporal**:
```bash
docker compose logs api | grep -i temporal
```

### Execution Stuck in Pending

**Possible causes**:
1. Worker not running or crashed
2. Worker not listening on correct task queue
3. Temporal server issue

**Debug steps**:
```bash
# 1. Check worker status
docker compose ps workers

# 2. Check worker logs for errors
just logs-workers

# 3. Check Temporal UI
open http://localhost:8080
# Look for: workflow pending, no worker polling queue

# 4. Restart worker if needed
docker compose restart workers
```

### Execution Fails

**Check execution error**:
```bash
# Via API (requires auth token)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks/$TASK_ID/executions | jq

# Or check database
docker compose exec postgres psql -U torale -d torale \
  -c "SELECT error_message FROM task_executions WHERE status = 'failed' ORDER BY started_at DESC LIMIT 5;"
```

**Common failure reasons**:
- Missing API keys (GOOGLE_API_KEY, etc.)
- Network connectivity issues
- LLM API rate limits
- Invalid search query or condition

**Check worker logs for stack traces**:
```bash
just logs-workers | grep -A 20 "ERROR"
```

### API Authentication Issues

**Test JWT authentication**:
```bash
# Get token from login
curl -X POST http://localhost:8000/auth/sync-user \
  -H "Content-Type: application/json" \
  -d '{"clerk_user_id": "user_xxx", "email": "test@example.com"}'

# Use token
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks
```

**For local development without auth**:
```bash
export TORALE_NOAUTH=1
# Now API calls work without authentication
```

### Database Migration Issues

**Check current migration version**:
```bash
just migrate-status

# Or
docker compose exec api alembic current
```

**Reset database** (⚠️ destroys all data):
```bash
just reset

# Or manually
docker compose down -v
docker compose up -d postgres
sleep 2
docker compose exec api alembic upgrade head
```

**Create new migration after schema changes**:
```bash
just migrate-new "description of change"

# Or
docker compose exec api alembic revision --autogenerate -m "description"
```

### Temporal Connection Issues

**Verify connection**:
```bash
# From API container
docker compose exec api python -c "
from temporalio.client import Client
import asyncio
async def check():
    client = await Client.connect('temporal:7233')
    print('Connected!')
asyncio.run(check())
"
```

**Check environment variables**:
```bash
docker compose exec api env | grep TEMPORAL
docker compose exec workers env | grep TEMPORAL
```

### Grounded Search Test Fails

**Check API key**:
```bash
# Verify GOOGLE_API_KEY is set
grep GOOGLE_API_KEY .env
```

**Test Gemini API directly**:
```bash
cd backend && uv run python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content('Say hello')
print(response.text)
"
```

**Common issues**:
- Invalid or expired API key
- API quota exceeded
- Network/firewall blocking Google API
- Grounding not available in your region

---

## Test Data Cleanup

### Clean Up Test Tasks

```bash
# Via API (list and delete)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks | jq

curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/tasks/$TASK_ID
```

### Reset All Data

```bash
# Full reset (destroys all data)
just reset

# Or keep data, just restart services
just restart
```

---

## CI/CD Testing

### Running Tests in CI

```bash
# Install dependencies
cd backend && uv sync

# Start test infrastructure
docker compose up -d postgres temporal

# Wait for services
sleep 10

# Run migrations
uv run alembic upgrade head

# Run tests
uv run pytest

# Cleanup
docker compose down -v
```

### Test Coverage Requirements

- Minimum 80% coverage for core modules
- All executors must have unit tests
- Critical API endpoints must have integration tests
- At least one E2E test per major workflow

---

## Architecture Overview

### Test Flow Diagram

```
Test Script
    │
    ↓
API (FastAPI)
    │
    ├─→ Create execution record (PostgreSQL)
    │
    └─→ Start workflow (Temporal Client)
            │
            ↓
        Temporal Server
            │
            ↓
        Worker (listening on task queue)
            │
            ├─→ execute_task activity
            │   ├─→ Update status to "running"
            │   ├─→ Call GroundedSearchExecutor
            │   │   ├─→ Google Search (via Gemini)
            │   │   ├─→ LLM evaluation
            │   │   └─→ State comparison
            │   └─→ Update result/status
            │
            └─→ send_notification activity
                └─→ Create in-app notification
```

### Temporal vs Production

**Local Development**:
- Self-hosted Temporal via docker-compose
- Single-node setup
- Embedded PostgreSQL for Temporal state
- Temporal UI on http://localhost:8080

**Production (GKE)**:
- Temporal Cloud (managed service)
- High availability, multi-region
- No in-cluster Temporal deployment
- Connected via cloud endpoint

---

## Best Practices

### Writing New Tests

1. **Use pytest fixtures** for common setup
2. **Test one thing** per test function
3. **Use descriptive names**: `test_grounded_search_extracts_state_correctly`
4. **Clean up after tests** (delete test data)
5. **Mock external APIs** when appropriate (Gemini, etc.)

### Test Naming Conventions

```python
# Good
def test_task_creation_requires_search_query():
    ...

def test_executor_handles_api_timeout():
    ...

# Bad
def test1():
    ...

def test_stuff():
    ...
```

### Debugging Workflow Issues

1. **Start with logs**: Check worker logs first
2. **Use Temporal UI**: See actual execution history
3. **Check activity inputs**: Verify parameters passed to activities
4. **Test activities directly**: Import and call activity functions in isolation
5. **Enable debug logging**: Set `LOG_LEVEL=DEBUG` in `.env`

### Performance Testing

```bash
# Create multiple tasks and measure execution time
time ./backend/scripts/test_temporal_e2e.sh

# Monitor resource usage
docker stats
```

---

## Further Reading

- [Temporal Testing Guide](https://docs.temporal.io/develop/testing)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- Torale API docs: `backend/src/torale/api/`
- Temporal workflows: `backend/src/torale/workers/workflows.py`
