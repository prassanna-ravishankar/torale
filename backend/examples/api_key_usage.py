#!/usr/bin/env python3
"""
Torale API Key Usage Examples

This file demonstrates how to authenticate and use the Torale SDK with API keys.

Prerequisites:
1. Generate an API key from the Torale web dashboard (Settings > API Access)
2. Add the API key to your root .env file: TORALE_API_KEY=sk_...
3. Install the SDK: pip install torale (or use uv in this repo)

Run this file:
    python backend/examples/api_key_usage.py --local  # Use local dev server
    python backend/examples/api_key_usage.py          # Use production API
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv

# Parse args BEFORE loading SDK to set environment correctly
parser = argparse.ArgumentParser(description="Torale SDK API Key Usage Examples")
parser.add_argument(
    "--local",
    action="store_true",
    help="Use local dev server (http://localhost:8000) instead of production API",
)
parser.add_argument(
    "--webhook-url",
    type=str,
    help="Webhook URL to configure and test (e.g., https://webhook.site/unique-id)",
)
parser.add_argument(
    "--webhook-secret",
    type=str,
    help="Webhook secret for testing (optional, will use saved config if not provided)",
)
args = parser.parse_args()

# Set dev mode BEFORE importing SDK
if args.local:
    os.environ["TORALE_DEV"] = "1"

# Load environment variables from root .env file
load_dotenv()

# ruff: noqa: E402
# SDK must be imported AFTER setting TORALE_DEV environment variable
from torale.sdk import Torale, ToraleAsync
from torale.sdk.exceptions import AuthenticationError


def example_1_env_variable():
    """
    Method 1: Authentication via Environment Variable (RECOMMENDED)

    This is the recommended approach for production use.
    Add TORALE_API_KEY=sk_... to your .env file or environment.
    """
    print("\n=== Example 1: Authentication via Environment Variable ===")

    # The SDK automatically reads TORALE_API_KEY from environment
    client = Torale()

    # List all tasks
    print("Fetching your monitoring tasks...")
    tasks = client.tasks.list()
    print(f"✓ Found {len(tasks)} task(s)")

    for task in tasks:
        status = "🟢 Active" if task.is_active else "⚪ Inactive"
        print(f"  {status} {task.name}")
        print(f"     ID: {task.id}")
        print(f"     Query: {task.search_query}")

    return client


def example_2_explicit_api_key():
    """
    Method 2: Explicit API Key in Code

    Useful for testing or when you need to use multiple API keys.
    NOT recommended for production - use environment variables instead.
    """
    print("\n=== Example 2: Explicit API Key ===")

    # Get API key from environment (in real code, you might hardcode for testing)
    api_key = os.getenv("TORALE_API_KEY")

    if not api_key:
        print("⚠️  TORALE_API_KEY not found in environment")
        return None

    # Pass API key explicitly
    client = Torale(api_key=api_key)
    print(f"✓ Authenticated with explicit key: {api_key[:20]}...")

    # Get task count
    tasks = client.tasks.list()
    print(f"✓ Found {len(tasks)} task(s)")

    return client


def example_3_cli_config():
    """
    Method 3: CLI Config File

    If you've run `torale auth set-api-key`, the SDK will automatically
    read the API key from ~/.torale/config.json
    """
    print("\n=== Example 3: CLI Config File ===")

    # First, remove TORALE_API_KEY from environment to test CLI config
    original_key = os.environ.pop("TORALE_API_KEY", None)

    try:
        client = Torale()
        tasks = client.tasks.list()
        print("✓ Authenticated via ~/.torale/config.json")
        print(f"✓ Found {len(tasks)} task(s)")
    except AuthenticationError:
        print("⚠️  CLI config not found or invalid. The SDK could not find an API key.")
        print("\nTo set up CLI config, run:")
        print("  torale auth set-api-key")
    finally:
        # Restore environment variable
        if original_key:
            os.environ["TORALE_API_KEY"] = original_key

    return None


def example_4_create_task():
    """
    Example: Create a monitoring task using the SDK
    """
    print("\n=== Example: Create a Monitoring Task ===\n")

    client = Torale()

    # Create a new monitoring task
    print("Creating task: 'iPhone 16 Release Monitor'...")
    task = client.tasks.create(
        name="iPhone 16 Release Monitor",
        search_query="When is iPhone 16 being released?",
        condition_description="A specific release date or month has been officially announced",
        schedule="0 9 * * *",  # Daily at 9 AM
        notify_behavior="once",  # Notify only once when condition is met
    )

    print("✓ Task created successfully!")
    print(f"\n  📝 Name: {task.name}")
    print(f"  🆔 ID: {task.id}")
    print(f"  ⏰ Schedule: {task.schedule} (Daily at 9 AM)")
    print(f"  🎯 Condition: {task.condition_description}")
    print(f"  🔔 Notify: {task.notify_behavior}")

    return task


def example_5_fluent_api():
    """
    Example: Use the fluent/builder API for cleaner task creation
    """
    print("\n=== Example: Fluent/Builder API ===\n")

    client = Torale()

    # Create task using fluent API
    print("Creating task with fluent API...")
    task = (
        client.monitor("Bitcoin price today")
        .when("Price exceeds $50,000")
        .check_every("0 */6 * * *")  # Every 6 hours
        .notify(behavior="once")  # Notify once when condition is met
        .create()
    )

    print("✓ Task created with fluent API!")
    print(f"\n  📝 Name: {task.name}")
    print(f"  🔍 Query: {task.search_query}")
    print(f"  🎯 Condition: {task.condition_description}")
    print("  ⏰ Schedule: Every 6 hours")

    return task


def example_6_task_webhooks():
    """
    Example: Create tasks with webhook notifications
    """
    print("\n=== Example: Task with Webhook Notifications ===\n")

    client = Torale()

    # Method 1: Direct API with webhook notification
    print("Creating task with webhook notification (Direct API)...")
    task = client.tasks.create(
        name="PS5 Stock Monitor",
        search_query="Is PS5 back in stock at Best Buy?",
        condition_description="PS5 is available for purchase",
        schedule="0 */2 * * *",  # Every 2 hours
        notifications=[{"type": "webhook", "url": "https://myapp.com/webhooks/ps5-alert"}],
    )

    print("✓ Task created with webhook!")
    print(f"\n  📝 Name: {task.name}")
    print("  🔔 Webhook: https://myapp.com/webhooks/ps5-alert")
    print("  ⏰ Schedule: Every 2 hours")

    # Method 2: Fluent API with webhook
    print("\n\nCreating task with webhook (Fluent API)...")
    task2 = (
        client.monitor("iPhone 16 Pro release date")
        .when("A specific release date is announced")
        .check_every("0 9 * * *")  # Daily at 9am
        .notify(webhook="https://myapp.com/webhooks/iphone")
        .create()
    )

    print("✓ Task created with fluent API!")
    print(f"\n  📝 Name: {task2.name}")
    print("  🔔 Webhook: https://myapp.com/webhooks/iphone")
    print("  ⏰ Schedule: Daily at 9am")


def example_7_task_operations():
    """
    Example: Common task operations (get, update, delete, execute)
    """
    print("\n=== Example: Task Operations ===\n")

    client = Torale()

    # List tasks
    tasks = client.tasks.list()
    if not tasks:
        print("⚠️  No tasks found. Create one first!")
        return

    task_id = tasks[0].id
    print(f"Working with task: {tasks[0].name}\n")

    # Get task details
    task = client.tasks.get(task_id)
    status_icon = "🟢" if task.is_active else "⚪"
    print(f"  {status_icon} Status: {'Active' if task.is_active else 'Inactive'}")
    print(f"  📅 Created: {task.created_at}")

    # Get task executions (history)
    executions = client.tasks.executions(task_id)
    print(f"  📊 Execution history: {len(executions)} execution(s)")

    # Manual execution (test the query)
    print("\n▶️  Executing task manually...")
    result = client.tasks.execute(task_id)
    print(f"  Status: {result.status}")
    if result.condition_met:
        print("  ✅ Condition MET!")
    else:
        print("  ⏳ Condition not met yet")


def example_8_webhook_management():
    """
    Example: Manage user-level webhook configuration

    Demonstrates setting up a default webhook URL for all task notifications,
    testing webhook delivery, and viewing delivery history.
    """
    print("\n=== Example: Webhook Configuration & Testing ===\n")

    client = Torale()

    # Get current webhook config
    print("Fetching current webhook configuration...")
    config = client.webhooks.get_config()
    print(f"  Current URL: {config['url'] or 'Not configured'}")
    print(f"  Enabled: {config['enabled']}")
    if config["secret"]:
        print(f"  Secret: {config['secret'][:16]}...")

    # If webhook URL provided via CLI, configure and test it
    if args.webhook_url:
        print(f"\n\nConfiguring webhook URL: {args.webhook_url}")
        updated_config = client.webhooks.update_config(url=args.webhook_url, enabled=True)
        print("✓ Webhook configured!")
        print(f"  URL: {updated_config['url']}")
        print(f"  Secret: {updated_config['secret']}")
        print(f"  Enabled: {updated_config['enabled']}")

        # Test webhook delivery
        print("\n\n🧪 Testing webhook delivery...")
        secret = args.webhook_secret or updated_config["secret"]

        try:
            result = client.webhooks.test(url=args.webhook_url, secret=secret)
            print(f"✅ {result['message']}")
            print("\n💡 Check your webhook endpoint to see the test payload!")
            print("   It includes sample task and execution data.")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print("\n💡 Make sure your webhook endpoint:")
            print("   - Is publicly accessible (or use ngrok for local testing)")
            print("   - Returns HTTP 2xx status code")
            print("   - Can handle POST requests")

    else:
        print("\n\n💡 TIP: Pass --webhook-url to configure and test webhooks")
        print(
            "   Example: python examples/api_key_usage.py --webhook-url https://webhook.site/unique-id"
        )


async def example_9_async_usage():
    """
    Example: Async SDK usage for concurrent operations
    """
    print("\n=== Example: Async SDK Usage ===\n")

    async with ToraleAsync() as client:
        # Fetch tasks asynchronously
        print("Fetching tasks asynchronously...")
        tasks = await client.tasks.list()
        print(f"✓ Found {len(tasks)} task(s)\n")

        if tasks and len(tasks) >= 2:
            # Execute multiple tasks concurrently
            task_ids = [t.id for t in tasks[:2]]  # First 2 tasks
            print(f"Executing {len(task_ids)} tasks concurrently...")

            results = await asyncio.gather(*[client.tasks.execute(task_id) for task_id in task_ids])

            print("✓ All executions completed\n")
            for i, result in enumerate(results):
                condition_icon = "✅" if result.condition_met else "⏳"
                print(f"  Task {i + 1}:")
                print(f"    Status: {result.status}")
                print(
                    f"    Condition: {condition_icon} {'MET' if result.condition_met else 'Not met yet'}"
                )
        else:
            print("⚠️  Need at least 2 tasks to demonstrate concurrent execution")


def main():
    """
    Run all examples
    """
    # Args are already parsed at module level
    if args.local:
        api_url = "http://localhost:8000"
    else:
        api_url = "https://api.torale.ai"

    print("=" * 60)
    print("TORALE SDK - API KEY AUTHENTICATION EXAMPLES")
    print("=" * 60)
    print(f"API URL: {api_url}")
    print("=" * 60)

    # Check if API key is configured
    if not os.getenv("TORALE_API_KEY"):
        print("\n⚠️  WARNING: TORALE_API_KEY not found in environment!")
        print("\nTo use these examples:")
        print("1. Generate an API key from: https://torale.ai/settings")
        print("2. Add to your .env file: TORALE_API_KEY=sk_...")
        print("3. Run this script again")
        return

    try:
        # Authentication examples
        print("\n" + "=" * 60)
        print("AUTHENTICATION METHODS")
        print("=" * 60)
        example_1_env_variable()
        example_2_explicit_api_key()
        example_3_cli_config()

        # Task creation/operation examples
        print("\n" + "=" * 60)
        print("TASK CREATION & OPERATIONS")
        print("=" * 60)
        example_4_create_task()
        example_5_fluent_api()
        example_6_task_webhooks()
        example_7_task_operations()

        # Webhook management
        print("\n" + "=" * 60)
        print("WEBHOOK CONFIGURATION")
        print("=" * 60)
        example_8_webhook_management()

        # Async example
        print("\n" + "=" * 60)
        print("ASYNC SDK USAGE")
        print("=" * 60)
        asyncio.run(example_9_async_usage())

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. Your API key is valid and active")
        print("2. The Torale API is running (just dev)")
        print("3. You have the correct permissions")


if __name__ == "__main__":
    main()
