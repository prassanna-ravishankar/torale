"""Integration tests for notification flows.

These tests verify the end-to-end notification flow from task execution
to webhook delivery and email verification.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from torale.notifications import (
    EmailVerificationService,
    WebhookDeliveryService,
    WebhookSignature,
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
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


@pytest.fixture
def sample_task_with_notifications(sample_user):
    """Create a task with both email and webhook notifications."""
    task = MagicMock()
    task.id = uuid4()
    task.user_id = sample_user.id
    task.name = "Test Task"
    task.schedule = "0 9 * * *"
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
    execution.started_at = datetime.now(UTC)
    execution.completed_at = datetime.now(UTC)
    return execution


@pytest.fixture
def sample_monitoring_result():
    """Create MonitoringResult dict (new structure)."""
    return {
        "summary": "Test answer",
        "sources": [{"uri": "https://example.com", "title": "Example"}],
        "metadata": {
            "changed": True,
            "change_explanation": "Test change detected",
            "current_state": {"test_field": "test_value"},
        },
    }


class TestEmailVerificationFlow:
    """Test complete email verification flow."""

    @pytest.mark.asyncio
    async def test_complete_verification_flow(self, sample_user):
        """Test full email verification flow: send → verify → use."""
        mock_conn = AsyncMock()

        # Step 1: User requests verification code
        # Mock: no recent verifications (rate limit check passes)
        mock_conn.fetchval = AsyncMock(return_value=0)

        can_send, error = await EmailVerificationService.can_send_verification(
            mock_conn, str(sample_user.id)
        )
        assert can_send is True
        assert error is None

        # Step 2: Verification code is created
        mock_conn.execute = AsyncMock()

        success, code, error = await EmailVerificationService.create_verification(
            mock_conn, str(sample_user.id), "custom@example.com"
        )

        assert success is True
        assert len(code) == 6
        assert code.isdigit()
        assert error is None

        # Step 3: User verifies with correct code
        from datetime import datetime, timedelta

        class MockTransaction:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "id": uuid4(),
                "user_id": sample_user.id,
                "email": "custom@example.com",
                "verification_code": code,
                "expires_at": datetime.utcnow() + timedelta(minutes=10),
                "attempts": 0,
                "verified": False,
            }
        )

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "custom@example.com", code
        )

        assert success is True
        assert error is None

        # Step 4: Email is now verified and can be used
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "clerk_email": sample_user.email,
                "in_verified_array": True,  # Email is in verified list
            }
        )

        is_verified = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), "custom@example.com"
        )
        assert is_verified is True

    @pytest.mark.asyncio
    async def test_clerk_email_bypass(self, sample_user):
        """Test that Clerk email is automatically verified."""
        mock_conn = AsyncMock()

        # Mock: email matches clerk_email
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "clerk_email": sample_user.email,
                "in_verified_array": False,
            }
        )

        # Clerk email should be verified without any verification record
        is_verified = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), sample_user.email
        )

        assert is_verified is True


class TestWebhookNotificationFlow:
    """Test complete webhook notification flow."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_complete_webhook_flow(
        self, mock_post, sample_task_with_notifications, sample_execution, sample_monitoring_result
    ):
        """Test full webhook flow: condition met → payload built → signed → delivered."""

        # Step 1: Build webhook payload from execution
        task_dict = {
            "id": sample_task_with_notifications.id,
            "name": sample_task_with_notifications.name,
            "search_query": sample_task_with_notifications.search_query,
            "condition_description": sample_task_with_notifications.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        assert payload.event_type == "task.condition_met"
        assert payload.data["task"]["id"] == str(sample_task_with_notifications.id)
        assert payload.data["execution"]["condition_met"] is True

        # Step 2: Sign payload
        secret = "test_secret_key"
        timestamp = int(datetime.now(UTC).timestamp())
        payload_json = payload.model_dump_json()
        signature = WebhookSignature.sign(payload_json, secret, timestamp)

        # Step 3: Verify signature (simulating recipient verification)
        is_valid = WebhookSignature.verify(payload_json, signature, secret)
        assert is_valid is True

        # Step 4: Deliver webhook
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        service = WebhookDeliveryService()
        success, http_status, error_msg, sig = await service.deliver(
            sample_task_with_notifications.webhook_url,
            payload,
            secret=secret,
        )

        assert success is True
        assert http_status == 200
        assert error_msg is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_webhook_retry_flow(
        self, mock_post, sample_task_with_notifications, sample_execution, sample_monitoring_result
    ):
        """Test webhook retry logic when delivery fails."""
        # Mock: Initial delivery fails with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task_with_notifications.id,
            "name": sample_task_with_notifications.name,
            "search_query": sample_task_with_notifications.search_query,
            "condition_description": sample_task_with_notifications.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        service = WebhookDeliveryService()
        success, http_status, error_msg, sig = await service.deliver(
            sample_task_with_notifications.webhook_url,
            payload,
            secret="test_secret",
        )

        # Should fail with 500
        assert success is False
        assert http_status == 500
        assert "HTTP 500" in error_msg


class TestNotificationSpamPrevention:
    """Test spam prevention mechanisms."""

    @pytest.mark.asyncio
    async def test_email_rate_limiting(self, sample_user):
        """Test that email verification is rate limited."""
        mock_conn = AsyncMock()

        # Mock: User has sent 3 verifications in the last hour (at limit)
        mock_conn.fetchval = AsyncMock(return_value=3)

        can_send, error = await EmailVerificationService.can_send_verification(
            mock_conn, str(sample_user.id)
        )

        assert can_send is False
        assert "Too many verification requests" in error

    @pytest.mark.asyncio
    async def test_notification_daily_limit(self, sample_user):
        """Test daily notification limit (100/day)."""
        mock_conn = AsyncMock()

        # Mock: User has sent 100 notifications today (at limit)
        mock_conn.fetchval = AsyncMock(return_value=100)

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Daily notification limit" in error

    @pytest.mark.asyncio
    async def test_notification_hourly_limit(self, sample_user):
        """Test hourly notification limit (10/hour)."""
        mock_conn = AsyncMock()

        # Mock fetchval: 50 daily (OK), 10 hourly (at limit)
        mock_conn.fetchval = AsyncMock(side_effect=[50, 10])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Too many notifications" in error


class TestMultiChannelNotification:
    """Test notifications across multiple channels."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_both_email_and_webhook(
        self,
        mock_post,
        sample_user,
        sample_task_with_notifications,
        sample_execution,
        sample_monitoring_result,
    ):
        """Test that task can notify via both email and webhook."""
        # Verify task has both channels configured
        assert "email" in sample_task_with_notifications.notification_channels
        assert "webhook" in sample_task_with_notifications.notification_channels
        assert sample_task_with_notifications.notification_email == "custom@example.com"
        assert sample_task_with_notifications.webhook_url == "https://example.com/webhook"

        # Test webhook delivery
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task_with_notifications.id,
            "name": sample_task_with_notifications.name,
            "search_query": sample_task_with_notifications.search_query,
            "condition_description": sample_task_with_notifications.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        webhook_service = WebhookDeliveryService()
        success, http_status, error_msg, sig = await webhook_service.deliver(
            sample_task_with_notifications.webhook_url,
            payload,
            secret="test_secret",
        )

        assert success is True
        assert http_status == 200

        # Test email verification for custom email
        mock_conn = AsyncMock()

        # Mock: Email is verified (in verified array)
        mock_conn.fetchrow = AsyncMock(
            return_value={
                "clerk_email": sample_user.email,
                "in_verified_array": True,
            }
        )

        is_verified = await EmailVerificationService.is_email_verified(
            mock_conn,
            str(sample_user.id),
            sample_task_with_notifications.notification_email,
        )

        assert is_verified is True
