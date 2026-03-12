---
layout: home
description: Torale developer documentation. API reference and Python SDK for building with grounded search monitoring.

hero:
  name: Torale Docs
  text: Developer Documentation
  tagline: Build with grounded search monitoring
  image:
    src: /logo.svg
    alt: Torale
  actions:
    - theme: brand
      text: Quickstart
      link: /getting-started/
    - theme: alt
      text: API Reference
      link: /api/overview
---

## Overview

Torale executes scheduled web searches, evaluates results against trigger conditions, and stores execution history. Grounded search combines Google Search with LLM evaluation for source-backed monitoring.

## Example

```python
from torale import ToraleClient

client = ToraleClient()

# Create a monitoring task
task = client.tasks.create(
    search_query="When is the iPhone 17 being released?",
    condition_description="Apple has announced a specific release date",
    schedule="0 9 * * *"  # Daily at 9 AM
)

# Check results
executions = client.tasks.get_executions(task.id)
if executions[0].condition_met:
    print(executions[0].result["answer"])
```

## Interfaces

- [Python SDK](/getting-started/sdk) - Client library for Python applications
- [REST API](/api/overview) - API reference
