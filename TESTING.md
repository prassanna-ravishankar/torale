# Testing Torale

## Quick Start

### 1. Start PostgreSQL
```bash
docker compose up -d postgres
```

### 2. Run Migrations
```bash
uv run alembic upgrade head
```

### 3. Start the API
```bash
uv run uvicorn torale.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run the Test Script
```bash
./test_torale.sh
```

## What the Test Script Does

The `test_torale.sh` script tests the complete Torale workflow:

1. **Health Check** - Verifies API is running
2. **User Registration** - Creates a new user account
3. **Authentication** - Logs in and gets JWT token
4. **Create Task** - Creates an AI-powered task
5. **List Tasks** - Retrieves all tasks for the user
6. **Get Task** - Fetches specific task details
7. **Execute Task** - Manually triggers task execution
8. **Execution History** - Views task execution logs
9. **Update Task** - Modifies task properties
10. **Delete Task** - Removes the task

## Manual Testing

### Using the API Docs

Open http://localhost:8000/docs in your browser for interactive API documentation.

### Using cURL

#### Register a User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "SecurePassword123!"
  }'
```

#### Login
```bash
curl -X POST "http://localhost:8000/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=SecurePassword123!"
```

Save the `access_token` from the response.

#### Create a Task
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Summary",
    "schedule": "0 9 * * *",
    "executor_type": "llm_text",
    "config": {
      "prompt": "Summarize today's tech news",
      "model": "gemini-2.0-flash-exp",
      "max_tokens": 200
    },
    "is_active": true
  }'
```

### Using the CLI

```bash
# Register
uv run torale auth register

# Login
uv run torale auth login

# Check status
uv run torale auth status

# Logout
uv run torale auth logout
```

## Running Tests with Pytest

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=torale

# Run specific test file
uv run pytest tests/test_gemini_integration.py

# Run standalone test scripts
uv run python tests/test_executors.py
```

## Docker Testing

### Run Everything in Docker
```bash
docker compose up -d
```

This starts:
- postgres (port 5432)
- api (port 8000)
- workers (background)
- temporal (port 7233)
- temporal-ui (port 8080)

### View Logs
```bash
docker compose logs -f api
docker compose logs -f workers
```

### Stop Everything
```bash
docker compose down
```

## Endpoints

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Temporal UI**: http://localhost:8080 (when running docker compose)

## Supported LLM Models

Configure API keys in `.env`:
- `OPENAI_API_KEY` - For GPT models (gpt-3.5-turbo, gpt-4, etc.)
- `ANTHROPIC_API_KEY` - For Claude models (claude-3-haiku-20240307, etc.)
- `GOOGLE_API_KEY` - For Gemini models (gemini-2.0-flash-exp, etc.)

## Troubleshooting

### Database Connection Issues
```bash
# Check postgres is running
docker ps | grep postgres

# Check connection
docker exec torale-postgres-1 pg_isready -U torale
```

### API Won't Start
```bash
# Check for port conflicts
lsof -i :8000

# View detailed logs
uv run uvicorn torale.api.main:app --log-level debug
```

### Migration Issues
```bash
# Check migration status
uv run alembic current

# Rollback last migration
uv run alembic downgrade -1

# Re-run migrations
uv run alembic upgrade head
```
