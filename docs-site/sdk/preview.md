---
description: Preview Torale SDK features before deployment. Test task configurations, validate conditions, and preview execution behavior locally.
---

# Preview

Test search queries before creating tasks.

## Basic Preview

```python
preview = client.tasks.preview(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date"
)

print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")
```

## With Full Results

```python
preview = client.tasks.preview(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date"
)

print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")
print(f"Reasoning: {preview.reasoning}")
print(f"Sources: {len(preview.grounding_sources)}")

for source in preview.grounding_sources:
    print(f"- {source['uri']}")
```

## Create Based on Preview

```python
# Preview first
preview = client.tasks.preview(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date"
)

# Create if satisfied with results
if preview.condition_met:
    task = client.tasks.create(
        search_query="When is the iPhone 17 being released?",
        condition_description="Apple has announced a specific release date",
        schedule="0 9 * * *"
    )
    print(f"Created: {task.id}")
else:
    print("Condition not yet met. Will create task anyway to monitor.")
    task = client.tasks.create(...)
```

## Async Preview

```python
from torale import AsyncToraleClient
import asyncio

async def preview_task():
    client = AsyncToraleClient(api_key="sk_...")

    preview = await client.tasks.preview(
        search_query="When is the iPhone 17 being released?",
        condition_description="Apple has announced a specific release date"
    )

    return preview

result = asyncio.run(preview_task())
print(result.answer)
```

## Next Steps

- Create tasks with [Tasks API](/sdk/tasks)
- Use [Async Client](/sdk/async)
- Read [Quickstart Guide](/sdk/quickstart)
