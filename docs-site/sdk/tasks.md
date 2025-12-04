# Tasks

Create and manage monitoring tasks with the Python SDK.

## Create Task

```python
task = client.tasks.create(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
    schedule="0 9 * * *"
)
```

**With all options:**

```python
task = client.tasks.create(
    name="iPhone Release Monitor",
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
    schedule="0 9 * * *",
    notify_behavior="once",
    run_immediately=True
)
```

## List Tasks

```python
# Get all tasks
tasks = client.tasks.list()

# Filter active only
active_tasks = client.tasks.list(active=True)

# With pagination
tasks = client.tasks.list(page=2, limit=10)
```

## Get Task

```python
task = client.tasks.get("task-id")

print(f"Name: {task.name}")
print(f"Active: {task.state}")
print(f"Condition met: {task.condition_met}")
```

## Update Task

```python
# Update schedule
task = client.tasks.update(
    "task-id",
    schedule="0 */6 * * *"
)

# Pause task
task = client.tasks.update(
    "task-id",
    state="paused"
)

# Change notification behavior
task = client.tasks.update(
    "task-id",
    notify_behavior="track_state"
)
```

## Delete Task

```python
client.tasks.delete("task-id")
```

## Execute Immediately

```python
execution_id = client.tasks.execute("task-id")
```

## View Executions

```python
# Get execution history
executions = client.tasks.get_executions("task-id")

for execution in executions:
    print(f"Status: {execution.status}")
    if execution.condition_met:
        print(f"Answer: {execution.result['answer']}")
```

## View Notifications

```python
# Get only executions where condition was met
notifications = client.tasks.get_notifications("task-id")

for notif in notifications:
    print(f"Time: {notif.created_at}")
    print(f"Answer: {notif.answer}")
```

## Next Steps

- Test queries with [Preview](/sdk/preview)
- Use [Async Client](/sdk/async) for concurrent operations
- Handle [Errors](/sdk/errors)
