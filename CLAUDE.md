# CLAUDE.md - Torale Project Context

## Project Overview
Torale is a platform-agnostic background task manager for AI-powered automation. Users create scheduled tasks using natural language prompts like "Write me a blog post every morning at 6 AM about climate tech" or "Check the weather and send me a summary every day at 7 AM."

**Domain**: torale.ai  
**Current Status**: Pre-development (specification complete)  
**MVP Goal**: CLI-driven task scheduling with LLM execution  
**Future Vision**: IFTTT-style conditional automation platform

## Architecture

### Tech Stack
- **Backend**: Python FastAPI
- **Database**: Supabase Cloud (PostgreSQL + Auth)
- **Scheduling**: Temporal workflows
- **Infrastructure**: Google Cloud Run + Cloud Build
- **AI**: OpenAI/Anthropic APIs
- **Notifications**: NotificationAPI
- **CLI**: Python typer
- **Package Management**: UV
- **Local Development**: Docker Compose (Temporal only)

### System Design
```
CLI Client ──► Cloud Run API ──► Supabase Cloud
                     │               (Auth + DB)
                     ▼
            Cloud Run Workers ──► LLM APIs
            (Temporal)        └──► NotificationAPI
```

### Core Components
1. **API Service**: FastAPI app handling task CRUD operations
2. **Workers**: Temporal workers executing scheduled tasks
3. **Executors**: Pluggable task execution engines (starting with LLM text generation)
4. **CLI**: Command-line interface for task management

## Project Structure
```
torale/
├── pyproject.toml
├── docker-compose.yml      # Local Temporal only
├── cloudbuild.yaml
├── Dockerfile
├── src/torale/
│   ├── api/               # FastAPI app
│   ├── workers/           # Temporal workers
│   ├── executors/         # Task executors
│   ├── cli/               # CLI commands
│   └── core/              # Shared utilities
└── tests/
```

## Database Schema
```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  name TEXT NOT NULL,
  schedule TEXT NOT NULL, -- cron expression
  executor_type TEXT NOT NULL DEFAULT 'llm_text',
  config JSONB NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE task_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES tasks(id),
  status TEXT NOT NULL, -- 'pending', 'running', 'success', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  result JSONB,
  error_message TEXT
);
```

## Executor Architecture

### Key Design Principle
The executor system is designed for extensibility. The MVP includes only `llm_text` executor, but the interface supports future executors like `llm_web_search`, `llm_browser`, `webhook`, etc.

### Executor Interface
```python
class TaskExecutor(ABC):
    @abstractmethod
    async def execute(self, config: dict) -> dict:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass
```

### Task Configuration Format
```json
{
  "name": "Daily blog post",
  "schedule": "0 6 * * *",
  "executor_type": "llm_text",
  "config": {
    "prompt": "Write a 500-word blog post about renewable energy trends",
    "model": "gpt-4",
    "max_tokens": 1000
  }
}
```

## API Design

### REST Endpoints
```
POST   /api/v1/tasks              # Create task
GET    /api/v1/tasks              # List tasks
GET    /api/v1/tasks/{id}         # Get task
PUT    /api/v1/tasks/{id}         # Update task
DELETE /api/v1/tasks/{id}         # Delete task
POST   /api/v1/tasks/{id}/execute # Manual execution
GET    /api/v1/tasks/{id}/executions # Execution history
```

### CLI Commands
```bash
torale auth login
torale task create "Daily summary" --schedule "0 9 * * *" --prompt "Summarize tech news"
torale task list
torale task execute <task-id>
torale logs <task-id>
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

### Local Development Setup
```bash
# Install dependencies
uv sync

# Start Temporal locally
docker compose up -d temporal

# Start API server
uv run uvicorn torale.api:app --reload

# Start workers
uv run python -m torale.workers
```

### Environment Variables
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Temporal
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default

# LLM APIs
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Notifications
NOTIFICATION_API_KEY=

# Deployment
GCP_PROJECT_ID=
CLOUD_RUN_REGION=us-central1
```

## Implementation Tasks

### Current Priority: Infrastructure Setup
1.1 Set up Supabase cloud project and configure authentication  
1.2 Create database schema and RLS policies *(Depends on: 1.1)*  
1.3 Configure Cloud Run services and Cloud Build pipeline  
1.4 Set up local development environment with Docker Temporal

### Next: Core API Development
2.1 Create FastAPI application with Supabase auth integration *(Depends on: 1.1)*  
2.2 Implement task CRUD operations with database integration *(Depends on: 1.2, 2.1)*  
2.3 Deploy API service to Cloud Run *(Depends on: 1.3, 2.2)*

### Then: Task Execution Engine
3.1 Implement LLMTextExecutor with OpenAI/Anthropic integration  
3.2 Create Temporal workflows and activities for task scheduling *(Depends on: 1.4)*  
3.3 Deploy Temporal workers to Cloud Run *(Depends on: 1.3, 3.1, 3.2)*  
3.4 Integrate NotificationAPI for result delivery *(Depends on: 3.1)*  
3.5 Add execution logging and error handling *(Depends on: 3.3, 3.4)*

### CLI Development
4.1 Set up CLI framework with typer  
4.2 Implement task management commands *(Depends on: 2.2)*  
4.3 Add authentication flow for CLI *(Depends on: 2.1)*  
4.4 Add manual task execution and logging features *(Depends on: 3.3)*

### Production Hardening
5.1 Set up monitoring, alerting, and observability  
5.2 Add comprehensive error handling across all services *(Depends on: 2.3, 3.5)*  
5.3 Configure auto-scaling policies for Cloud Run services *(Depends on: 2.3, 3.3)*  
5.4 Create deployment and usage documentation

## Security Requirements
- All API endpoints require Supabase authentication
- User isolation enforced via RLS policies
- LLM API keys stored securely in environment
- Rate limiting on API endpoints
- Input validation on all user data

## MVP Success Criteria
- Users can create and manage scheduled AI tasks via CLI
- Tasks execute reliably on schedule
- Results delivered successfully via notifications
- System handles basic error scenarios gracefully

## Post-MVP Roadmap

### Future Executor Types
- `llm_web_search`: Web search + LLM analysis
- `llm_browser`: Browser automation with LLM
- `webhook`: HTTP webhook execution
- `api_call`: Generic API integration

### Advanced Features
- Conditional execution (weather-based triggers)
- Multi-step workflows
- Template marketplace
- Team/organization support
- Advanced scheduling (timezone awareness)