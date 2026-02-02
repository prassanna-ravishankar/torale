# Task State Machine

Torale uses an explicit state machine to manage task lifecycle, replacing the previous boolean `is_active` field with a proper state enum.

## States

Tasks can be in one of three states:

- **`active`**: Task is running on schedule, APScheduler job is active
- **`paused`**: Task is paused, APScheduler job is paused (no executions)
- **`completed`**: Task has finished (condition met with `notify_behavior="once"`)

## State Transitions

### Valid Transitions

```
active ←→ paused    (pause/resume)
active → completed  (condition met, notify_behavior="once")
paused → completed  (manual completion)
completed → active  (restart after completion)
```

### Invalid Transitions

- `completed → paused` (must go through active to restart)
- Direct transitions skipping states

## Implementation

### Database Schema

```sql
CREATE TABLE tasks (
  ...
  state TEXT NOT NULL DEFAULT 'active',
  CHECK (state IN ('active', 'paused', 'completed')),
  ...
);
```

### State Machine Class

The `TaskStateMachine` class validates transitions and coordinates database + scheduler updates:

```python
from torale.core.task_state_machine import TaskStateMachine, TaskState

state_machine = TaskStateMachine(db_conn=db)

# Pause a task
await state_machine.transition(
    task_id=task_id,
    from_state=TaskState.ACTIVE,
    to_state=TaskState.PAUSED,
    task_name=task.name,
    user_id=user.id,
    schedule=task.schedule
)
```

### Scheduler Coordination

State transitions automatically manage APScheduler jobs:

- **`active` → `paused`**: Pauses APScheduler job (no new executions)
- **`paused` → `active`**: Resumes APScheduler job
- **`active` → `completed`**: Removes APScheduler job
- **`completed` → `active`**: Creates new APScheduler job

### Rollback on Failure

If scheduler operations fail during transition, the database state is rolled back:

```python
try:
    await self._update_database_state(task_id, to_state)
    result = await self._state_manager.set_task_active_state(...)
except Exception as e:
    # Rollback database to original state
    await self._update_database_state(task_id, from_state)
    raise
```

## API Endpoints

### Update Task State

```bash
curl -X PUT http://localhost:8000/api/v1/tasks/{task_id} \
  -H "Content-Type: application/json" \
  -d '{"state": "paused"}'
```

### Query by State

```bash
# List only active tasks
curl http://localhost:8000/api/v1/tasks?state=active

# List completed tasks
curl http://localhost:8000/api/v1/tasks?state=completed
```

## SDK Usage

### Python SDK

```python
from torale import Torale

client = Torale()

# Pause a task
task = client.tasks.update(task_id, state="paused")

# Resume a task
task = client.tasks.update(task_id, state="active")

# Mark as completed
task = client.tasks.update(task_id, state="completed")

# List by state
active_tasks = client.tasks.list(state="active")
```

### CLI

```bash
# Pause a task
torale task update <task-id> --state paused

# Resume a task
torale task update <task-id> --state active

# List active tasks
torale task list --state active
```

## Automatic State Transitions

### Completion on Condition Met

When `notify_behavior="once"` and the condition is met:

1. Task execution completes successfully
2. Notification is sent
3. Task state transitions to `completed`
4. APScheduler job is removed

This prevents duplicate notifications for one-time alerts.

### User Deactivation

When a user is deactivated (via admin endpoint):

1. All user's tasks transition to `paused`
2. All APScheduler jobs are paused
3. Tasks retain their data for potential reactivation

## Migration from `is_active`

Previous boolean field:
- `is_active=true` → `state="active"`
- `is_active=false` → `state="paused"`

The migration preserves all existing task states during the upgrade.

## Benefits

### 1. **Explicit State Management**
- Clear semantics: "paused" vs "completed" vs "active"
- No ambiguity about what `false` means

### 2. **Scheduler Consistency**
- Database and APScheduler always in sync
- Automatic rollback on failures

### 3. **Better Notifications**
- Completed tasks don't send duplicate notifications
- Paused tasks can be resumed without re-triggering

### 4. **Audit Trail**
- State changes can be logged
- Clear lifecycle history

## Next Steps

- View [Database Schema](/architecture/database-schema)
- Learn about [State Tracking](/architecture/state-tracking) (search results)
