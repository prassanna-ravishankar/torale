# Architecture

System architecture for self-hosted Torale deployments.

## Component Overview

```
Frontend → API → PostgreSQL
            ↓
        Temporal
            ↓
        Workers → LLM APIs
            ↓
      Notifications
```

## API Service

FastAPI application serving REST endpoints. Handles authentication via Clerk JWT tokens or API keys, validates requests, and coordinates with PostgreSQL for data persistence and Temporal for workflow scheduling.

Connects to PostgreSQL via Cloud SQL Proxy sidecar in Kubernetes, or direct connection in Docker Compose.

## Workers

Temporal workers execute monitoring tasks on schedule. Each worker runs activities that perform grounded search, evaluate conditions, compare with previous state, and send notifications when appropriate.

Workers scale horizontally and process tasks from the Temporal queue independently.

## Executors

The executor system implements different types of task execution. The grounded search executor queries Google Search via Gemini, extracts concise answers, evaluates whether conditions are met, and provides source attribution.

Executors are designed to be pluggable for future expansion to browser automation, API monitoring, or other sources.

## Database Schema

PostgreSQL stores users (Clerk-integrated), API keys (hashed), tasks with configuration, execution history, and notifications. The schema uses JSONB columns for flexible configuration storage and state tracking.

Migrations managed through Alembic with forward-only migrations in production.

## Temporal Workflows

Each task has a corresponding Temporal schedule that triggers workflow executions. The monitoring workflow fetches task configuration, executes grounded search via activities, compares state, and sends notifications.

Temporal provides durable execution with automatic retries, schedule management, and full observability through the Temporal UI.

## Scaling Strategy

**API and Workers** - Horizontal Pod Autoscaler (HPA) scales based on CPU usage from 2 to 10 replicas

**Database** - Cloud SQL auto-scales storage and compute, with optional read replicas for high read loads

**Cost Optimization** - All pods use Spot VMs for 60-91% savings, with automatic migration on preemption

## Next Steps

- Set up [Docker Compose](/self-hosted/docker-compose)
- Deploy to [Kubernetes](/self-hosted/kubernetes)
- Read [Configuration](/self-hosted/configuration)
