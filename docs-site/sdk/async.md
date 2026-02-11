---
description: Use async/await patterns with Torale Python SDK. Async task management, concurrent execution monitoring, and asynchronous notification handling.
---

# Async Client

Use Torale SDK with asyncio for concurrent operations.

## Installation

Same package, async client included:

```bash
pip install torale
```

## Basic Usage

```python
import asyncio
from torale import AsyncToraleClient

async def main():
    client = AsyncToraleClient(api_key="sk_...")

    # Create task
    task = await client.tasks.create(
        search_query="When is the next iPhone release?",
        condition_description="A specific date has been announced",
        schedule="0 9 * * *"
    )

    print(f"Created: {task.id}")

asyncio.run(main())
```

## Concurrent Operations

### Create Multiple Tasks

```python
async def create_tasks():
    client = AsyncToraleClient(api_key="sk_...")

    # Create tasks concurrently
    tasks = await asyncio.gather(
        client.tasks.create(
            search_query="iPhone release date?",
            condition_description="Date announced",
            schedule="0 9 * * *"
        ),
        client.tasks.create(
            search_query="PS5 in stock at Target?",
            condition_description="Available for purchase",
            schedule="0 */2 * * *"
        ),
        client.tasks.create(
            search_query="MacBook Pro price at Best Buy?",
            condition_description="Price below $1800",
            schedule="0 */4 * * *"
        )
    )

    for task in tasks:
        print(f"Created: {task.name}")

asyncio.run(create_tasks())
```

### Fetch Multiple Task Details

```python
async def get_task_details(task_ids):
    client = AsyncToraleClient(api_key="sk_...")

    # Fetch concurrently
    tasks = await asyncio.gather(*[
        client.tasks.get(task_id)
        for task_id in task_ids
    ])

    return tasks

task_ids = ["task-id-1", "task-id-2", "task-id-3"]
tasks = asyncio.run(get_task_details(task_ids))

for task in tasks:
    print(f"{task.name}: {task.state}")
```

## With FastAPI

```python
from fastapi import FastAPI, Depends
from torale import AsyncToraleClient
import os

app = FastAPI()

async def get_torale_client():
    return AsyncToraleClient(api_key=os.getenv("TORALE_API_KEY"))

@app.post("/create-task")
async def create_task(
    query: str,
    condition: str,
    client: AsyncToraleClient = Depends(get_torale_client)
):
    task = await client.tasks.create(
        search_query=query,
        condition_description=condition,
        schedule="0 9 * * *"
    )
    return {"task_id": task.id}

@app.get("/tasks")
async def list_tasks(
    client: AsyncToraleClient = Depends(get_torale_client)
):
    tasks = await client.tasks.list()
    return {"tasks": [t.dict() for t in tasks]}

@app.get("/tasks/{task_id}/executions")
async def get_executions(
    task_id: str,
    client: AsyncToraleClient = Depends(get_torale_client)
):
    executions = await client.tasks.get_executions(task_id)
    return {"executions": [e.dict() for e in executions]}
```

## Error Handling

```python
from torale import AsyncToraleClient
from torale.exceptions import ValidationError, RateLimitError
import asyncio

async def safe_create_task(client, **kwargs):
    try:
        return await client.tasks.create(**kwargs)
    except ValidationError as e:
        print(f"Validation error: {e.detail}")
    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s")
        await asyncio.sleep(e.retry_after)
        return await client.tasks.create(**kwargs)

async def main():
    client = AsyncToraleClient(api_key="sk_...")

    task = await safe_create_task(
        client,
        search_query="...",
        condition_description="...",
        schedule="0 9 * * *"
    )

asyncio.run(main())
```

## Batch Operations

```python
async def batch_update_tasks(task_ids, updates):
    """Update multiple tasks concurrently"""
    client = AsyncToraleClient(api_key="sk_...")

    tasks = await asyncio.gather(*[
        client.tasks.update(task_id, **updates)
        for task_id in task_ids
    ])

    return tasks

# Pause multiple tasks
task_ids = ["task-1", "task-2", "task-3"]
updated_tasks = asyncio.run(
    batch_update_tasks(task_ids, {"is_active": False})
)

print(f"Paused {len(updated_tasks)} tasks")
```

## Context Manager

```python
async def main():
    async with AsyncToraleClient(api_key="sk_...") as client:
        task = await client.tasks.create(
            search_query="...",
            condition_description="...",
            schedule="0 9 * * *"
        )
        print(f"Created: {task.id}")

asyncio.run(main())
```

## Best Practices

### 1. Use for I/O-bound Operations

```python
# ✓ Good - Concurrent API calls
tasks = await asyncio.gather(
    client.tasks.get("task-1"),
    client.tasks.get("task-2"),
    client.tasks.get("task-3")
)

# ✗ Bad - Sequential (slower)
task1 = await client.tasks.get("task-1")
task2 = await client.tasks.get("task-2")
task3 = await client.tasks.get("task-3")
```

### 2. Handle Rate Limits

```python
from asyncio import Semaphore

async def create_tasks_with_limit(task_configs):
    client = AsyncToraleClient(api_key="sk_...")
    semaphore = Semaphore(5)  # Max 5 concurrent requests

    async def create_with_semaphore(config):
        async with semaphore:
            return await client.tasks.create(**config)

    tasks = await asyncio.gather(*[
        create_with_semaphore(config)
        for config in task_configs
    ])

    return tasks
```

### 3. Retry Logic

```python
from asyncio import sleep

async def create_task_with_retry(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return await client.tasks.create(**kwargs)
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            await sleep(e.retry_after or 2 ** attempt)
```

## Next Steps

- View [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
- Read [API Reference](/api/tasks)
