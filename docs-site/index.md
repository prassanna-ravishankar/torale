---
layout: home

hero:
  name: Torale Docs
  text: Technical Documentation
  tagline: Grounded search monitoring platform
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

## Architecture

```mermaid
---
config:
  look: neo
  theme: base
---
flowchart LR
    A[Task]
    B[Temporal]
    C[Search]
    D[Evaluate]
    E[Store]

    A --> B --> C --> D --> E
```

**Core Components:**
- **Grounded Search**: Google Search API via Gemini LLM with source attribution
- **Temporal Workflows**: Cron-based scheduling with automatic retries and state management
- **State Tracking**: Detects changes between executions to prevent duplicate notifications
- **Condition Evaluation**: LLM-based determination of trigger condition status

## Interfaces

- [Web Dashboard](/getting-started/web-dashboard) - Browser-based task management
- [CLI](/getting-started/cli) - Command-line interface
- [Python SDK](/getting-started/sdk) - Programmatic access
- [API](/api/overview) - REST API reference
- [Self-Hosted](/getting-started/self-hosted) - Deploy on your infrastructure
