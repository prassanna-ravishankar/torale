---
description: Python SDK guide for programmatic Torale integration. Create tasks, manage executions, and build automated monitoring workflows in your applications.
---

# Python SDK

Integrate Torale into your Python applications.

## Installation

```bash
pip install torale
```

## Get API Key

1. Log in to [torale.ai](https://torale.ai)
2. Go to Settings → API Keys
3. Generate new key
4. Copy and save securely

## Create Your First Task

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

task = client.tasks.create(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
    schedule="0 9 * * *"
)

print(f"Created task: {task.id}")
```

## Preview Before Creating

```python
# Test your query first
preview = client.tasks.preview(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date"
)

print(f"Condition met: {preview.condition_met}")
print(f"Answer: {preview.answer}")

# Create if results look good
if preview.condition_met:
    task = client.tasks.create(
        search_query="When is the iPhone 17 being released?",
        condition_description="Apple has announced a specific release date",
        schedule="0 9 * * *"
    )
```

## Check Results

```python
# Get execution history
executions = client.tasks.get_executions(task.id)

for execution in executions:
    if execution.condition_met:
        print(f"Answer: {execution.result['answer']}")
        print(f"Sources: {execution.grounding_sources}")
```

## Environment Variables

Store your API key in an environment variable:

```bash
export TORALE_API_KEY=sk_...
```

```python
from torale import ToraleClient

# Client automatically reads from environment
client = ToraleClient()
```

## Async Client

For async applications:

```python
from torale import AsyncToraleClient
import asyncio

async def main():
    client = AsyncToraleClient(api_key="sk_...")

    task = await client.tasks.create(
        search_query="When is the iPhone 17 being released?",
        condition_description="Apple has announced a specific release date",
        schedule="0 9 * * *"
    )

    print(f"Created: {task.id}")

asyncio.run(main())
```

## Next Steps

- Read the [SDK Quickstart](/sdk/quickstart) for detailed examples
- Learn about [Async Client](/sdk/async)
- View [Error Handling](/sdk/errors)
