"""Tests for webhook signing and delivery."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import json
import hmac
import hashlib

from torale.core.webhook import (
    WebhookSignature,
    WebhookDeliveryService,
    build_webhook_payload,
)


@pytest.fixture
def sample_task():
    """Create a sample task."""
    task = MagicMock()
    task.id = uuid4()
    task.user_id = uuid4()
    task.name = "Test Task"
    task.schedule = "0 9 * * *"
    task.executor_type = "llm_grounded_search"
    task.config = {"model": "gemini-2.0-flash-exp"}
    task.search_query = "Test query"
    task.condition_description = "Test condition"
    task.is_active = True
    task.webhook_url = "https://example.com/webhook"
    return task


@pytest.fixture
def sample_execution(sample_task):
    """Create a sample task execution."""
    execution = MagicMock()
    execution.id = uuid4()
    execution.task_id = sample_task.id
    execution.status = "success"
    execution.condition_met = True
    execution.result = {"answer": "Test answer"}
    execution.change_summary = "Test change"
    execution.grounding_sources = [{"url": "https://example.com", "title": "Example"}]
    execution.started_at = datetime.now(timezone.utc)
    execution.completed_at = datetime.now(timezone.utc)
    return execution


class TestWebhookSignature:
    """Tests for WebhookSignature class."""

    def test_generate_secret(self):
        """Test that secret generation creates secure random string."""
        secret = WebhookSignature.generate_secret()

        assert len(secret) == 64  # 32 bytes = 64 hex characters
        assert all(c in "0123456789abcdef" for c in secret)

    def test_different_secrets(self):
        """Test that multiple calls generate different secrets."""
        secrets = [WebhookSignature.generate_secret() for _ in range(10)]
        assert len(set(secrets)) == 10

    def test_sign_creates_valid_signature(self):
        """Test that signing creates expected format."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        timestamp = 1234567890

        signature = WebhookSignature.sign(payload, secret, timestamp)

        # Check format: t=timestamp,v1=signature
        assert signature.startswith(f"t={timestamp},v1=")
        parts = signature.split(",")
        assert len(parts) == 2
        assert parts[0] == f"t={timestamp}"
        assert parts[1].startswith("v1=")

    def test_sign_uses_hmac_sha256(self):
        """Test that signature uses HMAC-SHA256."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        timestamp = 1234567890

        signature = WebhookSignature.sign(payload, secret, timestamp)

        # Extract signature part
        sig_part = signature.split("v1=")[1]

        # Compute expected signature
        signed_payload = f"{timestamp}.{json.dumps(payload, separators=(',', ':'))}"
        expected_sig = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert sig_part == expected_sig

    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        timestamp = int(datetime.now(timezone.utc).timestamp())

        signature = WebhookSignature.sign(payload, secret, timestamp)

        result = WebhookSignature.verify(payload, signature, secret)

        assert result is True

    def test_verify_invalid_signature(self):
        """Test verification rejects invalid signature."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        timestamp = int(datetime.now(timezone.utc).timestamp())

        # Create signature with different secret
        signature = WebhookSignature.sign(payload, "wrong_secret", timestamp)

        result = WebhookSignature.verify(payload, signature, secret)

        assert result is False

    def test_verify_malformed_signature(self):
        """Test verification rejects malformed signature."""
        secret = "test_secret_key"
        payload = {"test": "data"}

        result = WebhookSignature.verify(payload, "invalid_format", secret)

        assert result is False

    def test_verify_expired_timestamp(self):
        """Test verification rejects old timestamps (>5 min)."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        # Timestamp from 10 minutes ago
        old_timestamp = int(datetime.now(timezone.utc).timestamp()) - 600

        signature = WebhookSignature.sign(payload, secret, old_timestamp)

        result = WebhookSignature.verify(payload, signature, secret, tolerance=300)

        assert result is False

    def test_verify_within_tolerance(self):
        """Test verification accepts timestamps within tolerance."""
        secret = "test_secret_key"
        payload = {"test": "data"}
        # Timestamp from 2 minutes ago
        recent_timestamp = int(datetime.now(timezone.utc).timestamp()) - 120

        signature = WebhookSignature.sign(payload, secret, recent_timestamp)

        result = WebhookSignature.verify(payload, signature, secret, tolerance=300)

        assert result is True


class TestBuildWebhookPayload:
    """Tests for build_webhook_payload function."""

    def test_payload_structure(self, sample_task, sample_execution):
        """Test that payload has correct structure."""
        payload = build_webhook_payload(sample_task, sample_execution)

        assert "event" in payload
        assert "task" in payload
        assert "execution" in payload
        assert "timestamp" in payload

    def test_event_type(self, sample_task, sample_execution):
        """Test event type is correct."""
        payload = build_webhook_payload(sample_task, sample_execution)

        assert payload["event"] == "task.condition_met"

    def test_task_data(self, sample_task, sample_execution):
        """Test task data includes necessary fields."""
        payload = build_webhook_payload(sample_task, sample_execution)

        task_data = payload["task"]
        assert task_data["id"] == str(sample_task.id)
        assert task_data["name"] == sample_task.name
        assert task_data["search_query"] == sample_task.search_query
        assert task_data["condition_description"] == sample_task.condition_description

    def test_execution_data(self, sample_task, sample_execution):
        """Test execution data includes necessary fields."""
        payload = build_webhook_payload(sample_task, sample_execution)

        exec_data = payload["execution"]
        assert exec_data["id"] == str(sample_execution.id)
        assert exec_data["status"] == sample_execution.status
        assert exec_data["condition_met"] == sample_execution.condition_met
        assert exec_data["change_summary"] == sample_execution.change_summary
        assert exec_data["grounding_sources"] == sample_execution.grounding_sources

    def test_timestamp_format(self, sample_task, sample_execution):
        """Test timestamp is in ISO format."""
        payload = build_webhook_payload(sample_task, sample_execution)

        # Should be parseable as ISO datetime
        timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)


class TestWebhookDeliveryService:
    """Tests for WebhookDeliveryService class."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def delivery_service(self, mock_db):
        """Create webhook delivery service instance."""
        return WebhookDeliveryService(mock_db)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_successful_delivery(
        self, mock_post, delivery_service, mock_db, sample_task, sample_execution
    ):
        """Test successful webhook delivery."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(sample_task, sample_execution)
        delivery = await delivery_service.deliver(
            sample_task,
            sample_execution,
            payload,
            secret="test_secret",
        )

        assert delivery.status == "success"
        assert delivery.http_status_code == 200
        assert delivery.response_body == "OK"
        assert delivery.retry_count == 0
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_failed_delivery_retries(
        self, mock_post, delivery_service, mock_db, sample_task, sample_execution
    ):
        """Test that failed delivery triggers retries."""
        # First call fails with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(sample_task, sample_execution)
        delivery = await delivery_service.deliver(
            sample_task,
            sample_execution,
            payload,
            secret="test_secret",
        )

        assert delivery.status == "retrying"
        assert delivery.http_status_code == 500
        assert delivery.retry_count == 0
        assert delivery.next_retry_at is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_timeout(
        self, mock_post, delivery_service, mock_db, sample_task, sample_execution
    ):
        """Test that delivery has 10-second timeout."""
        import asyncio

        mock_post.side_effect = asyncio.TimeoutError()

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(sample_task, sample_execution)
        delivery = await delivery_service.deliver(
            sample_task,
            sample_execution,
            payload,
            secret="test_secret",
        )

        assert delivery.status == "failed"
        assert "timeout" in delivery.error_message.lower()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_includes_headers(
        self, mock_post, delivery_service, mock_db, sample_task, sample_execution
    ):
        """Test that delivery includes required headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(sample_task, sample_execution)
        await delivery_service.deliver(
            sample_task,
            sample_execution,
            payload,
            secret="test_secret",
        )

        # Verify headers in the call
        call_kwargs = mock_post.call_args[1]
        headers = call_kwargs["headers"]

        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert "X-Torale-Signature" in headers
        assert "X-Torale-Event" in headers
        assert headers["X-Torale-Event"] == "task.condition_met"
        assert "X-Torale-Delivery-ID" in headers

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_records_attempt(
        self, mock_post, delivery_service, mock_db, sample_task, sample_execution
    ):
        """Test that delivery is recorded in database."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = build_webhook_payload(sample_task, sample_execution)
        delivery = await delivery_service.deliver(
            sample_task,
            sample_execution,
            payload,
            secret="test_secret",
        )

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        # Verify delivery record
        assert delivery.task_id == sample_task.id
        assert delivery.execution_id == sample_execution.id
        assert delivery.webhook_url == sample_task.webhook_url
