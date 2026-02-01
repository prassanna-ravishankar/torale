"""Tests for webhook signing and delivery."""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from torale.notifications import (
    WebhookDeliveryService,
    WebhookSignature,
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
            "change_explanation": "Test change",
            "current_state": {"test_field": "test_value"},
        },
    }


class TestWebhookSignature:
    """Tests for WebhookSignature class."""

    def test_generate_secret(self):
        """Test that secret generation creates secure random string."""
        secret = WebhookSignature.generate_secret()

        assert len(secret) == 43  # 32 bytes = 43 URL-safe base64 characters
        # URL-safe base64 uses A-Z, a-z, 0-9, -, _
        assert all(
            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in secret
        )

    def test_different_secrets(self):
        """Test that multiple calls generate different secrets."""
        secrets = [WebhookSignature.generate_secret() for _ in range(10)]
        assert len(set(secrets)) == 10

    def test_sign_creates_valid_signature(self):
        """Test that signing creates expected format."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})
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
        payload = json.dumps({"test": "data"})
        timestamp = 1234567890

        signature = WebhookSignature.sign(payload, secret, timestamp)

        # Extract signature part
        sig_part = signature.split("v1=")[1]

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload}"
        expected_sig = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert sig_part == expected_sig

    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})
        timestamp = int(datetime.now(UTC).timestamp())

        signature = WebhookSignature.sign(payload, secret, timestamp)

        result = WebhookSignature.verify(payload, signature, secret)

        assert result is True

    def test_verify_invalid_signature(self):
        """Test verification rejects invalid signature."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})
        timestamp = int(datetime.now(UTC).timestamp())

        # Create signature with different secret
        signature = WebhookSignature.sign(payload, "wrong_secret", timestamp)

        result = WebhookSignature.verify(payload, signature, secret)

        assert result is False

    def test_verify_malformed_signature(self):
        """Test verification rejects malformed signature."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})

        result = WebhookSignature.verify(payload, "invalid_format", secret)

        assert result is False

    def test_verify_expired_timestamp(self):
        """Test verification rejects old timestamps (>5 min)."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})
        # Timestamp from 10 minutes ago
        old_timestamp = int(datetime.now(UTC).timestamp()) - 600

        signature = WebhookSignature.sign(payload, secret, old_timestamp)

        result = WebhookSignature.verify(payload, signature, secret, tolerance=300)

        assert result is False

    def test_verify_within_tolerance(self):
        """Test verification accepts timestamps within tolerance."""
        secret = "test_secret_key"
        payload = json.dumps({"test": "data"})
        # Timestamp from 2 minutes ago
        recent_timestamp = int(datetime.now(UTC).timestamp()) - 120

        signature = WebhookSignature.sign(payload, secret, recent_timestamp)

        result = WebhookSignature.verify(payload, signature, secret, tolerance=300)

        assert result is True


class TestBuildWebhookPayload:
    """Tests for build_webhook_payload function."""

    def test_payload_structure(self, sample_task, sample_execution, sample_monitoring_result):
        """Test that payload has correct structure."""
        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        assert payload.event_type == "task.condition_met"
        assert "task" in payload.data
        assert "execution" in payload.data
        assert "result" in payload.data
        assert payload.created_at > 0

    def test_event_type(self, sample_task, sample_execution, sample_monitoring_result):
        """Test event type is correct."""
        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        assert payload.event_type == "task.condition_met"

    def test_task_data(self, sample_task, sample_execution, sample_monitoring_result):
        """Test task data includes necessary fields."""
        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        task_data = payload.data["task"]
        assert task_data["id"] == str(sample_task.id)
        assert task_data["name"] == sample_task.name
        assert task_data["search_query"] == sample_task.search_query
        assert task_data["condition_description"] == sample_task.condition_description

    def test_execution_data(self, sample_task, sample_execution, sample_monitoring_result):
        """Test execution data includes necessary fields."""
        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        exec_data = payload.data["execution"]
        assert exec_data["id"] == str(sample_execution.id)
        assert exec_data["condition_met"] == sample_monitoring_result["metadata"]["changed"]
        assert (
            exec_data["change_summary"]
            == sample_monitoring_result["metadata"]["change_explanation"]
        )

    def test_timestamp_format(self, sample_task, sample_execution, sample_monitoring_result):
        """Test timestamp is Unix timestamp."""
        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )

        # created_at should be Unix timestamp (int)
        assert isinstance(payload.created_at, int)
        assert payload.created_at > 0


class TestWebhookDeliveryService:
    """Tests for WebhookDeliveryService class."""

    @pytest.fixture
    def delivery_service(self):
        """Create webhook delivery service instance."""
        return WebhookDeliveryService()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_successful_delivery(
        self, mock_post, delivery_service, sample_task, sample_execution, sample_monitoring_result
    ):
        """Test successful webhook delivery."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )
        success, http_status, error_msg, signature = await delivery_service.deliver(
            sample_task.webhook_url,
            payload,
            secret="test_secret",
        )

        assert success is True
        assert http_status == 200
        assert error_msg is None
        assert signature is not None
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_failed_delivery_retries(
        self, mock_post, delivery_service, sample_task, sample_execution, sample_monitoring_result
    ):
        """Test that failed delivery returns error status."""
        # First call fails with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )
        success, http_status, error_msg, signature = await delivery_service.deliver(
            sample_task.webhook_url,
            payload,
            secret="test_secret",
        )

        assert success is False
        assert http_status == 500
        assert "HTTP 500" in error_msg
        assert signature is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_timeout(
        self, mock_post, delivery_service, sample_task, sample_execution, sample_monitoring_result
    ):
        """Test that delivery has 10-second timeout."""
        import httpx

        mock_post.side_effect = httpx.TimeoutException("Timeout")

        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )
        success, http_status, error_msg, signature = await delivery_service.deliver(
            sample_task.webhook_url,
            payload,
            secret="test_secret",
        )

        assert success is False
        assert http_status is None
        assert "timeout" in error_msg.lower()
        assert signature is not None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_includes_headers(
        self, mock_post, delivery_service, sample_task, sample_execution, sample_monitoring_result
    ):
        """Test that delivery includes required headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )
        await delivery_service.deliver(
            sample_task.webhook_url,
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
        assert "X-Torale-Delivery" in headers

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_delivery_returns_result_tuple(
        self, mock_post, delivery_service, sample_task, sample_execution, sample_monitoring_result
    ):
        """Test that delivery returns proper result tuple."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        task_dict = {
            "id": sample_task.id,
            "name": sample_task.name,
            "search_query": sample_task.search_query,
            "condition_description": sample_task.condition_description,
        }
        execution_dict = {
            "completed_at": sample_execution.completed_at,
        }

        payload = build_webhook_payload(
            str(sample_execution.id), task_dict, execution_dict, sample_monitoring_result
        )
        result = await delivery_service.deliver(
            sample_task.webhook_url,
            payload,
            secret="test_secret",
        )

        # Verify result tuple structure
        assert isinstance(result, tuple)
        assert len(result) == 4
        success, http_status, error_msg, signature = result
        assert success is True
        assert http_status == 200
        assert error_msg is None
        assert isinstance(signature, str)
