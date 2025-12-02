# CLAUDE.md - Torale Project Context

## Project Overview
Torale is a **grounded search monitoring platform** for AI-powered conditional automation. Users create monitoring tasks that watch for specific conditions using Google Search + LLM analysis, then notify when conditions are met.

**Use Cases:**
- "Tell me when the next iPhone release date is announced"
- "Notify me when swimming pool memberships open for summer"
- "Alert me when PS5 is back in stock at Best Buy"
- "Let me know when GPT-5 launch date is confirmed"

**Domain**: torale.ai
**Current Status**: MVP implementation (grounded search monitoring)
**MVP Goal**: Automated web monitoring with intelligent condition evaluation
**Future Vision**: Full IFTTT-style platform with multi-step workflows and external integrations

## Architecture

### Tech Stack
- **Backend**: Python FastAPI
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: Cloud SQL PostgreSQL 16 (managed)
- **Authentication**: Clerk (OAuth + Email/Password with Google & GitHub)
- **Scheduling**: Temporal Cloud (production), self-hosted (local dev)
- **Infrastructure**: GKE Autopilot (clusterkit) + GitHub Actions + Helm
- **AI**: Google Gemini with grounded search (primary), OpenAI/Anthropic (fallback)
- **Search**: Google Search API via Gemini grounding
- **Notifications**: In-app (database-stored), future: NotificationAPI
- **CLI**: Python typer with API key authentication
- **Package Management**: UV (backend), npm (frontend)
- **Local Development**: Docker Compose (PostgreSQL + self-hosted Temporal + API + Workers)

### System Design
```
User ──► Frontend (torale.ai)
              ↓
         API (api.torale.ai) ──► Cloud SQL PostgreSQL
              ↓                   (Auth + DB + State)
         Temporal Cloud
              ↓
         Workers (GKE) ──► Gemini + Google Search
              └──► In-app Notifications
                   State comparison & condition evaluation
```

### Core Components
1. **API Service**: FastAPI app handling task CRUD operations and notifications endpoint
2. **Workers**: Temporal workers executing scheduled monitoring tasks
3. **Executors**: Grounded search executor with condition evaluation
4. **CLI**: Command-line interface for creating and managing monitoring tasks
5. **State Tracker**: Compares current search results with historical state to detect changes

### Frontend Runtime Configuration
The frontend uses `window.CONFIG` for environment-agnostic Docker images:

- **Local Dev**: `frontend/public/config.js` (git-tracked) sets `window.CONFIG` with `undefined` values → components fall back to `.env` files
- **Production**: Kubernetes ConfigMap mounts `config.js` with real values → components use production settings
- **Pattern**: `window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL`
- **Benefit**: Same Docker image deploys to any environment; config injected at runtime via ConfigMap

## Deployment Architecture

### Production (GKE)
- **Cluster**: GKE Autopilot (clusterkit) in us-central1
- **Namespace**: torale
- **Cost Optimization**: Spot pods (60-91% savings), zonal Cloud SQL
- **Database**: Cloud SQL PostgreSQL 16 (managed, private IP)
- **Orchestration**: Helm + Helmfile (default environment)
- **Temporal**: Temporal Cloud (us-central1.gcp.api.temporal.io:7233)
  - Namespace: quickstart-baldmaninc.g5zzo
  - Task Queue: torale-tasks
- **CI/CD**: GitHub Actions with Workload Identity Federation (keyless auth)
- **Ingress**: GCE Load Balancer + GKE Managed Certificates (auto SSL)
- **Domains**: api.torale.ai (API), torale.ai (Frontend)

### Staging (GKE)
- **Cluster**: Same GKE cluster (clusterkit)
- **Namespace**: torale-staging
- **Database**: Shares Cloud SQL with production (same torale database)
- **Authentication**: Shares production Clerk app (subdomain auto-allowed, no Clerk config needed)
- **Orchestration**: Helm + Helmfile (`-e staging`)
- **Temporal**: Same Temporal Cloud namespace
  - Task Queue: torale-staging (isolated from production)
- **CI/CD**: GitHub Actions (`staging.yml`) - triggered by `deploy` label on PR or manual dispatch
  - Does NOT auto-trigger on push; re-add label or use workflow_dispatch to redeploy
- **Lifecycle**: Staging persists indefinitely; redeploys update it, no auto-teardown
- **Ingress**: Separate GCE Load Balancer + GKE Managed Certificate
- **Domains**: api.staging.torale.ai (API), staging.torale.ai (Frontend)

### Components
1. **API Deployment**: FastAPI with Cloud SQL Proxy sidecar + init container for migrations
2. **Worker Deployment**: Temporal workers with Cloud SQL Proxy sidecar
3. **Frontend Deployment**: nginx serving React SPA (multi-stage Docker build)
4. **HPA**: Auto-scale API/Workers based on CPU (min 2, max 10 replicas)

### Local Development
- **Database**: PostgreSQL 16 via Docker Compose
- **Temporal**: Self-hosted via Docker Compose (matches production workflows)
- **Services**: API + Workers running locally via `just dev`

## Project Structure
```
torale/
├── backend/               # Backend services
│   ├── src/torale/
│   │   ├── api/          # FastAPI app
│   │   ├── workers/      # Temporal workers
│   │   ├── executors/    # Task executors
│   │   ├── cli/          # CLI commands
│   │   └── core/         # Shared utilities
│   ├── alembic/          # Database migrations
│   ├── tests/            # Unit/integration tests
│   ├── scripts/          # Test & utility scripts
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/             # React + TypeScript + Vite
│   ├── src/              # React components
│   ├── Dockerfile        # Multi-stage build
│   └── nginx.conf        # nginx config
├── helm/                 # Kubernetes Helm charts
│   └── torale/          # Main app chart
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── scripts/              # Setup and management scripts
│   ├── k8s-setup-cloudsql.sh
│   ├── k8s-create-secrets.sh
│   └── k8s-check-status.sh
├── docs-site/            # Public-facing documentation (VitePress)
│   ├── index.md          # Documentation home
│   ├── deployment/       # Deployment guides (CI/CD, K8s, etc.)
│   ├── contributing/     # Contributing guides (testing, etc.)
│   └── .vitepress/       # VitePress configuration
├── helmfile.yaml.gotmpl  # Multi-chart orchestration with environments
├── justfile              # Task runner (just dev, just test, etc.)
├── docker-compose.yml    # Local development
├── .github/workflows/    # GitHub Actions CI/CD
├── .env / .env.example
├── CLAUDE.md
└── README.md
```

## Database Schema
```sql
-- Clerk-authenticated users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- API keys for CLI authentication
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  key_prefix TEXT NOT NULL,  -- Display prefix like "sk_...abc123"
  key_hash TEXT NOT NULL UNIQUE,  -- SHA256 hash of actual key
  name TEXT NOT NULL,  -- User-defined name like "CLI Key"
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMP WITH TIME ZONE,
  is_active BOOLEAN NOT NULL DEFAULT true
);

-- Monitoring tasks
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  schedule TEXT NOT NULL, -- cron expression
  executor_type TEXT NOT NULL DEFAULT 'llm_grounded_search',
  config JSONB NOT NULL,
  is_active BOOLEAN DEFAULT true,

  -- Grounded search monitoring fields
  search_query TEXT,  -- "When is next iPhone release?"
  condition_description TEXT,  -- "A specific date has been announced"
  notify_behavior TEXT DEFAULT 'once',  -- 'once', 'always', 'track_state'
  condition_met BOOLEAN DEFAULT false,
  last_known_state JSONB,  -- Previous search results for comparison
  last_notified_at TIMESTAMP WITH TIME ZONE,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE task_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES tasks(id),
  status TEXT NOT NULL, -- 'pending', 'running', 'success', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  result JSONB,
  error_message TEXT,

  -- Grounded search execution fields
  condition_met BOOLEAN,  -- Was trigger condition met?
  change_summary TEXT,  -- What changed from last execution?
  grounding_sources JSONB,  -- Array of source URLs with metadata

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pre-built task templates
CREATE TABLE task_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,  -- 'product_release', 'price_tracking', 'availability', etc.
  icon TEXT,  -- Emoji or icon identifier
  search_query TEXT NOT NULL,  -- Template with placeholders like {product}
  condition_description TEXT NOT NULL,  -- Template for condition description
  schedule TEXT NOT NULL DEFAULT '0 9 * * *',  -- Default cron schedule
  notify_behavior TEXT NOT NULL DEFAULT 'once',
  config JSONB DEFAULT '{"model": "gemini-2.0-flash-exp"}',  -- Default executor config
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CHECK (notify_behavior IN ('once', 'always', 'track_state'))
);
```

## Executor Architecture

### Key Design Principle
The executor system uses grounded search to monitor web information and evaluate conditions. The MVP uses `llm_grounded_search` executor which combines Google Search with Gemini's LLM to intelligently detect when monitored conditions are met.

### Executor Interface
```python
class TaskExecutor(ABC):
    @abstractmethod
    async def execute(self, config: dict) -> dict:
        """
        Execute task and return results with grounding sources
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        """
        Validate task configuration
        """
        pass
```

### Grounded Search Executor
The `GroundedSearchExecutor` performs:
1. **Grounded Search**: Queries Google Search via Gemini's grounding feature with temporal context
2. **Answer Extraction**: LLM synthesizes answer from search results (concise 2-4 sentences for email)
3. **Condition Evaluation**: LLM determines if trigger condition is met
4. **State Comparison**: Compares with `last_known_state` to detect meaningful changes
5. **Source Attribution**: Extracts and stores grounding citations (with filtering of Vertex AI infrastructure URLs)
6. **Temporal Awareness**: Provides LLM with last execution time to improve change detection and reduce noise

### Task Configuration Format
```json
{
  "name": "iPhone Release Monitor",
  "schedule": "0 9 * * *",
  "executor_type": "llm_grounded_search",
  "search_query": "When is the next iPhone being released?",
  "condition_description": "A specific release date or month has been officially announced",
  "notify_behavior": "once",
  "config": {
    "model": "gemini-2.0-flash-exp",
    "search_provider": "google"
  }
}
```

## Authentication Architecture

### Clerk Integration
Torale uses **Clerk** for authentication, providing OAuth (Google, GitHub) and email/password login with a pre-built UI and secure session management.

#### Backend Authentication
- **Session Verification**: `clerk_auth.py` verifies Clerk JWT tokens on every API request
- **User Sync**: `/auth/sync-user` endpoint creates/updates local user records on first login
- **User Model**: Simplified to store only `clerk_user_id` and `email` (no passwords)
- **API Key Auth**: Separate authentication system for CLI access via hashed API keys

#### Frontend Authentication
- **Dual-Mode Authentication**: Supports both Clerk (production) and NoAuth (local dev with `VITE_TORALE_NOAUTH=1`)
- **ClerkProvider**: Wraps entire app in `main.tsx` with publishable key (production only)
- **Sign In/Up**: Clerk's pre-built `<SignIn />` and `<SignUp />` components at `/sign-in` and `/sign-up`
- **Protected Routes**: Use abstracted `useAuth()` hook from `@/contexts/AuthContext` (NOT Clerk's hook directly)
- **User Info**: Access via `useAuth()` hook (provides unified interface for both modes)
- **API Calls**: Clerk tokens automatically injected via `api.setTokenGetter(getToken)`

**IMPORTANT - Component Development Pattern:**
```typescript
// ❌ WRONG - Breaks in NoAuth mode (VITE_TORALE_NOAUTH=1)
import { useUser } from '@clerk/clerk-react'
const { user } = useUser()
const email = user?.primaryEmailAddress?.emailAddress

// ✅ CORRECT - Works in both Clerk and NoAuth modes
import { useAuth } from '@/contexts/AuthContext'
const { user } = useAuth()
const email = user?.email
const role = user?.publicMetadata?.role
```

**Why this matters:**
- `useUser()` from `@clerk/clerk-react` only works when `<ClerkProvider>` is present
- Local dev uses `NoAuthProvider` when `VITE_TORALE_NOAUTH=1`, which doesn't include ClerkProvider
- `useAuth()` from `@/contexts/AuthContext` provides a unified interface that works in both modes
- The abstraction layer ensures components work seamlessly in both production and local development

#### CLI Authentication
- **API Keys**: Users generate API keys in web dashboard (`/auth/api-keys`)
- **Key Format**: `sk_[32-char random string]` with SHA256 hash stored in database
- **Usage**: CLI accepts `--api-key` flag or reads from config file
- **Security**: Keys are hashed, never stored in plain text, can be revoked

### Authentication Flow

1. **Web App Login**:
   - User navigates to `/sign-in` or `/sign-up`
   - Clerk handles OAuth or email/password authentication
   - Clerk redirects to dashboard on success
   - Frontend calls `/auth/sync-user` to create/update local user record
   - Clerk token automatically included in all API requests

2. **CLI Authentication**:
   - User generates API key in web dashboard
   - Key displayed once, user saves it securely
   - CLI sends API key in Authorization header
   - Backend verifies key hash and authorizes request

### Security Benefits
- No passwords stored locally (Clerk handles all password management)
- OAuth reduces password fatigue and improves security
- Clerk handles 2FA, email verification, password reset
- API keys provide secure CLI access without exposing user credentials
- Tokens automatically expire and refresh

## API Design

### Authentication Endpoints
```
POST   /auth/sync-user                  # Sync Clerk user to database (auto-called on login)
GET    /auth/me                         # Get current user info
POST   /auth/api-keys                   # Generate new API key for CLI
GET    /auth/api-keys                   # List user's API keys
DELETE /auth/api-keys/{id}              # Revoke API key
```

### REST Endpoints
```
POST   /api/v1/tasks/suggest            # AI-powered task suggestion from natural language (context-aware)
POST   /api/v1/tasks/preview            # Preview search query without creating task (new)
POST   /api/v1/tasks                    # Create monitoring task
GET    /api/v1/tasks                    # List tasks
GET    /api/v1/tasks/{id}               # Get task details
PUT    /api/v1/tasks/{id}               # Update task (query, condition, schedule)
DELETE /api/v1/tasks/{id}               # Delete task + Temporal schedule
POST   /api/v1/tasks/{id}/execute       # Manual execution (test query)
GET    /api/v1/tasks/{id}/executions    # Full execution history
GET    /api/v1/tasks/{id}/notifications # Filtered: condition_met = true only
```

### Admin Endpoints (requires admin role)
```
GET    /admin/stats                     # Platform overview (users, tasks, executions, popular queries)
GET    /admin/queries                   # All user queries with statistics
GET    /admin/executions                # Full execution history across all users
GET    /admin/temporal/workflows        # Recent Temporal workflow executions (with clickable UI links)
GET    /admin/temporal/schedules        # All active Temporal schedules
GET    /admin/errors                    # Recent failed executions
GET    /admin/users                     # All platform users with activity stats
PATCH  /admin/users/{id}/deactivate     # Deactivate user account
```

**Admin Access**: Set `{"role": "admin"}` in user's publicMetadata via Clerk Dashboard

### CLI Commands
```bash
# Authentication
torale auth set-api-key              # Configure API key from web dashboard
torale auth status                   # Check authentication status
torale auth logout                   # Remove credentials

# Task management
torale task create \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced" \
  --schedule "0 9 * * *" \
  --notify-behavior once

torale task list [--active]
torale task get <task-id>
torale task update <task-id> [--name NAME] [--schedule CRON] [--active/--inactive]
torale task delete <task-id> [--yes]
torale task execute <task-id>       # Test search query manually
torale task logs <task-id>          # Full execution history

# Local development without auth
export TORALE_NOAUTH=1
torale task list
```

## Development Conventions

### Code Style
- **Python Philosophy**: Follow the Zen of Python principles
- **Type Checking**: Use Astral's `ty` instead of mypy
- **Linting**: Use `ruff` but be practical - ignore rules when there's good reason to violate them
- **Naming**: Prioritize readability over brevity

### Git Workflow
- **Commits**: Keep changes atomic and focused
- **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  - `feat: add task scheduling API`
  - `fix: handle temporal connection timeout`
  - `docs: update CLI usage examples`

### Testing
- **Framework**: pytest for all Python testing
- **Structure**: Mirror source structure in tests/
- **Coverage**: Focus on critical paths, don't overtest

### Error Handling
- **Philosophy**: Don't overindex on error handling
- **Strategy**: Allow errors to surface to their natural point
- **Implementation**: Handle errors as and when required, not preemptively

### Deployment
- **Environments**: Local → Staging → Production
- **Staging**: staging.torale.ai (same database, isolated Temporal task queue)
- **Principle**: Keep deployment simple, add complexity only when needed

## Design Principles

### Core Philosophy
1. **KISS (Keep It Simple, Stupid)**: Prefer simple solutions over complex ones
2. **YAGNI (You Aren't Gonna Need It)**: Avoid overengineering, build only what's needed now
3. **Readable Code**: Keep files light, create abstractions when they improve readability
4. **Future-Aware Design**: Keep post-MVP requirements in sight, design interfaces that won't create rework later - but don't build those features now

### Practical Application
- Design clean interfaces (like the executor pattern) that support future extensions without current complexity
- Prefer composition over inheritance
- Write code that's easy to understand and modify
- Make decisions that minimize future technical debt without over-engineering present solutions

## Development Workflow

### Quick Start with Justfile
```bash
# List all available commands
just

# Local Development
just dev           # Docker Compose
just test          # Run tests
just migrate       # Database migrations
just logs          # View logs

# Production Deployment (GKE)
just k8s-setup     # One-time setup
just k8s-deploy-all # Deploy to cluster
just k8s-status    # Check status
just k8s-logs-api  # View logs
```

### Local Development Setup
```bash
# Install dependencies
cd backend && uv sync

# Start all services (recommended)
just dev

# Or start services individually
docker compose up -d postgres temporal
cd backend && uv run uvicorn torale.api.main:app --reload
cd backend && uv run python -m torale.workers
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://torale:torale@localhost:5432/torale

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_...                # Backend: Verify Clerk tokens
CLERK_PUBLISHABLE_KEY=pk_test_...           # Backend: Initialize Clerk client
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...      # Frontend: Initialize ClerkProvider
VITE_API_BASE_URL=http://localhost:8000     # Frontend: API endpoint

# Temporal
# Local: localhost:7233
# Production: us-central1.gcp.api.temporal.io:7233
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_API_KEY=                         # Required for Temporal Cloud (production)
TEMPORAL_UI_URL=http://localhost:8080     # Temporal UI for clickable workflow links (Cloud: https://cloud.temporal.io)

# AI APIs (Gemini required, others optional)
GOOGLE_API_KEY=your-gemini-api-key       # Required for grounded search
OPENAI_API_KEY=                           # Optional fallback
ANTHROPIC_API_KEY=                        # Optional fallback

# Notifications (future)
NOTIFICATION_API_KEY=

# GKE Deployment (production only)
GCP_PROJECT_ID=
GCP_REGION=us-central1
```

## Implementation Status

### ✅ Completed
- **Infrastructure**: GKE + Cloud SQL + Temporal Cloud with GitHub Actions CI/CD
- **Environments**: Production + Staging with isolated Temporal task queues
- **Authentication**: Clerk (OAuth + email/password) with API key support for CLI
- **Core API**: Task CRUD with Temporal schedule management
- **Temporal Integration**: Temporal Cloud with automatic cron-based execution
- **Worker Framework**: Activities and workflows for task execution
- **Database Migrations**: Alembic migration system (incremental migrations)
- **Grounded Search**: Google Search via Gemini with condition evaluation
- **State Tracking**: last_known_state comparison and change detection
- **Notification System**: In-app notifications endpoint
- **Task Templates**: Pre-built templates for common monitoring use cases
- **CLI**: Full CLI with API key authentication and no-auth dev mode
- **Frontend**: React dashboard with Clerk authentication
- **Design System**: Neo-brutalist "The Machine" design system fully implemented (see `.claude/skills/torale-design-system.md`)
- **Cost Optimization**: Spot pods (60-91% savings), zonal Cloud SQL
- **Admin Console**: Full platform monitoring with 8 admin endpoints (stats, queries, executions, Temporal workflows/schedules, errors, users, user management)
- **Live Search Preview** (#37): `/api/v1/tasks/preview` endpoint allows testing queries before creating tasks
- **Immediate Task Execution** (#36): `run_immediately` flag executes tasks instantly after creation
- **Fixed Grounding Source Display** (#38): Clean domain names instead of Vertex AI redirect URLs, filtering of internal infrastructure URLs
- **AI-Powered Task Creation**: `/api/v1/tasks/suggest` endpoint uses LLM to generate task configuration from natural language prompts
- **Context-Aware Task Refinement**: "Magic Refine" feature accepts current task context to preserve details when updating (e.g., "add river facing" appends to existing query)
- **Visual Schedule Builder**: Custom schedule dialog with hourly/daily/weekly/monthly presets, human-readable cron display, and advanced cron input
- **Simplified Task Creation UX**: Single-page form with progressive disclosure for advanced options, replacing multi-step wizard
- **Modernized Task Editing**: Consistent UX with creation dialog, includes Magic Refine for AI-assisted updates
- **Temporal Context**: LLM now has awareness of last execution time for better change detection and noise reduction

### 🚧 In Progress
- **Historical state comparison UI**: Visual representation of state changes over time

### 📋 Future Work
- **External Notifications**: NotificationAPI integration for email/SMS
- **Browser Automation**: Monitor dynamic websites (Playwright integration)
- **Multi-step Workflows**: Chain multiple conditions together
- **Production Features**: Rate limiting, usage analytics, team collaboration
- **Observability**: Enhanced monitoring, alerting, and logging

## Security Requirements
- All API endpoints require authentication (Clerk JWT or API key)
- User isolation enforced via application-level WHERE clauses
- API keys (Google, OpenAI, Anthropic) stored securely in environment
- CLI API keys hashed with SHA256, never stored in plain text
- Rate limiting on API endpoints
- Input validation on all user data
- SQL injection prevention via parameterized queries (asyncpg)

## Database Migration Architecture

### Unified Init Container Pattern

**Both local and production use the same pattern**: migrations run in a separate container/job **before** the application starts.

**Why Init Container/Job Pattern?**

We use separate migration containers (not entrypoint scripts) because:
- **Separation of Concerns**: Migrations are separate from application startup, making failures easier to diagnose
- **Single Execution**: Runs once before application containers start (avoiding race conditions with multiple replicas)
- **Explicit Dependencies**: Clear dependency chain shows that database must be migrated before app starts
- **Failure Handling**: Migration failures prevent application from starting, ensuring database schema matches code

### Production: Kubernetes Job with Helm Hooks

**Implementation:**
- **Template**: `helm/torale/templates/migration-job.yaml`
- **Helm Hooks**: `pre-install,pre-upgrade` with weight `-5`
- **Containers**: Migration container + Cloud SQL Proxy sidecar
- **Command**: Waits for proxy → `alembic upgrade head`
- **Why Job not Pod Init Container**: Kubernetes init containers run before ALL containers including sidecars, but we need the Cloud SQL Proxy sidecar running

**Verification:**
```bash
# Check Job execution
kubectl get jobs -n torale | grep migrations
kubectl logs -n torale job/torale-migrations

# Verify current migration version
kubectl exec -n torale deploy/torale-api -- alembic current

# Check migration history
kubectl exec -n torale deploy/torale-api -- alembic history
```

### Local Development: Init Container

**Implementation:**
- **Service**: `init-migrations` in `docker-compose.yml`
- **Dependency Chain**: `postgres (healthy) → init-migrations (completed) → api (starts)`
- **Command**: Waits for postgres → `alembic upgrade head`
- **Pattern**: Mirrors production approach for consistency

**Verification:**
```bash
# Migrations run automatically on docker-compose up
docker compose up -d

# Check migration logs
docker compose logs init-migrations

# Verify current migration version
docker compose exec api alembic current
```

### Migration Best Practices

**Philosophy**: Forward-only migrations for production systems

**Core Rules:**
1. **Never modify migrations after production deployment** - Once applied, treat as immutable
2. **Never consolidate migrations in production systems** - Keep linear history
3. **Never reuse revision IDs** - Each migration must have unique identifier
4. **Test migrations on local copy before production** - Use `docker compose down -v` for fresh starts

### Migration Workflow

```bash
# Create new migration
docker compose exec api alembic revision --autogenerate -m "description"

# Test locally (fresh start)
just down-v && just dev-all

# Verify migration applied locally
docker compose exec api alembic current
docker compose exec api alembic history

# Deploy to production (automatic via Kubernetes Job)
git push origin main
# GitHub Actions → builds image → Helm deploys → Job runs migrations → API pods start
```

### Troubleshooting

**Local:**
- **Out of sync?** Never manually edit alembic_version table - use `alembic stamp`
- **Missing templates?** Run `just down-v && just dev-all` for fresh local start
- **Migration failed?** Check `docker compose logs init-migrations`
- **Need to re-run?** `docker compose down && docker compose up -d` (init container runs fresh)

**Production:**
- **Migration failed?** Check `kubectl logs -n torale job/torale-migrations`
- **Migration job not running?** Verify Helm hooks: `kubectl get jobs -n torale -o yaml | grep "helm.sh/hook"`
- **Need current version?** `kubectl exec -n torale deploy/torale-api -- alembic current`

## MVP Success Criteria
✅ Users can create monitoring tasks via API/CLI
✅ Tasks execute automatically on cron schedules (Temporal)
✅ Grounded search queries Google Search via Gemini
✅ LLM intelligently evaluates if conditions are met
✅ State tracking prevents duplicate notifications
✅ In-app notifications viewable via API
✅ Configurable notify behavior (once/always/track_state)
✅ System handles errors gracefully with retries

## Post-MVP Roadmap

### Enhanced Monitoring Capabilities
- **Browser Automation**: Monitor dynamic websites (Playwright integration)
- **Price Tracking**: Track price changes with historical charts
- **Availabilityx Monitoring**: Stock alerts, event tickets, reservations
- **Multi-source Aggregation**: Combine results from multiple searches
- **Custom Scrapers**: User-defined extraction rules for specific websites

### Notification Enhancements
- **External Channels**: Email, SMS, Slack, Discord via NotificationAPI
- **Rich Notifications**: Include images, tables, charts
- **Digest Mode**: Bundle multiple notifications into daily/weekly summaries
- **Notification Templates**: User-customizable notification formats

### Advanced Features
- **Multi-step Workflows**: "When X happens, then check Y, then notify"
- **Conditional Chains**: Complex logic with AND/OR conditions
- **Team Collaboration**: Share monitoring tasks across organizations
- **Template Marketplace**: Pre-built monitoring templates
- **API Integrations**: Monitor APIs, webhooks, RSS feeds
- **Historical Analysis**: Trend detection, pattern recognition