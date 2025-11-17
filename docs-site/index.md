---
layout: home

hero:
  name: Torale
  text: Automated Web Monitoring
  tagline: Monitor the web. Get notified when it matters.
  image:
    src: /logo.svg
    alt: Torale
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started/
    - theme: alt
      text: Try Torale
      link: https://torale.ai

features:
  - title: Grounded Search
    details: Search the web with real-time results from Google Search, evaluated by LLMs for accurate, source-backed answers.

  - title: Intelligent Conditions
    details: Define specific trigger conditions in natural language. The system evaluates search results and determines when your criteria are met.

  - title: Automated Scheduling
    details: Configure when checks run using cron expressions. Temporal workflows handle execution, retries, and error recovery automatically.

  - title: State Tracking
    details: Compare results over time to detect meaningful changes. Get notified once when conditions are met, not repeatedly for the same information.
---

## What is Torale?

Torale automates web monitoring by executing scheduled searches, evaluating results against your conditions, and sending notifications when conditions are met. Instead of manually checking websites for updates, you create monitoring tasks that handle the search, evaluation, and notification process automatically.

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

## Use Cases

**Product Launch Monitoring** - Get notified when companies announce release dates for new products you're interested in.

**Price Tracking** - Monitor price changes across retailers and get alerted when items drop below your target price.

**Stock Availability** - Track when out-of-stock items become available for purchase.

**Event & Ticketing** - Know immediately when tickets go on sale for concerts, sports events, or festivals.

## How It Works

Torale combines four core capabilities to automate web monitoring:

**Grounded Search** uses Google Search to find current information on the web, with LLM-powered answer extraction that provides concise, source-backed responses.

**Intelligent Conditions** evaluate whether your specific trigger criteria have been met. The system understands natural language conditions and makes intelligent determinations based on search results.

**Automated Scheduling** runs your tasks on configurable cron schedules. Temporal workflows handle execution timing, automatic retries on failures, and durable state management across system restarts.

**State Tracking** compares current results with previous executions to identify meaningful changes. This prevents duplicate notifications when information hasn't actually changed.

## Get Started

Choose your preferred method:

- [Web Dashboard](/getting-started/web-dashboard) - Sign up at torale.ai and create tasks through the UI
- [CLI](/getting-started/cli) - Install the command-line tool for terminal-based task management
- [Python SDK](/getting-started/sdk) - Integrate monitoring into your Python applications
- [Self-Hosted](/getting-started/self-hosted) - Run Torale on your own infrastructure
