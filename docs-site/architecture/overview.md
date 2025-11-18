# System Overview

Torale is a grounded search monitoring platform built for scalability and reliability.

## Architecture Diagram

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

## Tech Stack

### Backend
- **Python FastAPI** - REST API server
- **PostgreSQL 16** - Cloud SQL managed database
- **Temporal Cloud** - Workflow orchestration
- **UV** - Fast Python package manager

### Frontend
- **React 18 + TypeScript** - UI framework
- **Vite** - Build tool
- **Clerk** - Authentication (OAuth + email/password)

### AI & Search
- **Google Gemini** - Primary LLM with grounded search
- **Google Search API** - Via Gemini grounding
- **OpenAI/Anthropic** - Fallback models

### Infrastructure
- **GKE Autopilot** - Kubernetes cluster
- **Cloud SQL** - Managed PostgreSQL
- **GCE Load Balancer** - Ingress with SSL
- **Spot VMs** - Cost optimization (60-91% savings)
- **GitHub Actions** - CI/CD with Workload Identity

## Core Components

### 1. API Service
FastAPI application handling:
- Task CRUD operations
- Authentication (Clerk JWT + API keys)
- Preview endpoint for testing queries
- Admin endpoints for platform monitoring

**Location:** `backend/src/torale/api/`

### 2. Workers
Temporal workers executing scheduled tasks:
- Cron-based execution via Temporal schedules
- Grounded search with condition evaluation
- State comparison and change detection
- Notification triggering

**Location:** `backend/src/torale/workers/`

### 3. Executors
Task execution engine:
- `GroundedSearchExecutor` - Google Search + Gemini evaluation
- Condition evaluation logic
- Source attribution and filtering
- State tracking

**Location:** `backend/src/torale/executors/`

### 4. Frontend
React SPA with:
- Clerk authentication
- Task creation wizard
- Execution history viewer
- Notification dashboard

**Location:** `frontend/src/`

### 5. CLI
Python CLI using Typer:
- API key authentication
- Task management commands
- Preview functionality
- JSON output for scripting

**Location:** `backend/src/torale/cli/`

## Data Flow

### Task Creation
1. User creates task via dashboard/CLI/SDK
2. API validates and stores in PostgreSQL
3. Temporal schedule created with cron expression
4. Task becomes active and ready for execution

### Task Execution
1. Temporal triggers workflow at scheduled time
2. Worker picks up task from queue
3. Executor performs grounded search:
   - Queries Google Search via Gemini
   - LLM evaluates condition
   - Extracts and filters sources
4. State comparison with `last_known_state`
5. Notification sent if condition met and changed
6. Execution result stored in database

### Notification Flow
1. Condition evaluation determines if met
2. State comparison checks for meaningful changes
3. Notification behavior rules applied:
   - `once` - Notify once, then pause task
   - `always` - Notify every time
   - `track_state` - Notify on changes only
4. Notification stored in database
5. User views in dashboard

## Scalability

### Horizontal Scaling
- **API**: 2-10 replicas (HPA based on CPU)
- **Workers**: 2-10 replicas (HPA based on CPU)
- **Frontend**: 2-10 replicas (HPA based on CPU)

### Database
- Cloud SQL with automated backups
- Connection pooling via Cloud SQL Proxy
- Read replicas for scaling (future)

### Temporal
- Temporal Cloud handles workflow orchestration
- Automatic retry and error handling
- Durable execution across failures

## Security

### Authentication
- Clerk for web (OAuth + email/password)
- API keys for CLI/SDK (SHA256 hashed)
- JWT token verification on every request

### Data Protection
- All connections use TLS
- Secrets managed via Kubernetes secrets
- No passwords stored (Clerk handles auth)

### Network Security
- Private VPC for database
- Cloud SQL Proxy for secure connections
- GKE Managed Certificates for SSL

## Cost Optimization

### Spot Pods
All services use Spot VMs:
- 60-91% cost savings
- Automatic migration on preemption
- Suitable for stateless workloads

### Resource Right-Sizing
- API: 100m CPU, 256Mi memory
- Workers: 100m CPU, 256Mi memory
- Frontend: 50m CPU, 64Mi memory

### Regional Deployment
- Single region (us-central1) for simplicity
- Zonal Cloud SQL for cost savings

**Monthly cost:** ~$50-100 for production workload

## Next Steps

- Learn about [Grounded Search](/architecture/grounded-search)
- Understand [Temporal Workflows](/architecture/temporal-workflows)
- Explore [State Tracking](/architecture/state-tracking)
- View [Database Schema](/architecture/database-schema)
