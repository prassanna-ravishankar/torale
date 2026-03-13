---
description: Manage monitoring tasks with Torale Python SDK. Create, list, update, and delete tasks programmatically with fluent API examples.
---

# Tasks

Create and manage monitoring tasks with the Python SDK.

## Create Task

The `name`, `search_query`, and `condition_description` are the core parameters:

```python
task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
)
```

**With all options:**

```python
from torale.tasks import TaskState

task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
    notifications=[
        {"type": "email", "address": "me@example.com"},
        {"type": "webhook", "url": "https://myapp.com/alert"},
    ],
    state=TaskState.ACTIVE,  # or "active" (default)
)
```

### Create Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | `str` | Yes | - | Task name |
| `search_query` | `str` | Yes | - | Query to monitor |
| `condition_description` | `str` | Yes | - | Condition that triggers notification |
| `notifications` | `list[dict]` | No | `[]` | Notification channels |
| `state` | `str` or `TaskState` | No | `"active"` | `"active"` or `"paused"` |

### Notification Config

Each notification dict has a `type` field and type-specific fields:

```python
# Email notification
{"type": "email", "address": "me@example.com"}

# Webhook notification
{"type": "webhook", "url": "https://myapp.com/alert", "method": "POST", "headers": {"X-Custom": "value"}}
```

## Fluent Builder API

For a more readable syntax, use the fluent builder:

```python
# Via client instance
task = (client.monitor("When is iPhone 17 being released?")
    .when("Apple has announced a specific release date")
    .notify(email="me@example.com", webhook="https://myapp.com/alert")
    .named("iPhone Release Monitor")
    .create())

# Create in paused state
task = (client.monitor("Bitcoin price")
    .when("price exceeds $100,000")
    .paused()
    .create())
```

Or use the standalone `monitor()` function:

```python
from torale import monitor

task = (monitor("Bitcoin price")
    .when("price exceeds $100,000")
    .notify(webhook="https://myapp.com/crypto")
    .create())
```

The standalone `monitor()` creates a default `Torale` client automatically (using env vars or config file for authentication).

### Builder Methods

| Method | Description |
|--------|-------------|
| `.when(condition)` | Set the condition description (required) |
| `.notify(email=..., webhook=...)` | Add notification channels |
| `.named(name)` | Set a custom task name |
| `.paused()` | Create task in paused state |
| `.create()` | Build and create the task |

## List Tasks

```python
# Get all tasks
tasks = client.tasks.list()

# Filter active only
active_tasks = client.tasks.list(active=True)

# Filter paused only
paused_tasks = client.tasks.list(active=False)
```

## Get Task

```python
task = client.tasks.get("task-id")

print(f"Name: {task.name}")
print(f"State: {task.state}")
print(f"Search Query: {task.search_query}")
print(f"Created: {task.created_at}")
print(f"Next Run: {task.next_run}")
```

### Task Fields

Key fields on the returned `Task` object:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `UUID` | Task ID |
| `name` | `str` | Task name |
| `state` | `TaskState` | `"active"`, `"paused"`, or `"completed"` |
| `search_query` | `str` | Search query |
| `condition_description` | `str` | Trigger condition |
| `notifications` | `list[NotificationConfig]` | Notification channels |
| `created_at` | `datetime` | Creation timestamp |
| `next_run` | `datetime` or `None` | Next scheduled execution |
| `last_execution` | `TaskExecution` or `None` | Most recent execution |

## Update Task

Only pass the fields you want to change:

```python
# Pause task
task = client.tasks.update("task-id", state="paused")

# Resume task
task = client.tasks.update("task-id", state="active")

# Update search query and condition
task = client.tasks.update(
    "task-id",
    search_query="New search query",
    condition_description="New condition",
)
```

## Delete Task

```python
client.tasks.delete("task-id")
```

## Execute Immediately

Trigger a manual execution (test run):

```python
execution = client.tasks.execute("task-id")
print(f"Status: {execution.status}")
```

## View Executions

```python
# Get execution history
executions = client.tasks.executions("task-id")

for execution in executions:
    print(f"Status: {execution.status}")
    print(f"Started: {execution.started_at}")
    if execution.notification:
        print(f"Notification: {execution.notification}")

# Limit results
recent = client.tasks.executions("task-id", limit=5)
```

## View Notifications

Get only executions where the condition was met:

```python
notifications = client.tasks.notifications("task-id")

for notif in notifications:
    print(f"Time: {notif.started_at}")
    print(f"Notification: {notif.notification}")
    if notif.grounding_sources:
        print(f"Sources: {len(notif.grounding_sources)}")
```

## Next Steps

- Use [Async Client](/sdk/async) for concurrent operations
- Handle [Errors](/sdk/errors)
- View [Examples](/sdk/examples)
