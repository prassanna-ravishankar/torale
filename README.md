# Torale

**Grounded search monitoring platform** for AI-powered conditional automation.

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
2. **Torale runs scheduled searches** via Google Search (grounded via Gemini)
3. **LLM evaluates** if your condition is met based on search results
4. **You get notified** when condition triggers (once, always, or on state change)

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

Integrate Torale into your Python applications:

```bash
pip install torale
```

```python
from torale.sdk import ToraleClient

# Initialize client with your API key
client = ToraleClient(
    api_key="sk_your_api_key_here",
    base_url="https://api.torale.ai"  # or http://localhost:8000 for self-hosted
)

# Create a monitoring task
task = client.tasks.create(
    name="iPhone Release Monitor",
    schedule="0 9 * * *",
    executor_type="llm_grounded_search",
    search_query="When is the next iPhone being released?",
    condition_description="A specific release date has been announced",
    notify_behavior="once",
    config={"model": "gemini-2.0-flash-exp"}
)

# Get task status
task = client.tasks.get(task.id)
print(f"Task status: {task.is_active}")

# List all notifications
notifications = client.tasks.get_notifications(task.id)
for notification in notifications:
    print(f"[{notification.created_at}] {notification.message}")
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
- **Google AI**: Get key from https://aistudio.google.com/app/apikey (required)
- **Database**: PostgreSQL connection string (local default works)
- **Secret Key**: Generate with `openssl rand -hex 32`

#### 3. Start Services
```bash
# Start all services (PostgreSQL + Temporal + API + Workers)
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
    "executor_type": "llm_grounded_search",
    "search_query": "When is the next iPhone being released?",
    "condition_description": "A specific release date has been announced",
    "notify_behavior": "once",
    "config": {
      "model": "gemini-2.0-flash-exp"
    }
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
- **Workers**: Temporal workflows (self-hosted via Docker Compose)
- **Executor**: Grounded search + LLM condition evaluation
- **Scheduler**: Temporal cron schedules
- **Search**: Google Search via Gemini grounding
- **CLI**: Python typer with API key authentication

### Production (GKE)
- **Infrastructure**: GKE Autopilot (clusterkit) in us-central1
- **Database**: Cloud SQL PostgreSQL 16 (managed, zonal)
- **Orchestration**: Temporal Cloud + GitHub Actions CI/CD
- **Cost**: Spot pods (60-91% savings), zonal Cloud SQL
- **Domains**: api.torale.ai (API), torale.ai (Frontend)

## Features

### ✅ Implemented
- Grounded search monitoring via Google Search
- Intelligent condition evaluation (LLM-based)
- Automatic scheduled execution (cron)
- State tracking (no duplicate alerts)
- User-configurable notify behavior:
  - `once`: Notify once, then auto-disable
  - `always`: Notify every time condition is met
  - `track_state`: Notify only when state changes
- In-app notifications endpoint
- Task templates for common use cases
- Clerk authentication (OAuth + email/password)
- API key authentication for CLI
- CLI for task management
- Temporal Cloud integration (production)
- Frontend dashboard with task management
- GKE deployment with cost optimization

### 🚧 In Progress
- Enhanced grounding source display
- Historical state comparison UI
- External notifications (email/SMS)

### 📋 Future Roadmap
- **Shareable Tasks**: Share monitoring tasks with rich OpenGraph previews
- External notifications (email/SMS via NotificationAPI)
- Browser automation for dynamic sites
- Price tracking with charts
- Multi-step conditional workflows
- Template marketplace
- Team/organization support

## Known Issues

### Frontend
- **Alert Component Layout**: The info panel in the task creation dialog has alignment issues with the icon and text. The shadcn/ui Alert component's grid layout may need adjustment for proper spacing.

## Research

Systematic evaluation framework for comparing grounded search approaches. See [`backend/research/`](backend/research/) for details.

**Results**: Perplexity achieves 80% accuracy at ~800 tokens (~9s), outperforming Gemini (60%/~750 tokens/~3.4s) and OpenAI (70%/~14,500 tokens/~28s).

## Testing

Torale has comprehensive unit, integration, and E2E tests covering Temporal workflows, grounded search, and scheduled execution.

### Unit Tests

Run pytest tests without requiring services:

```bash
just test               # Run backend unit tests
just test-cov           # Run with coverage report
just lint               # Run ruff linting
```

### E2E Integration Tests

E2E tests require running services (PostgreSQL, Temporal, API, Workers) and support two authentication modes:

**Option 1: No-Auth Mode (Recommended for Development)**

```bash
# Start services with no-auth mode
TORALE_NOAUTH=1 just dev-bg

# Run all E2E tests
TORALE_NOAUTH=1 just test-e2e
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
just test-e2e
```

**Available E2E Tests:**
- `test_temporal_e2e.sh` - Tests Temporal workflow execution
- `test_schedule.sh` - Tests automatic scheduled task execution
- `test_grounded_search.sh` - Tests grounded search monitoring functionality

See [docs/TESTING.md](docs/TESTING.md) for detailed testing guide, including debugging workflows and troubleshooting.

## Deployment

### Local Development
```bash
just dev        # Start all services via docker-compose
just dev-all    # Include frontend dev server
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

See [docs/CI-CD.md](docs/CI-CD.md) for detailed setup.

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
just k8s-deploy-all # Deploy Temporal + Torale

# Manage
just k8s-status     # Check deployment status
just k8s-logs-api   # View API logs
just k8s-logs-workers # View worker logs
```

**Access:**
- Frontend: https://torale.ai
- API: https://api.torale.ai
- Temporal UI: `just k8s-port-forward-temporal` → http://localhost:8080

See [docs/k8s-deployment.md](docs/k8s-deployment.md) for detailed guide.

## How Grounded Search Works

1. **Task Created**: User defines search query + condition to monitor
2. **Scheduled Execution**: Temporal triggers task based on cron schedule
3. **Grounded Search**: Gemini performs Google Search with grounding
4. **LLM Evaluation**: LLM analyzes search results and evaluates condition
5. **State Comparison**: Compares with `last_known_state` to detect changes
6. **Notification**: If condition met (and not already notified), creates in-app notification
7. **Auto-disable** (optional): If `notify_behavior = "once"`, task deactivates after first alert

## Configuration

### Notify Behaviors

- **`once`**: Alert once when condition is first met, then auto-disable task
- **`always`**: Alert every time condition is met (use with caution)
- **`track_state`**: Alert only when underlying state changes (smart deduplication)

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

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# AI (Gemini required for grounded search)
GOOGLE_API_KEY=your-gemini-api-key

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
