---
description: Torale Python SDK quickstart guide. Install the SDK, authenticate, and create monitoring tasks programmatically in minutes with code examples.
---

# Quickstart

Get started with the Torale Python SDK in minutes.

## Installation

```bash
pip install torale
```

## Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Navigate to Settings -> API Keys
3. Generate new key
4. Copy key (shown only once)

## Basic Usage

### Initialize Client

```python
from torale import Torale

client = Torale(api_key="sk_...")
```

### Create a Task

::: code-group

```python [Sync]
from torale import Torale

client = Torale(api_key="sk_...")

task = client.tasks.create(
    name="iPhone Release Monitor",                                     # [!code highlight]
    search_query="When is the iPhone 17 being released?",              # [!code highlight]
    condition_description="Apple has announced a specific release date" # [!code highlight]
)

print(f"Created: {task.id}")
```

```python [Async]
import asyncio
from torale import ToraleAsync

async def create_task():
    async with ToraleAsync(api_key="sk_...") as client:
        task = await client.tasks.create(
            name="iPhone Release Monitor",                                     # [!code highlight]
            search_query="When is the iPhone 17 being released?",              # [!code highlight]
            condition_description="Apple has announced a specific release date" # [!code highlight]
        )
        print(f"Created: {task.id}")

asyncio.run(create_task())
```

:::

### Fluent Builder API

The SDK provides a fluent builder for a more readable syntax:

```python
from torale import Torale

client = Torale(api_key="sk_...")

task = (client.monitor("When is the iPhone 17 being released?")
    .when("Apple has announced a specific release date")
    .notify(email="me@example.com", webhook="https://myapp.com/alert")
    .named("iPhone Release Monitor")
    .create())
```

Or use the standalone `monitor()` function (creates a default client automatically):

```python
from torale import monitor

task = (monitor("When is the iPhone 17 being released?")
    .when("Apple has announced a specific release date")
    .notify(webhook="https://myapp.com/alert")
    .create())
```

### List Tasks

```python
# Get all tasks
tasks = client.tasks.list()

for task in tasks:
    print(f"{task.name}: {task.state}")

# Filter active tasks only
active_tasks = client.tasks.list(active=True)
```

### Get Task Details

```python
task = client.tasks.get("task-id")

print(f"Name: {task.name}")
print(f"Query: {task.search_query}")
print(f"Condition: {task.condition_description}")
print(f"State: {task.state}")
```

### Update Task

```python
# Pause task
task = client.tasks.update("task-id", state="paused")

# Update search query
task = client.tasks.update("task-id", search_query="New search query")
```

### Delete Task

```python
client.tasks.delete("task-id")
```

### Trigger Manual Execution

```python
execution = client.tasks.execute("task-id")
print(f"Status: {execution.status}")
```

### View Executions

```python
executions = client.tasks.executions("task-id")

for execution in executions:
    print(f"Status: {execution.status}")
    print(f"Started: {execution.started_at}")
    if execution.notification:
        print(f"Notification: {execution.notification}")
```

### View Notifications

```python
# Get only executions where condition was met
notifications = client.tasks.notifications("task-id")

for notif in notifications:
    print(f"Time: {notif.started_at}")
    print(f"Notification: {notif.notification}")
```

## Complete Example

```python
from torale import Torale

# Initialize
client = Torale(api_key="sk_...")

# Create task
task = client.tasks.create(
    name="PS5 Price Tracker",
    search_query="What is the current price of PS5 at Best Buy?",
    condition_description="Price is $449 or lower",
    notifications=[{"type": "webhook", "url": "https://myapp.com/alert"}],
)

print(f"Created task: {task.id}")
print(f"State: {task.state}")

# Trigger a manual execution
execution = client.tasks.execute(task.id)
print(f"Execution status: {execution.status}")

# Check execution history
executions = client.tasks.executions(task.id, limit=5)
for ex in executions:
    print(f"  {ex.started_at}: {ex.status}")

# List all tasks
print("\nAll tasks:")
for t in client.tasks.list():
    print(f"  - {t.name}: {t.state}")
```

## Environment Variables

```python
import os
from torale import Torale

# Set environment variable
os.environ["TORALE_API_KEY"] = "sk_..."

# Client reads from environment
client = Torale()  # No api_key needed
```

Or use `.env` file:

```bash
# .env
TORALE_API_KEY=sk_...
```

```python
from dotenv import load_dotenv
from torale import Torale

load_dotenv()
client = Torale()
```

## Error Handling

```python
from torale import Torale
from torale.sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
)

client = Torale(api_key="sk_...")

try:
    task = client.tasks.create(
        name="My Monitor",
        search_query="...",
        condition_description="...",
    )
except ValidationError as e:
    print(f"Validation error: {e}")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Resource not found")
```

## Next Steps

- Learn about [Async Client](/sdk/async)
- View more [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
- Read [API Reference](/api/tasks)
