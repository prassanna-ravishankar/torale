<div align="center">
  <img src="./frontend/public/logo.svg" alt="τorale" width="120" height="120">
  <h1>τorale</h1>
  <p><strong>Grounded search monitoring platform for AI-powered conditional automation</strong></p>

  [![PyPI version](https://badge.fury.io/py/torale.svg)](https://badge.fury.io/py/torale)
  [![Deploy](https://github.com/prassanna-ravishankar/torale/actions/workflows/production.yml/badge.svg)](https://github.com/prassanna-ravishankar/torale/actions/workflows/production.yml)
  [![App](https://img.shields.io/badge/app-torale.ai-green)](https://torale.ai)
  [![Documentation](https://img.shields.io/badge/docs-torale.ai-blue)](https://docs.torale.ai)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

Monitor the web for specific conditions using Google Search + LLM analysis, then get notified when they're met.

## Use Cases

- **Product Launches**: "Tell me when the next iPhone release date is announced"
- **Availability Monitoring**: "Notify me when swimming pool memberships open for summer"
- **Stock Alerts**: "Alert me when PS5 is back in stock at Best Buy"
- **Event Tracking**: "Let me know when GPT-5 launch date is confirmed"
- **Price Monitoring**: "Tell me when iPhone 15 price drops below $500"

## Installation

```bash
pip install torale
```

Get started at **[torale.ai](https://torale.ai)** or see the [Quick Start](#quick-start) guide below.

## How It Works

1. **Create a monitoring task** with a search query and condition
2. **Agent searches the web** via Perplexity with cross-run memory (Mem0)
3. **Agent evaluates** if your condition is met based on search results
4. **You get notified** when condition triggers (once or always)

## Quick Start

### Option 1: Use the Hosted Service (Recommended)

The fastest way to get started is using the hosted service at **[torale.ai](https://torale.ai)**:

1. **Sign up** at https://torale.ai (Google/GitHub OAuth or email)
2. **Create monitoring tasks** via the web dashboard
3. **Get notified** when conditions are met

### Option 2: Install the CLI

Install the Torale CLI to manage tasks from your terminal:

```bash
pip install torale
```

**Configure authentication:**

```bash
# Generate an API key at https://torale.ai (or your self-hosted instance)
torale auth set-api-key

# Create your first monitoring task
torale task create "iPhone Release Monitor" \
  --schedule "0 9 * * *" \
  --prompt "Search for iPhone release date announcements"

# List all tasks
torale task list

# View task notifications
torale notifications TASK_ID
```

### Option 3: Use the Python SDK

Integrate Torale into your Python applications for programmatic task management.

#### Installation

```bash
pip install torale
```

#### Authentication

The SDK requires developer access. To get an API key:

1. Sign up at https://torale.ai
2. Contact support to request developer access (adds `role: "developer"` to your account)
3. Go to Settings → API Access and generate an API key
4. Configure the SDK with your API key

#### Quick Start - Synchronous Client

```python
from torale import Torale

# Option 1: Environment variable (recommended for development)
# export TORALE_API_KEY=sk_...
client = Torale()  # Auto-discovers from environment

# Option 2: Explicit API key (useful for testing, not recommended for production)
client = Torale(api_key="sk_your_api_key_here")

# Option 3: CLI config file (recommended for local CLI usage)
# Run: torale auth set-api-key
# Stores in: ~/.torale/config.json
client = Torale()  # Auto-discovers from config file

# Create a monitoring task
task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the next iPhone being released?",
    condition_description="A specific release date has been announced",
    schedule="0 9 * * *",  # Daily at 9am
    notify_behavior="once",  # Options: "once", "always", "track_state"
    notifications=[
        {"type": "webhook", "url": "https://myapp.com/alert"}
    ]
)

print(f"Created task: {task.id}")
```

#### Async Client

For better performance with concurrent operations:

```python
import asyncio
from torale import ToraleAsync

async def main():
    async with ToraleAsync(api_key="sk_...") as client:
        # Create multiple tasks concurrently
        task1 = client.tasks.create(
            name="iPhone Monitor",
            search_query="When is iPhone 16 being released?",
            condition_description="A specific date is announced"
        )
        task2 = client.tasks.create(
            name="PS5 Stock Monitor",
            search_query="Is PS5 in stock at Best Buy?",
            condition_description="PS5 is available for purchase"
        )

        # Wait for both to complete
        tasks = await asyncio.gather(task1, task2)
        print(f"Created {len(tasks)} tasks")

asyncio.run(main())
```

#### API Reference

**Task Management**

```python
# List all tasks
tasks = client.tasks.list(active=True)

# Get specific task
task = client.tasks.get(task_id="550e8400-...")

# Update task
task = client.tasks.update(
    task_id="550e8400-...",
    name="New Name",
    state="paused"  # "active", "paused", or "completed"
)

# Delete task
client.tasks.delete(task_id="550e8400-...")

# Manual execution (test run)
execution = client.tasks.execute(task_id="550e8400-...")
print(execution.status)  # "pending", "running", "success", "failed"
```

**Preview Queries**

Test search queries before creating tasks:

```python
# Preview with explicit condition
result = client.tasks.preview(
    search_query="When is iPhone 16 being released?",
    condition_description="A specific release date is announced"
)

# Preview without condition (LLM will infer)
result = client.tasks.preview(
    search_query="What's the latest news on GPT-5?"
)

print(result["answer"])
print(f"Condition met: {result['condition_met']}")
if "inferred_condition" in result:
    print(f"Inferred: {result['inferred_condition']}")

for source in result["grounding_sources"]:
    print(f"- {source['title']}: {source['url']}")
```

**Execution History & Notifications**

```python
# Get all executions
executions = client.tasks.executions(task_id="550e8400-...", limit=100)
for exec in executions:
    print(f"{exec.started_at}: {exec.status}")

# Get only notifications (condition met)
notifications = client.tasks.notifications(task_id="550e8400-...", limit=10)
for notif in notifications:
    print(f"{notif.started_at}: {notif.notification}")
```

**Fluent Builder API**

For a more expressive syntax:

```python
from torale import monitor

task = (monitor("When is iPhone 16 being released?")
    .when("A specific release date is announced")
    .check_every("6 hours")  # Human-readable schedules
    .notify(webhook="https://myapp.com/alert")
    .named("iPhone Release Monitor")
    .create())
```

**Notification Configuration**

```python
# Webhook notifications
task = client.tasks.create(
    name="Bitcoin Alert",
    search_query="Bitcoin price USD",
    condition_description="Price exceeds $50,000",
    notifications=[
        {"type": "webhook", "url": "https://myapp.com/webhook"}
    ]
)

# Email notifications (requires verified email)
task = client.tasks.create(
    name="Job Alert",
    search_query="Software Engineer jobs in NYC",
    condition_description="New positions posted",
    notifications=[
        {"type": "email", "address": "you@example.com"}
    ]
)

# Multiple notification channels
task = client.tasks.create(
    name="Multi-channel Alert",
    search_query="Product launch announcement",
    condition_description="Official announcement is made",
    notifications=[
        {"type": "email", "address": "you@example.com"},
        {"type": "webhook", "url": "https://myapp.com/webhook"}
    ]
)
```

**Environment Configuration**

```bash
# Production (default)
export TORALE_API_KEY=sk_your_api_key_here

# Local development with authentication
export TORALE_API_KEY=sk_local_key
export TORALE_DEV=1  # Uses http://localhost:8000

# Local development without authentication
export TORALE_NOAUTH=1  # Skips auth, uses localhost

# Custom API URL
export TORALE_API_URL=https://custom.domain.com
```

**Context Managers**

Both sync and async clients support context managers for automatic cleanup:

```python
# Synchronous
with Torale() as client:
    tasks = client.tasks.list()

# Asynchronous
async with ToraleAsync() as client:
    tasks = await client.tasks.list()
```

**Error Handling**

```python
from torale.sdk.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    APIError
)

try:
    task = client.tasks.create(...)
except AuthenticationError:
    print("Invalid API key or not authenticated")
except ValidationError as e:
    print(f"Invalid input: {e}")
except NotFoundError:
    print("Resource not found")
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

### Option 4: Self-Hosted Setup

Run Torale on your own infrastructure:

#### 1. Install Dependencies
```bash
pip install uv
uv sync
```

#### 2. Set up Environment
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
- **Gemini**: API key for the monitoring agent (required)
- **Perplexity**: API key for agent search (required)
- **Mem0**: API key for agent cross-run memory (required)
- **Database**: PostgreSQL connection string (local default works)
- **Secret Key**: Generate with `openssl rand -hex 32`

#### 3. Start Services
```bash
# Start all services (PostgreSQL + API)
docker compose up -d

# Check status
docker compose ps
```

#### 4. Access the Web Interface
```bash
# Start frontend
cd frontend && npm run dev

# Navigate to http://localhost:3000
# Sign in with Clerk (Google/GitHub OAuth or email/password)
# Create tasks via the dashboard UI
```

#### 5. Or use the API directly
```bash
# Use your API key from the web dashboard
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer sk_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone Release Monitor",
    "schedule": "0 9 * * *",
    "search_query": "When is the next iPhone being released?",
    "condition_description": "A specific release date has been announced",
    "notify_behavior": "once"
  }'
```

## Frontend

The Torale frontend is a React + TypeScript application built with Vite.

### Setup
```bash
# Install frontend dependencies
cd frontend && npm install

# Create frontend environment file
cat > frontend/.env << EOF
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
VITE_API_BASE_URL=http://localhost:8000
EOF

# Start development server
npm run dev
```

### Features
- **Authentication**: Clerk (Google/GitHub OAuth + email/password)
- **Dashboard**: View and manage all monitoring tasks
- **Task Creation**: Create new monitoring tasks with search queries and conditions
- **Task Details**: View execution history, notifications, and state changes
- **API Key Management**: Generate API keys for CLI access
- **Real-time Updates**: Auto-refresh execution status
- **Toast Notifications**: User feedback for all actions

### Tech Stack
- React 18 + TypeScript
- Vite (build tool)
- Clerk (authentication)
- React Router (routing)
- Tailwind CSS (styling)
- shadcn/ui (component library)
- Sonner (toast notifications)

Access the frontend at http://localhost:3000 after starting the dev server.

## Architecture

### Local Development
- **API**: FastAPI with Clerk authentication + API keys
- **Database**: PostgreSQL 16 via Docker Compose
- **Scheduler**: APScheduler with PostgreSQL job store
- **Agent**: Gemini-powered monitoring agent via Pydantic AI (Perplexity search + Mem0 memory)
- **CLI**: Python typer with API key authentication

### Production (GKE)
- **Infrastructure**: GKE Autopilot (clusterkit) in us-central1
- **Database**: Cloud SQL PostgreSQL 16 (managed, zonal)
- **Orchestration**: APScheduler + GitHub Actions CI/CD
- **Cost**: Spot pods (60-91% savings), zonal Cloud SQL
- **Domains**: api.torale.ai (API), torale.ai (Frontend)

## Features

### ✅ Implemented
- Agent-powered search monitoring (Gemini + Perplexity + Mem0)
- Intelligent condition evaluation with grounded sources
- APScheduler with agent-driven dynamic scheduling
- User-configurable notify behavior:
  - `once`: Notify once, then auto-disable
  - `always`: Notify every time condition is met
- In-app notifications endpoint
- Task templates for common use cases
- Clerk authentication (OAuth + email/password)
- API key authentication for CLI
- CLI for task management
- Frontend dashboard with task management
- GKE deployment with cost optimization
- **Live Search Preview** - Test queries before creating tasks
- **Immediate Task Execution** - Run monitoring tasks instantly after creation
- **AI-Powered Task Creation** - "Magic Input" uses LLM to generate task configuration from natural language
- **Context-Aware Task Refinement** - "Magic Refine" updates existing tasks while preserving context
- **Simplified Task Creation UX** - 3 fields + a toggle

### 📋 Future Roadmap
- **Shareable Tasks**: Share monitoring tasks with rich OpenGraph previews
- External notifications (email/SMS/Slack via webhooks)
- Browser automation for dynamic sites
- Price tracking with charts
- Multi-step conditional workflows
- Template marketplace
- Team/organization support
- Natural language schedule input ("every weekday at 9am")
- Timezone selection and display
- Advanced scheduling (date ranges, skip holidays)

## Known Issues

### Frontend
- **Alert Component Layout**: The info panel in the task creation dialog has alignment issues with the icon and text. The shadcn/ui Alert component's grid layout may need adjustment for proper spacing.

## Research

Systematic evaluation framework for comparing grounded search approaches. See [`backend/research/`](backend/research/) for details.

**Results**: Perplexity achieves 80% accuracy at ~800 tokens (~9s), outperforming Gemini (60%/~750 tokens/~3.4s) and OpenAI (70%/~14,500 tokens/~28s).

## Testing

Torale has comprehensive unit, integration, and E2E tests covering the agent pipeline, scheduler, and API.

### Unit Tests

Run pytest tests without requiring services:

```bash
just test               # Run backend unit tests
just test-cov           # Run with coverage report
just lint               # Run ruff linting
```

### Integration Tests

Integration tests require running services (PostgreSQL, API) and support two authentication modes:

**Option 1: No-Auth Mode (Recommended for Development)**

```bash
# Start services with no-auth mode
just dev-noauth

# Run integration tests
TORALE_NOAUTH=1 just test-integration
```

This automatically creates a test user and bypasses Clerk authentication for testing.

**Option 2: Clerk Authentication (Production-like)**

```bash
# Start services normally
just dev-bg

# Get a Clerk session token:
# 1. Login at http://localhost:3000
# 2. Open browser dev tools (F12)
# 3. Go to Application/Storage → Cookies
# 4. Copy the __session cookie value

# Run tests with Clerk token
export CLERK_TEST_TOKEN='your-clerk-session-token'
just test-integration
```

See [docs-site/contributing/testing.md](https://docs.torale.ai/contributing/testing) for detailed testing guide, including debugging workflows and troubleshooting.

## Deployment

### Local Development
```bash
just dev         # Start all services via docker-compose
just dev-frontend # Start frontend dev server
just dev-full    # Start everything
just dev-noauth  # Start everything in no-auth mode
```

### CI/CD (Recommended)

Torale uses **GitHub Actions** for automated CI/CD with production and branch deployments.

**Setup (one-time with keyless auth):**
```bash
./scripts/setup-github-wif.sh
```

Then add 3 GitHub secrets (outputted by script):
- `GCP_PROJECT_ID`
- `GCP_SERVICE_ACCOUNT`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`

See [CI/CD Setup](https://docs.torale.ai/deployment/ci-cd) for detailed setup.

**Automatic deployments:**
- **Push to `main`** → Production deployment (`torale` namespace)
- **Push to `feat/**`, `fix/**`** → Branch deployment (`torale-{branch}` namespace)
- **Pull Request** → Build and scan only (no deployment)

**Branch management:**
```bash
just list-branches              # List all branch deployments
just cleanup-branch feat-auth   # Delete specific branch
just cleanup-old-branches       # Delete branches >7 days old
```

**Workflows:**
- `.github/workflows/production.yml` - Production deployment
- `.github/workflows/branch.yml` - Branch deployments
- `.github/workflows/pr.yml` - PR checks
- `.github/workflows/build.yml` - Reusable build/scan job

**Features:**
- ✅ Parallel Docker builds (3x matrix jobs)
- ✅ Security scanning with Trivy
- ✅ Automated Helmfile deployment to GKE
- ✅ Health checks and rollout verification
- ✅ Isolated branch test environments

### Production (GKE ClusterKit)

**Prerequisites:** gcloud CLI, kubectl, helm, helmfile

```bash
# One-time setup
just k8s-auth       # Get cluster credentials
just k8s-setup      # Create Cloud SQL + IAM
just k8s-secrets    # Create K8s secrets from .env

# Manual deploy (if not using CI/CD)
just k8s-deploy-all # Deploy Torale

# Manage
just k8s-status     # Check deployment status
just k8s-logs-api   # View API logs
```

**Access:**
- Frontend: https://torale.ai
- API: https://api.torale.ai
See [Kubernetes Deployment](https://docs.torale.ai/deployment/kubernetes) for detailed guide.

## How Grounded Search Works

1. **Task Created**: User defines search query + condition to monitor
2. **Scheduled Execution**: APScheduler triggers task based on cron schedule
3. **Agent Search**: Agent searches via Perplexity, uses Mem0 for cross-run memory
4. **Condition Evaluation**: Agent evaluates if condition is met, returns evidence + sources
5. **Notification**: If condition met → notifies via email/webhook
6. **Auto-disable** (optional): If `notify_behavior = "once"`, task deactivates after first alert
7. **Dynamic Reschedule**: Agent returns `next_run` to adjust check frequency

## Configuration

### Notify Behaviors

- **`once`**: Alert once when condition is first met, then auto-disable task
- **`always`**: Alert every time condition is met (use with caution)

### Schedule Formats

Use standard cron expressions:
- `* * * * *`: Every minute (testing only)
- `0 * * * *`: Every hour
- `0 9 * * *`: Every day at 9 AM
- `0 9 * * 1`: Every Monday at 9 AM
- `0 9 1 * *`: First day of every month at 9 AM

## API Endpoints

### Authentication
```
POST   /auth/sync-user                     # Sync Clerk user to database (auto-called)
GET    /auth/me                            # Get current user info
POST   /auth/api-keys                      # Generate API key for CLI
GET    /auth/api-keys                      # List user's API keys
DELETE /auth/api-keys/{id}                 # Revoke API key
```

### Tasks
```
POST   /api/v1/tasks/suggest               # AI-powered task suggestion from natural language (context-aware)
POST   /api/v1/tasks/preview               # Preview search query (test without creating task)
POST   /api/v1/tasks                       # Create monitoring task
GET    /api/v1/tasks                       # List tasks
GET    /api/v1/tasks/{id}                  # Get task details
PUT    /api/v1/tasks/{id}                  # Update task
DELETE /api/v1/tasks/{id}                  # Delete task + schedule
POST   /api/v1/tasks/{id}/execute          # Manual execution (testing)
GET    /api/v1/tasks/{id}/executions       # Full execution history
GET    /api/v1/tasks/{id}/notifications    # Filtered: condition_met = true
```

## CLI Commands

```bash
# Authentication
torale auth set-api-key                    # Configure API key
torale auth status                         # Check auth status
torale auth logout                         # Remove credentials

# Tasks
torale task create NAME --schedule CRON --prompt PROMPT
torale task list [--active]
torale task get TASK_ID
torale task update TASK_ID [--name NAME] [--schedule CRON] [--active/--inactive]
torale task delete TASK_ID [--yes]
torale task execute TASK_ID               # Manual execution
torale task logs TASK_ID [--limit N]      # View execution logs

# Development mode (no auth required)
export TORALE_NOAUTH=1
torale task list
```

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://torale:torale@localhost:5432/torale

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...              # Backend: Verify Clerk tokens
CLERK_PUBLISHABLE_KEY=pk_test_...         # Backend: Initialize Clerk client

# Agent
AGENT_URL=http://localhost:8000

# AI (required for monitoring agent)
GEMINI_API_KEY=your-gemini-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key
MEM0_API_KEY=your-mem0-api-key

# Development/Testing (optional)
TORALE_NOAUTH=1                            # Disable auth for local testing (DO NOT USE IN PRODUCTION)
```

### Frontend (frontend/.env)
```bash
# Clerk
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...    # Frontend: Initialize ClerkProvider
VITE_API_BASE_URL=http://localhost:8000   # Frontend: API endpoint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT
