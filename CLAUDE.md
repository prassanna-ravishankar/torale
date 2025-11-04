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
- **Database**: PostgreSQL 16 (self-hosted)
- **Authentication**: FastAPI-Users (JWT-based)
- **Scheduling**: Temporal workflows with cron schedules
- **Infrastructure**: Google Cloud Run + Cloud Build (deployment)
- **AI**: Google Gemini with grounded search (primary), OpenAI/Anthropic (fallback)
- **Search**: Google Search API via Gemini grounding
- **Notifications**: In-app (database-stored), future: NotificationAPI
- **CLI**: Python typer
- **Package Management**: UV
- **Local Development**: Docker Compose (PostgreSQL + Temporal + API + Workers)

### System Design
```
CLI Client ──► Cloud Run API ──► PostgreSQL
                     │             (Auth + DB + State Tracking)
                     ▼
            Temporal Schedules (Cron-based execution)
                     │
                     ▼
            Cloud Run Workers ──► Gemini + Google Search
            (Task execution)   └──► In-app Notifications
                     │
                     └──► State comparison & condition evaluation
```

### Core Components
1. **API Service**: FastAPI app handling task CRUD operations and notifications endpoint
2. **Workers**: Temporal workers executing scheduled monitoring tasks
3. **Executors**: Grounded search executor with condition evaluation
4. **CLI**: Command-line interface for creating and managing monitoring tasks
5. **State Tracker**: Compares current search results with historical state to detect changes

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
├── frontend/             # Frontend (to be added)
├── docs/                 # Documentation
│   └── TEST_TEMPORAL.md
├── justfile              # Task runner (just dev, just test, etc.)
├── docker-compose.yml    # Orchestration
├── cloudbuild.yaml       # Cloud Build config
├── deploy.sh             # Deployment script
├── .env / .env.example
├── CLAUDE.md
└── README.md
```

## Database Schema
```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
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
1. **Grounded Search**: Queries Google Search via Gemini's grounding feature
2. **Answer Extraction**: LLM synthesizes answer from search results
3. **Condition Evaluation**: LLM determines if trigger condition is met
4. **State Comparison**: Compares with `last_known_state` to detect changes
5. **Source Attribution**: Extracts and stores grounding citations

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

## API Design

### REST Endpoints
```
POST   /api/v1/tasks                    # Create monitoring task
GET    /api/v1/tasks                    # List tasks
GET    /api/v1/tasks/{id}               # Get task details
PUT    /api/v1/tasks/{id}               # Update task (query, condition, schedule)
DELETE /api/v1/tasks/{id}               # Delete task + Temporal schedule
POST   /api/v1/tasks/{id}/execute       # Manual execution (test query)
GET    /api/v1/tasks/{id}/executions    # Full execution history
GET    /api/v1/tasks/{id}/notifications # Filtered: condition_met = true only
```

### CLI Commands
```bash
torale auth login
torale task create \
  --query "When is the next iPhone release?" \
  --condition "A specific date has been announced" \
  --schedule "0 9 * * *" \
  --notify-behavior once

torale task list
torale task execute <task-id>       # Test search query manually
torale notifications <task-id>      # View alerts when condition was met
torale logs <task-id>               # Full execution history
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
- **Environments**: Local → Production (no staging for MVP)
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

# Start all services
just dev

# Run tests
just test

# Database migrations
just migrate

# View logs
just logs
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

# Authentication
SECRET_KEY=your-secret-key-for-jwt

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# AI APIs (Gemini required, others optional)
GOOGLE_API_KEY=your-gemini-api-key       # Required for grounded search
OPENAI_API_KEY=                           # Optional fallback
ANTHROPIC_API_KEY=                        # Optional fallback

# Notifications (future)
NOTIFICATION_API_KEY=

# Deployment
GCP_PROJECT_ID=
CLOUD_RUN_REGION=us-central1
```

## Implementation Status

### ✅ Completed
- **Infrastructure**: PostgreSQL + Temporal + Docker Compose setup
- **Authentication**: FastAPI-Users with JWT tokens
- **Core API**: Task CRUD with Temporal schedule management
- **Temporal Integration**: Automatic cron-based execution
- **Worker Framework**: Activities and workflows for task execution
- **Database Migrations**: Alembic migration system

### 🚧 In Progress: Grounded Search Migration
- **Database Schema**: Add grounded search fields (search_query, condition_description, notify_behavior, etc.)
- **GroundedSearchExecutor**: Replace llm_text with grounded search + condition evaluation
- **State Tracking**: Implement last_known_state comparison logic
- **Notification System**: In-app notifications endpoint
- **Testing**: E2E tests for monitoring use cases

### 📋 Future Work
- **External Notifications**: NotificationAPI integration for email/SMS
- **CLI Enhancement**: Update CLI for monitoring task creation
- **Multi-step Workflows**: Chain multiple conditions together
- **Production Deployment**: Cloud Run deployment with auto-scaling
- **Observability**: Monitoring, alerting, and logging infrastructure

## Security Requirements
- All API endpoints require JWT authentication (FastAPI-Users)
- User isolation enforced via application-level WHERE clauses
- API keys (Google, OpenAI, Anthropic) stored securely in environment
- Rate limiting on API endpoints
- Input validation on all user data
- SQL injection prevention via parameterized queries (asyncpg)

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
- **Availability Monitoring**: Stock alerts, event tickets, reservations
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