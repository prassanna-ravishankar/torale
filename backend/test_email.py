#!/usr/bin/env python
"""Quick test of condition met email."""

import asyncio

from torale.notifications.novu_service import novu_service


async def main():
    result = await novu_service.send_condition_met_notification(
        subscriber_id="me@prassanna.io",
        task_name="iPhone Release Monitor",
        search_query="When is the next iPhone being released?",
        answer="Apple announced the iPhone 16 will be released on September 20, 2024, with pre-orders starting September 13.",
        change_summary="Apple officially announced the release date during their September event",
        grounding_sources=[
            {
                "title": "Apple announces iPhone 16",
                "uri": "https://www.apple.com/newsroom/2024/09/iphone-16",
            },
            {"title": "iPhone 16 Guide", "uri": "https://www.macrumors.com/guide/iphone-16/"},
            {
                "title": "Apple Event Coverage",
                "uri": "https://www.theverge.com/2024/9/9/apple-event",
            },
        ],
        task_id="test_123",
        execution_id="test_456",
    )

    if result.get("success"):
        print(f"✓ Email sent! Transaction: {result.get('transaction_id')}")
    else:
        print(f"✗ Failed: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
