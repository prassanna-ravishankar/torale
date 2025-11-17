# Quickstart

Get started with the Torale Python SDK in minutes.

## Installation

```bash
pip install torale
```

## Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings → API Keys
3. Generate new key
4. Copy key (shown only once)

## Basic Usage

### Initialize Client

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")
```

### Create a Task

::: code-group

```python [Sync]
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

task = client.tasks.create(
    search_query="When is the iPhone 17 being released?",  # [!code highlight]
    condition_description="Apple has announced a specific release date",  # [!code highlight]
    schedule="0 9 * * *"  # Daily at 9 AM
)

print(f"Created: {task.id}")
```

```python [Async]
from torale import AsyncToraleClient
import asyncio

async def create_task():
    client = AsyncToraleClient(api_key="sk_...")

    task = await client.tasks.create(
        search_query="When is the iPhone 17 being released?",  # [!code highlight]
        condition_description="Apple has announced a specific release date",  # [!code highlight]
        schedule="0 9 * * *"  # Daily at 9 AM
    )

    print(f"Created: {task.id}")

asyncio.run(create_task())
```

:::

::: tip Preview First
Use `client.tasks.preview()` to test your query before creating a task.
:::

### Preview Before Creating

```python
# Test query without creating task
preview = client.tasks.preview(
    search_query="When is the next iPhone release?",
    condition_description="A specific date has been announced"
)

print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")
print(f"Sources: {len(preview.grounding_sources)}")

# Create if results look good
if preview.condition_met:
    task = client.tasks.create(
        search_query="When is the next iPhone release?",
        condition_description="A specific date has been announced",
        schedule="0 9 * * *"
    )
```

### List Tasks

```python
# Get all tasks
tasks = client.tasks.list()

for task in tasks:
    print(f"{task.name}: {task.is_active}")

# Filter active tasks only
active_tasks = client.tasks.list(active=True)
```

### Get Task Details

```python
task = client.tasks.get("task-id")

print(f"Name: {task.name}")
print(f"Query: {task.search_query}")
print(f"Condition: {task.condition_description}")
print(f"Schedule: {task.schedule}")
print(f"Active: {task.is_active}")
```

### Update Task

```python
# Update schedule
task = client.tasks.update(
    "task-id",
    schedule="0 */6 * * *"  # Every 6 hours
)

# Pause task
task = client.tasks.update(
    "task-id",
    is_active=False
)

# Change notification behavior
task = client.tasks.update(
    "task-id",
    notify_behavior="track_state"
)
```

### Delete Task

```python
client.tasks.delete("task-id")
print("Task deleted")
```

### View Executions

```python
# Get execution history
executions = client.tasks.get_executions("task-id")

for execution in executions:
    print(f"Status: {execution.status}")
    print(f"Condition met: {execution.condition_met}")
    if execution.result:
        print(f"Answer: {execution.result.get('answer')}")
    print("---")
```

### View Notifications

```python
# Get notifications (condition_met = true only)
notifications = client.tasks.get_notifications("task-id")

for notif in notifications:
    print(f"Time: {notif.created_at}")
    print(f"Answer: {notif.answer}")
    print(f"Sources: {len(notif.grounding_sources)}")
```

## Complete Example

```python
from torale import ToraleClient

# Initialize
client = ToraleClient(api_key="sk_...")

# Preview query
preview = client.tasks.preview(
    search_query="What is the current price of PS5 at Best Buy?",
    condition_description="Price is $449 or lower"
)

print(f"Preview - Condition met: {preview.condition_met}")
print(f"Preview - Answer: {preview.answer}")

# Create task if preview looks good
task = client.tasks.create(
    name="PS5 Price Tracker",
    search_query="What is the current price of PS5 at Best Buy?",
    condition_description="Price is $449 or lower",
    schedule="0 */4 * * *",  # Every 4 hours
    notify_behavior="always",
    run_immediately=True  # Execute right away
)

print(f"\nCreated task: {task.id}")
print(f"Active: {task.is_active}")

# Check execution status after a moment
import time
time.sleep(5)

executions = client.tasks.get_executions(task.id, limit=1)
if executions:
    latest = executions[0]
    print(f"\nLatest execution status: {latest.status}")
    if latest.condition_met:
        print(f"Condition met! {latest.result.get('answer')}")
    else:
        print("Condition not yet met")

# List all tasks
print("\nAll tasks:")
for t in client.tasks.list():
    print(f"- {t.name}: {'active' if t.is_active else 'paused'}")
```

## Environment Variables

```python
import os
from torale import ToraleClient

# Set environment variable
os.environ["TORALE_API_KEY"] = "sk_..."

# Client reads from environment
client = ToraleClient()  # No api_key needed
```

Or use `.env` file:

```bash
# .env
TORALE_API_KEY=sk_...
```

```python
from dotenv import load_dotenv
from torale import ToraleClient

load_dotenv()  # Load .env file
client = ToraleClient()  # Reads from environment
```

## Error Handling

```python
from torale import ToraleClient
from torale.exceptions import (
    ValidationError,
    NotFoundError,
    RateLimitError
)

client = ToraleClient(api_key="sk_...")

try:
    task = client.tasks.create(
        search_query="...",
        condition_description="...",
        schedule="invalid"  # Bad cron
    )
except ValidationError as e:
    print(f"Validation error: {e.detail}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except NotFoundError:
    print("Task not found")
```

## Using with FastAPI

```python
from fastapi import FastAPI, Depends
from torale import ToraleClient
import os

app = FastAPI()

def get_torale_client():
    return ToraleClient(api_key=os.getenv("TORALE_API_KEY"))

@app.post("/create-monitor")
async def create_monitor(
    query: str,
    condition: str,
    client: ToraleClient = Depends(get_torale_client)
):
    task = client.tasks.create(
        search_query=query,
        condition_description=condition,
        schedule="0 9 * * *"
    )
    return {"task_id": task.id}

@app.get("/tasks")
async def list_tasks(
    client: ToraleClient = Depends(get_torale_client)
):
    tasks = client.tasks.list()
    return {"tasks": [t.dict() for t in tasks]}
```

## Next Steps

- Learn about [Async Client](/sdk/async)
- View more [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
- Read [API Reference](/api/tasks)
