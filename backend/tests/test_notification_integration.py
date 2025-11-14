"""Integration tests for notification flows.

These tests verify the end-to-end notification flow from task execution
to webhook delivery and email verification.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from torale.core.email_verification import EmailVerificationService
from torale.core.webhook import (
    WebhookSignature,
    WebhookDeliveryService,
    build_webhook_payload,
)


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = MagicMock()
    user.id = uuid4()
    user.clerk_user_id = "user_test123"
    user.email = "user@example.com"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def sample_task_with_notifications(sample_user):
    """Create a task with both email and webhook notifications."""
    task = MagicMock()
    task.id = uuid4()
    task.user_id = sample_user.id
    task.name = "Test Task"
    task.schedule = "0 9 * * *"
    task.executor_type = "llm_grounded_search"
    task.config = {"model": "gemini-2.0-flash-exp"}
    task.search_query = "Test query"
    task.condition_description = "Test condition"
    task.is_active = True
    task.notification_channels = ["email", "webhook"]
    task.notification_email = "custom@example.com"
    task.webhook_url = "https://example.com/webhook"
    return task


@pytest.fixture
def sample_execution(sample_task_with_notifications):
    """Create a successful task execution with condition met."""
    execution = MagicMock()
    execution.id = uuid4()
    execution.task_id = sample_task_with_notifications.id
    execution.status = "success"
    execution.condition_met = True
    execution.result = {"answer": "Test answer"}
    execution.change_summary = "Test change detected"
    execution.grounding_sources = [{"url": "https://example.com", "title": "Example"}]
    execution.started_at = datetime.now(timezone.utc)
    execution.completed_at = datetime.now(timezone.utc)
    return execution


class TestEmailVerificationFlow:
    """Test complete email verification flow."""

    @pytest.mark.asyncio
    async def test_complete_verification_flow(self, sample_user):
        """Test full email verification flow: send → verify → use."""
        mock_db = AsyncMock()

        # Step 1: User requests verification code
        service = EmailVerificationService(mock_db)

        # Mock: no recent verifications (rate limit check passes)
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 0))

        can_send = await service.can_send_verification(
            sample_user.id, "custom@example.com"
        )
        assert can_send is True

        # Step 2: Verification code is created
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        code = "123456"
        verification = await service.create_verification(
            sample_user.id, "custom@example.com", code
        )

        assert verification.code == code
        assert verification.attempts_left == 5
        assert verification.is_verified is False

        # Step 3: User verifies with correct code
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        success = await service.verify_code(
            sample_user.id, "custom@example.com", code
        )

        assert success is True
        assert verification.is_verified is True

        # Step 4: Email is now verified and can be used
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_verified = await service.is_email_verified(
            sample_user, "custom@example.com"
        )
        assert is_verified is True

    @pytest.mark.asyncio
    async def test_clerk_email_bypass(self, sample_user):
        """Test that Clerk email is automatically verified."""
        mock_db = AsyncMock()
        service = EmailVerificationService(mock_db)

        # Clerk email should be verified without any verification record
        is_verified = await service.is_email_verified(sample_user, sample_user.email)

        assert is_verified is True
        # No database query should have been made
        mock_db.execute.assert_not_called()


class TestWebhookNotificationFlow:
    """Test complete webhook notification flow."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_complete_webhook_flow(
        self, mock_post, sample_task_with_notifications, sample_execution
    ):
        """Test full webhook flow: condition met → payload built → signed → delivered."""
        mock_db = AsyncMock()

        # Step 1: Build webhook payload from execution
        payload = build_webhook_payload(
            sample_task_with_notifications, sample_execution
        )

        assert payload["event"] == "task.condition_met"
        assert payload["task"]["id"] == str(sample_task_with_notifications.id)
        assert payload["execution"]["condition_met"] is True

        # Step 2: Sign payload
        secret = "test_secret_key"
        timestamp = int(datetime.now(timezone.utc).timestamp())
        signature = WebhookSignature.sign(payload, secret, timestamp)

        # Step 3: Verify signature (simulating recipient verification)
        is_valid = WebhookSignature.verify(payload, signature, secret)
        assert is_valid is True

        # Step 4: Deliver webhook
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = WebhookDeliveryService(mock_db)
        delivery = await service.deliver(
            sample_task_with_notifications,
            sample_execution,
            payload,
            secret=secret,
        )

        assert delivery.status == "success"
        assert delivery.http_status_code == 200
        assert delivery.webhook_url == sample_task_with_notifications.webhook_url

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_webhook_retry_flow(
        self, mock_post, sample_task_with_notifications, sample_execution
    ):
        """Test webhook retry logic when delivery fails."""
        mock_db = AsyncMock()

        # Mock: Initial delivery fails with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(
            sample_task_with_notifications, sample_execution
        )

        service = WebhookDeliveryService(mock_db)
        delivery = await service.deliver(
            sample_task_with_notifications,
            sample_execution,
            payload,
            secret="test_secret",
        )

        # Should be marked for retry
        assert delivery.status == "retrying"
        assert delivery.http_status_code == 500
        assert delivery.next_retry_at is not None
        assert delivery.retry_count == 0


class TestNotificationSpamPrevention:
    """Test spam prevention mechanisms."""

    @pytest.mark.asyncio
    async def test_email_rate_limiting(self, sample_user):
        """Test that email verification is rate limited."""
        mock_db = AsyncMock()
        service = EmailVerificationService(mock_db)

        # Mock: User has sent 3 verifications in the last hour (at limit)
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 3))

        can_send = await service.can_send_verification(
            sample_user.id, "test@example.com"
        )

        assert can_send is False

    @pytest.mark.asyncio
    async def test_notification_daily_limit(self, sample_user):
        """Test daily notification limit (100/day)."""
        mock_db = AsyncMock()
        service = EmailVerificationService(mock_db)

        # Mock: User has sent 100 notifications today (at limit)
        mock_result = MagicMock()
        mock_result.scalar = lambda: 100
        mock_db.execute = AsyncMock(return_value=mock_result)

        can_send = await service.check_spam_limits(
            sample_user.id, "test@example.com"
        )

        assert can_send is False

    @pytest.mark.asyncio
    async def test_notification_hourly_limit(self, sample_user):
        """Test hourly notification limit (10/hour)."""
        mock_db = AsyncMock()
        service = EmailVerificationService(mock_db)

        def side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if not hasattr(side_effect, "call_count"):
                side_effect.call_count = 0
            side_effect.call_count += 1

            if side_effect.call_count == 1:
                mock_result.scalar = lambda: 50  # Under daily limit
            else:
                mock_result.scalar = lambda: 10  # At hourly limit
            return mock_result

        mock_db.execute = AsyncMock(side_effect=side_effect)

        can_send = await service.check_spam_limits(
            sample_user.id, "test@example.com"
        )

        assert can_send is False


class TestMultiChannelNotification:
    """Test notifications across multiple channels."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_both_email_and_webhook(
        self, mock_post, sample_user, sample_task_with_notifications, sample_execution
    ):
        """Test that task can notify via both email and webhook."""
        mock_db = AsyncMock()

        # Verify task has both channels configured
        assert "email" in sample_task_with_notifications.notification_channels
        assert "webhook" in sample_task_with_notifications.notification_channels
        assert sample_task_with_notifications.notification_email == "custom@example.com"
        assert sample_task_with_notifications.webhook_url == "https://example.com/webhook"

        # Test webhook delivery
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(
            sample_task_with_notifications, sample_execution
        )

        webhook_service = WebhookDeliveryService(mock_db)
        webhook_delivery = await webhook_service.deliver(
            sample_task_with_notifications,
            sample_execution,
            payload,
            secret="test_secret",
        )

        assert webhook_delivery.status == "success"

        # Test email verification for custom email
        email_service = EmailVerificationService(mock_db)

        # Mock: Email is verified
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: MagicMock(
            is_verified=True, email="custom@example.com"
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_verified = await email_service.is_email_verified(
            sample_user, sample_task_with_notifications.notification_email
        )

        assert is_verified is True
