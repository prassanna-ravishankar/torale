#!/usr/bin/env python
"""Test script for notification system (email verification, Novu, webhooks)."""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from torale.core.email_verification import EmailVerificationService
from torale.core.webhook import WebhookPayload, WebhookSignature
from torale.notifications.novu_service import novu_service


async def test_email_verification():
    """Test email verification code generation."""
    print("\n=== Testing Email Verification ===")

    # Test code generation
    code = EmailVerificationService.generate_code()
    print(f"✓ Generated code: {code}")
    assert len(code) == 6
    assert code.isdigit()
    print("✓ Code format valid")


async def test_webhook_signature():
    """Test webhook signature generation and verification."""
    print("\n=== Testing Webhook Signatures ===")

    # Generate secret
    secret = WebhookSignature.generate_secret()
    print(f"✓ Generated secret: {secret[:16]}...")
    assert len(secret) > 32

    # Test signing
    payload = '{"test": "data"}'
    timestamp = int(time.time())  # Use current time
    signature = WebhookSignature.sign(payload, secret, timestamp)
    print(f"✓ Generated signature: {signature[:50]}...")
    assert signature.startswith("t=")
    assert ",v1=" in signature

    # Test verification
    is_valid = WebhookSignature.verify(payload, signature, secret, tolerance=300)
    print(f"✓ Signature verification: {is_valid}")
    assert is_valid

    # Test tampering detection
    tampered_payload = '{"test": "modified"}'
    is_invalid = WebhookSignature.verify(tampered_payload, signature, secret, tolerance=300)
    print(f"✓ Tampered payload rejected: {not is_invalid}")
    assert not is_invalid


async def test_webhook_payload():
    """Test webhook payload building."""
    print("\n=== Testing Webhook Payload ===")

    payload = WebhookPayload(
        id="test_123",
        event_type="task.condition_met",
        created_at=1699564800,
        data={
            "task": {
                "id": "task_456",
                "name": "Test Task",
                "search_query": "test query",
                "condition_description": "test condition",
            },
            "execution": {
                "id": "exec_789",
                "condition_met": True,
                "change_summary": "Test change",
                "completed_at": "2024-11-09T10:00:00Z",
            },
            "result": {
                "answer": "Test answer",
                "grounding_sources": [],
            },
        },
    )

    print(f"✓ Created payload: {payload.event_type}")
    print(f"✓ Payload ID: {payload.id}")
    print(f"✓ Payload data keys: {list(payload.data.keys())}")

    # Test JSON serialization
    json_payload = payload.model_dump_json()
    print(f"✓ JSON payload length: {len(json_payload)} bytes")


async def test_novu_service():
    """Test Novu service initialization and actual notification sending."""
    print("\n=== Testing Novu Service ===")

    print(f"✓ Novu service enabled: {novu_service._enabled}")
    if novu_service._enabled:
        print("✓ Novu client initialized")

        # Try sending a test notification
        print("\nAttempting to send test notification...")
        result = await novu_service.send_condition_met_notification(
            subscriber_id="test@example.com",
            task_name="Test Task",
            search_query="Test query",
            answer="Test answer",
            change_summary="Test change",
            grounding_sources=[{"title": "Test Source", "uri": "https://example.com"}],
            task_id="test_task_123",
            execution_id="test_exec_456",
        )

        if result.get("success"):
            print("✓ Test notification sent successfully!")
            print(f"  Transaction ID: {result.get('transaction_id')}")
        else:
            print(f"✗ Failed to send notification: {result.get('error')}")
    else:
        print("⚠ Novu not configured (expected in development)")


async def main():
    """Run all tests."""
    print("Starting notification system tests...")

    try:
        await test_email_verification()
        await test_webhook_signature()
        await test_webhook_payload()
        await test_novu_service()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
