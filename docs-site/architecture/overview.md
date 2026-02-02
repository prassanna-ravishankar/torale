# System Overview

Torale is a grounded search monitoring platform built for scalability and reliability.

## Architecture Diagram

```
User ──► Frontend (torale.ai)
              ↓
         API (api.torale.ai) ──► Cloud SQL PostgreSQL
              ↓                   (Auth + DB + State)
         APScheduler
              ↓
         Agent ──► Perplexity Search + Mem0 Memory
              └──► Notifications (email/webhook)
                   Condition evaluation & evidence
```

## Tech Stack

### Backend
- **Python FastAPI** - REST API server
- **PostgreSQL 16** - Cloud SQL managed database
- **APScheduler** - In-process job scheduling with PostgreSQL job store
- **UV** - Fast Python package manager

### Frontend
- **React 18 + TypeScript** - UI framework
- **Vite** - Build tool
- **Clerk** - Authentication (OAuth + email/password)

### AI & Search
- **Gemini** - Monitoring agent (via Pydantic AI)
- **Perplexity** - Web search
- **Mem0** - Cross-run agent memory

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

### 2. Scheduler
APScheduler with PostgreSQL job store:
- Cron-based task execution
- Dynamic rescheduling via agent `next_run`
- Job state sync on startup

**Location:** `backend/src/torale/scheduler/`

### 3. Monitoring Agent
Gemini-powered agent service (Pydantic AI):
- Perplexity search for web monitoring
- Mem0 for cross-run memory and context
- Returns structured evidence, sources, confidence, and notifications

**Location:** `torale-agent/`

### 4. Frontend
React SPA with:
- Clerk authentication
- Task creation wizard
- Execution history viewer
- Notification dashboard

**Location:** `frontend/src/`

### 6. CLI
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
3. APScheduler job created with cron expression
4. Task becomes active and ready for execution

### Task Execution
1. APScheduler triggers job at scheduled time
2. Backend calls the monitoring agent
3. Agent searches via Perplexity, checks Mem0 memory
4. Agent evaluates condition, returns evidence + sources
5. Notification sent if condition met
6. Execution result stored in database
7. Agent's `next_run` dynamically reschedules the job

### Notification Flow
1. Agent determines if condition is met
2. Notification behavior rules applied:
   - `once` - Notify once, then complete task
   - `always` - Notify every time
3. Notification sent via email/webhook
4. User views in dashboard

## Scalability

### Horizontal Scaling
- **API**: 2-10 replicas (HPA based on CPU)
- **Frontend**: 2-10 replicas (HPA based on CPU)

### Database
- Cloud SQL with automated backups
- Connection pooling via Cloud SQL Proxy
- Read replicas for scaling (future)

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
- Explore [State Tracking](/architecture/state-tracking)
- View [Database Schema](/architecture/database-schema)
