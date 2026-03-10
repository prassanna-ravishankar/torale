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
from torale import ToraleAsync

async def main():
    async with ToraleAsync(api_key="sk_...") as client:
        task = await client.tasks.create(
            name="iPhone Release Monitor",
            search_query="When is the next iPhone release?",
            condition_description="A specific date has been announced",
        )
        print(f"Created: {task.id}")

asyncio.run(main())
```

The `ToraleAsync` client supports the same resources and methods as the sync `Torale` client, with `await` on every call.

## Context Manager

Always use `async with` to ensure the HTTP client is closed properly:

```python
async with ToraleAsync(api_key="sk_...") as client:
    tasks = await client.tasks.list()
```

Or close manually:

```python
client = ToraleAsync(api_key="sk_...")
try:
    tasks = await client.tasks.list()
finally:
    await client.close()
```

## Concurrent Operations

### Create Multiple Tasks

```python
async def create_tasks():
    async with ToraleAsync(api_key="sk_...") as client:
        tasks = await asyncio.gather(
            client.tasks.create(
                name="iPhone Monitor",
                search_query="iPhone release date?",
                condition_description="Date announced",
            ),
            client.tasks.create(
                name="PS5 Stock Monitor",
                search_query="PS5 in stock at Target?",
                condition_description="Available for purchase",
            ),
            client.tasks.create(
                name="MacBook Price Monitor",
                search_query="MacBook Pro price at Best Buy?",
                condition_description="Price below $1800",
            ),
        )

        for task in tasks:
            print(f"Created: {task.name}")

asyncio.run(create_tasks())
```

### Fetch Multiple Task Details

```python
async def get_task_details(task_ids):
    async with ToraleAsync(api_key="sk_...") as client:
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

## Available Methods

`ToraleAsync` has the same interface as the sync client. All methods are async:

| Resource | Method | Description |
|----------|--------|-------------|
| `client.tasks` | `create(...)` | Create a task |
| `client.tasks` | `list(active=...)` | List tasks |
| `client.tasks` | `get(task_id)` | Get a task |
| `client.tasks` | `update(task_id, ...)` | Update a task |
| `client.tasks` | `delete(task_id)` | Delete a task |
| `client.tasks` | `execute(task_id)` | Trigger manual execution |
| `client.tasks` | `executions(task_id, limit=100)` | Get execution history |
| `client.tasks` | `notifications(task_id, limit=100)` | Get notifications |
| `client.webhooks` | `get_config()` | Get webhook config |
| `client.webhooks` | `update_config(url=..., enabled=...)` | Update webhook config |
| `client.webhooks` | `test(url, secret)` | Test webhook delivery |
| `client.webhooks` | `list_deliveries(task_id=..., limit=...)` | List webhook deliveries |

## With FastAPI

```python
import os

from fastapi import FastAPI, Depends
from torale import ToraleAsync

app = FastAPI()

async def get_torale_client():
    client = ToraleAsync(api_key=os.getenv("TORALE_API_KEY"))
    try:
        yield client
    finally:
        await client.close()

@app.post("/create-task")
async def create_task(
    query: str,
    condition: str,
    client: ToraleAsync = Depends(get_torale_client),
):
    task = await client.tasks.create(
        name=f"Monitor: {query[:50]}",
        search_query=query,
        condition_description=condition,
    )
    return {"task_id": str(task.id)}

@app.get("/tasks")
async def list_tasks(
    client: ToraleAsync = Depends(get_torale_client),
):
    tasks = await client.tasks.list()
    return {"tasks": [t.model_dump() for t in tasks]}

@app.get("/tasks/{task_id}/executions")
async def get_executions(
    task_id: str,
    client: ToraleAsync = Depends(get_torale_client),
):
    executions = await client.tasks.executions(task_id)
    return {"executions": [e.model_dump() for e in executions]}
```

## Batch Operations with Rate Limiting

```python
from asyncio import Semaphore

async def create_tasks_with_limit(task_configs):
    async with ToraleAsync(api_key="sk_...") as client:
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

## Error Handling

```python
from torale import ToraleAsync
from torale.sdk.exceptions import ValidationError, RateLimitError, APIError
import asyncio

async def safe_create_task(client, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return await client.tasks.create(**kwargs)
        except ValidationError as e:
            print(f"Validation error: {e}")
            raise  # Don't retry validation errors
        except APIError as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"API error, retrying in {wait}s...")
            await asyncio.sleep(wait)

async def main():
    async with ToraleAsync(api_key="sk_...") as client:
        task = await safe_create_task(
            client,
            name="My Monitor",
            search_query="...",
            condition_description="...",
        )

asyncio.run(main())
```

## Next Steps

- View [Examples](/sdk/examples)
- Handle [Errors](/sdk/errors)
- Read [API Reference](/api/tasks)
