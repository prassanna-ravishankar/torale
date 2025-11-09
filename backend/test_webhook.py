#!/usr/bin/env python
"""Test webhook delivery."""

import asyncio
import json
import time

from torale.core.webhook import WebhookPayload, WebhookSignature


async def main():
    # Generate a test webhook secret
    secret = WebhookSignature.generate_secret()
    print(f"Generated webhook secret: {secret}\n")

    # Create a test payload manually
    payload_data = {
        "id": "test_exec_123",
        "event_type": "task.condition_met",
        "created_at": int(time.time()),
        "object": "event",
        "api_version": "v1",
        "data": {
            "task": {
                "id": "test_task_456",
                "name": "iPhone Release Monitor",
                "search_query": "When is the next iPhone being released?",
                "condition_description": "A specific release date has been announced",
            },
            "execution": {
                "id": "test_exec_123",
                "condition_met": True,
                "change_summary": "Apple officially announced the release date during their September event",
                "completed_at": "2024-11-09T10:30:00Z",
            },
            "result": {
                "answer": "Apple announced the iPhone 16 will be released on September 20, 2024",
                "grounding_sources": [
                    {
                        "title": "Apple announces iPhone 16",
                        "uri": "https://www.apple.com/newsroom/2024/09/iphone-16",
                    },
                    {
                        "title": "iPhone 16 Guide",
                        "uri": "https://www.macrumors.com/guide/iphone-16/",
                    },
                ],
            },
        },
    }

    payload = WebhookPayload(**payload_data)

    # Convert to JSON
    payload_json = json.dumps(payload.model_dump(), indent=2)
    print("Webhook Payload:")
    print(payload_json)
    print()

    # Generate signature
    timestamp = int(time.time())
    signature = WebhookSignature.sign(payload_json, secret, timestamp)
    print(f"Webhook Signature: {signature}")
    print()

    # Verify signature
    is_valid = WebhookSignature.verify(payload_json, signature, secret)
    print(f"Signature Valid: {is_valid}")
    print()

    # Show headers that would be sent
    print("Headers that would be sent:")
    print("Content-Type: application/json")
    print("User-Agent: Torale-Webhooks/1.0")
    print("X-Torale-Event: task.condition_met")
    print(f"X-Torale-Signature: {signature}")
    print(f"X-Torale-Delivery: {payload.id}")
    print()

    print("\n✓ Webhook test data generated!")
    print("\nTo test with a real endpoint:")
    print("1. Go to https://webhook.site")
    print("2. Copy your unique URL")
    print("3. Use this curl command:")
    print()
    print("curl -X POST https://webhook.site/YOUR-ID \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'X-Torale-Event: task.condition_met' \\")
    print(f"  -H 'X-Torale-Signature: {signature}' \\")
    print(f"  -H 'X-Torale-Delivery: {payload.id}' \\")
    print(f"  -d '{payload_json}'")


if __name__ == "__main__":
    asyncio.run(main())
