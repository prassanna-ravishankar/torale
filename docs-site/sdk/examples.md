---
description: Torale Python SDK code examples. Real-world monitoring scenarios with complete code samples for common use cases and integration patterns.
---

# Examples

Practical examples using the Torale Python SDK.

## Product Release Monitoring

```python
from torale import ToraleClient

client = ToraleClient(api_key="sk_...")

# Monitor iPhone release
iphone_task = client.tasks.create(
    name="iPhone 16 Release Monitor",
    search_query="When is the iPhone 16 being released?",
    condition_description="Apple has officially announced a specific release date",
    schedule="0 9 * * *",  # Daily at 9 AM
    notify_behavior="once"
)

# Monitor GPT-5 release
gpt5_task = client.tasks.create(
    name="GPT-5 Release Monitor",
    search_query="When is GPT-5 being released by OpenAI?",
    condition_description="OpenAI has announced an official release date",
    schedule="0 */6 * * *",  # Every 6 hours
    notify_behavior="once"
)

print(f"Monitoring {len([iphone_task, gpt5_task])} product releases")
```

## Price Tracking

```python
# Track MacBook price
macbook_task = client.tasks.create(
    name="MacBook Pro Price Alert - Best Buy",
    search_query="What is the current price of MacBook Pro M3 14-inch at Best Buy?",
    condition_description="The price is $1799 or lower",
    schedule="0 */4 * * *",  # Every 4 hours
    notify_behavior="always"  # Want every occurrence
)

# Track PS5 price
ps5_task = client.tasks.create(
    name="PS5 Price Tracker",
    search_query="What is the current price of PS5 at Amazon?",
    condition_description="Price is $449 or lower",
    schedule="0 */6 * * *",
    notify_behavior="always"
)
```

## Stock Availability

```python
# Monitor PS5 stock
ps5_stock = client.tasks.create(
    name="PS5 Stock Alert - Target",
    search_query="Is PlayStation 5 in stock at Target?",
    condition_description="PS5 is currently available for purchase",
    schedule="0 */2 * * *",  # Every 2 hours
    notify_behavior="once"  # Buy once, then pause
)

# Check immediately
client.tasks.execute(ps5_stock.id)
```

## News Monitoring

```python
# Track AI regulation
ai_regulation = client.tasks.create(
    name="AI Regulation Monitor",
    search_query="What is the latest on California AI regulation SB-1047?",
    condition_description="New developments or official updates have been announced",
    schedule="0 9 * * *",  # Daily at 9 AM
    notify_behavior="always"  # Notify on every match
)
```

## Bulk Task Creation

```python
# Create multiple monitoring tasks
queries = [
    {
        "name": "iPhone Release",
        "query": "When is the next iPhone being released?",
        "condition": "A specific date has been announced"
    },
    {
        "name": "PS5 Stock",
        "query": "Is PS5 in stock at Best Buy?",
        "condition": "PS5 is available for purchase"
    },
    {
        "name": "MacBook Price",
        "query": "What is the MacBook Pro M3 price at Best Buy?",
        "condition": "Price is below $1800"
    }
]

tasks = []
for config in queries:
    task = client.tasks.create(
        name=config["name"],
        search_query=config["query"],
        condition_description=config["condition"],
        schedule="0 9 * * *"
    )
    tasks.append(task)
    print(f"Created: {task.name}")

print(f"\nTotal tasks created: {len(tasks)}")
```

## Task Management Dashboard

```python
from torale import ToraleClient
from datetime import datetime

client = ToraleClient(api_key="sk_...")

def display_dashboard():
    """Display task monitoring dashboard"""
    tasks = client.tasks.list()

    print("=" * 60)
    print("TORALE MONITORING DASHBOARD")
    print("=" * 60)

    # Summary
    active = sum(1 for t in tasks if t.state == "active")
    met_condition = sum(1 for t in tasks if t.condition_met)

    print(f"\nTotal Tasks: {len(tasks)}")
    print(f"Active: {active}")
    print(f"Paused: {len(tasks) - active}")
    print(f"Conditions Met: {met_condition}")

    # Task list
    print("\n" + "=" * 60)
    print("TASKS")
    print("=" * 60)

    for task in tasks:
        status = "✓ ACTIVE" if task.state == "active" else "⏸ PAUSED"
        condition = "✓ MET" if task.condition_met else "⏳ WAITING"

        print(f"\n{task.name}")
        print(f"  Status: {status}")
        print(f"  Condition: {condition}")
        print(f"  Schedule: {task.schedule}")

        # Get latest execution
        executions = client.tasks.get_executions(task.id, limit=1)
        if executions:
            latest = executions[0]
            print(f"  Last run: {latest.created_at}")
            print(f"  Duration: {latest.completed_at - latest.started_at if latest.completed_at else 'N/A'}")

    print("\n" + "=" * 60)

display_dashboard()
```

## Notification Checker

```python
def check_notifications():
    """Check for new notifications"""
    tasks = client.tasks.list()

    print("Checking notifications...\n")

    for task in tasks:
        notifications = client.tasks.get_notifications(task.id, limit=5)

        if notifications:
            print(f"📬 {task.name}: {len(notifications)} notifications")

            for notif in notifications[:3]:  # Show latest 3
                print(f"  • {notif.created_at}: {notif.answer[:100]}...")

            print()
        else:
            print(f"   {task.name}: No notifications")

check_notifications()
```

## Automated Task Cleanup

```python
from datetime import datetime, timedelta

def cleanup_old_tasks():
    """Pause tasks that haven't triggered in 30 days"""
    tasks = client.tasks.list(active=True)
    thirty_days_ago = datetime.now() - timedelta(days=30)

    paused_count = 0

    for task in tasks:
        # Check last execution
        executions = client.tasks.get_executions(task.id, limit=1)

        if executions:
            latest = executions[0]
            if datetime.fromisoformat(latest.created_at.replace('Z', '+00:00')) < thirty_days_ago:
                # Pause task
                client.tasks.update(task.id, state="paused")
                print(f"Paused: {task.name} (inactive for 30+ days)")
                paused_count += 1

    print(f"\nPaused {paused_count} tasks")

cleanup_old_tasks()
```

## Preview Before Creating

```python
# Preview multiple queries
queries_to_test = [
    {
        "query": "When is the next iPhone release?",
        "condition": "A specific date has been announced"
    },
    {
        "query": "Is PS5 in stock at Best Buy?",
        "condition": "PS5 is available"
    }
]

print("Previewing queries...\n")

for config in queries_to_test:
    preview = client.tasks.preview(
        search_query=config["query"],
        condition_description=config["condition"]
    )

    print(f"Query: {config['query']}")
    print(f"Condition met: {preview.condition_met}")
    print(f"Answer: {preview.answer}")
    print(f"Sources: {len(preview.grounding_sources)}")
    print("-" * 60)

    # Create task if condition met
    if preview.condition_met:
        task = client.tasks.create(
            search_query=config["query"],
            condition_description=config["condition"],
            schedule="0 9 * * *"
        )
        print(f"✓ Created task: {task.id}\n")
```

## Execution Monitoring

```python
def monitor_execution_health():
    """Monitor execution success rates"""
    tasks = client.tasks.list()

    print("Execution Health Report\n")
    print("=" * 60)

    for task in tasks:
        executions = client.tasks.get_executions(task.id, limit=20)

        if not executions:
            continue

        total = len(executions)
        success = sum(1 for e in executions if e.status == "success")
        failed = sum(1 for e in executions if e.status == "failed")
        condition_met = sum(1 for e in executions if e.condition_met)

        success_rate = (success / total) * 100 if total > 0 else 0

        print(f"\n{task.name}")
        print(f"  Total executions: {total}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Failed: {failed}")
        print(f"  Condition met: {condition_met}")

        if failed > 0:
            print("  ⚠️  Has failures - check error logs")

    print("\n" + "=" * 60)

monitor_execution_health()
```

## Next Steps

- Handle [Errors](/sdk/errors)
- Learn about [Async Client](/sdk/async)
- Read [API Reference](/api/tasks)
