---
description: Torale database schema documentation. Tables, relationships, indexes, constraints, and data model for self-hosted deployments.
---

# Database Schema

Torale uses PostgreSQL for all data storage, with separate tables for users, tasks, executions, and templates.

## Users & Authentication

### Users Table

Stores Clerk-authenticated user accounts:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### API Keys Table

CLI authentication keys with SHA256 hashing:

```sql
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
```

## Tasks & Monitoring

### Tasks Table

Monitoring tasks with state machine:

```sql
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  schedule TEXT NOT NULL, -- cron expression
  state TEXT NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'completed'

  -- Grounded search monitoring fields
  search_query TEXT,  -- "When is next iPhone release?"
  condition_description TEXT,  -- "A specific date has been announced"
  notify_behavior TEXT DEFAULT 'once',  -- 'once', 'always'
  last_known_state JSONB,  -- Previous search results for comparison
  last_execution_id UUID REFERENCES task_executions(id),  -- Latest execution

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  state_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CHECK (state IN ('active', 'paused', 'completed'))
);
```

**Key Fields:**
- `state`: Task lifecycle state (see [Task State Machine](/architecture/task-state-machine))
- `last_known_state`: JSONB storing previous search results for change detection
- `notify_behavior`: Controls notification frequency

### Task Executions Table

Execution history with results:

```sql
CREATE TABLE task_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES tasks(id),
  status TEXT NOT NULL, -- 'pending', 'running', 'success', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  result JSONB,
  error_message TEXT,

  -- Grounded search execution fields
  notification TEXT,  -- Notification text (if condition met)
  grounding_sources JSONB,  -- Array of source URLs with metadata

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Fields:**
- `result`: JSONB with search results and LLM analysis
- `grounding_sources`: Array of URLs with titles and snippets
- `condition_met`: Whether the trigger condition was satisfied

### Task Templates Table

Pre-built monitoring templates:

```sql
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
  state TEXT NOT NULL DEFAULT 'active',  -- Template availability: 'active', 'paused'
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
  CHECK (notify_behavior IN ('once', 'always')),
  CHECK (state IN ('active', 'paused'))
);
```

## Indexes

Key indexes for performance:

```sql
-- User lookups
CREATE INDEX idx_users_clerk_id ON users(clerk_user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- Task queries
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_state ON tasks(state);
CREATE INDEX idx_tasks_user_state ON tasks(user_id, state);

-- Execution queries
CREATE INDEX idx_executions_task_id ON task_executions(task_id);
CREATE INDEX idx_executions_created_at ON task_executions(created_at DESC);
CREATE INDEX idx_executions_condition_met ON task_executions(condition_met);
```

## Migrations

Database schema is managed with [Alembic](https://alembic.sqlalchemy.org/).

**Migration workflow:**
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

See [Deployment Architecture](https://github.com/torale-ai/torale/blob/main/CLAUDE.md#database-migration-architecture) for production migration patterns.

## Next Steps

- Learn about [Task State Machine](/architecture/task-state-machine)
- Read [Architecture Overview](/architecture/overview)
