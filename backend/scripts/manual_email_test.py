"""Test condition met notification to specific email."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add backend to path - must be before importing local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# ruff: noqa: E402 - Import must come after sys.path modification
from torale.notifications.novu_service import novu_service


async def main():
    email = "me@prassanna.io"

    print("\n=== Testing Condition Met Notification ===")
    print(f"Sending to: {email}")

    result = await novu_service.send_condition_met_notification(
        subscriber_id=email,
        task_name="Test Task - iPhone Release Monitor",
        search_query="When is the next iPhone being released?",
        answer="Apple announced the iPhone 16 will be released on September 20, 2024, with pre-orders starting September 13.",
        change_summary="Apple officially announced the release date during their September event",
        grounding_sources=[
            {
                "title": "Apple announces iPhone 16 release date",
                "uri": "https://www.apple.com/newsroom/2024/09/iphone-16-available-september-20/",
            },
            {
                "title": "iPhone 16: Everything you need to know",
                "uri": "https://www.macrumors.com/guide/iphone-16/",
            },
            {
                "title": "Apple Event September 2024",
                "uri": "https://www.theverge.com/2024/9/9/apple-event-iphone-16",
            },
        ],
        task_id="test_task_123",
        execution_id="test_exec_456",
    )

    if result.get("success"):
        print("✓ Notification sent successfully!")
        print(f"  Transaction ID: {result.get('transaction_id')}")
    else:
        print(f"✗ Failed: {result.get('error')}")
        if result.get("skipped"):
            print("  (Novu not configured)")


if __name__ == "__main__":
    asyncio.run(main())
