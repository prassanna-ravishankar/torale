"""Tests for webhook API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import HTTPException

from torale.api.routers.webhooks import (
    get_user_webhook_config,
    update_user_webhook_config,
    test_webhook,
    list_webhook_deliveries,
    WebhookConfig,
    WebhookTestRequest,
)


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "user@example.com"
    return user


@pytest.fixture
def mock_db():
    """Create a mock database."""
    db = AsyncMock()
    return db


class TestGetUserWebhookConfig:
    """Tests for get_user_webhook_config endpoint."""

    @pytest.mark.asyncio
    async def test_get_enabled_config(self, mock_user, mock_db):
        """Test getting webhook config when enabled."""
        # Mock: user has webhook configured and enabled
        mock_db.fetch_one.return_value = {
            "webhook_url": "https://example.com/webhook",
            "webhook_enabled": True,
        }

        result = await get_user_webhook_config(mock_user, mock_db)

        assert result["webhook_url"] == "https://example.com/webhook"
        assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_disabled_config(self, mock_user, mock_db):
        """Test getting webhook config when disabled."""
        # Mock: user has webhook URL but disabled
        mock_db.fetch_one.return_value = {
            "webhook_url": "https://example.com/webhook",
            "webhook_enabled": False,
        }

        result = await get_user_webhook_config(mock_user, mock_db)

        assert result["webhook_url"] == "https://example.com/webhook"
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_no_config(self, mock_user, mock_db):
        """Test getting webhook config when none exists."""
        # Mock: user has no webhook configured
        mock_db.fetch_one.return_value = {"webhook_url": None, "webhook_enabled": False}

        result = await get_user_webhook_config(mock_user, mock_db)

        assert result["webhook_url"] is None
        assert result["enabled"] is False


class TestUpdateUserWebhookConfig:
    """Tests for update_user_webhook_config endpoint."""

    @pytest.mark.asyncio
    async def test_enable_webhook_first_time(self, mock_user, mock_db):
        """Test enabling webhook for the first time generates secret."""
        config = WebhookConfig(webhook_url="https://example.com/webhook", enabled=True)

        # Mock: user has no existing secret
        mock_db.fetch_one.return_value = {"webhook_secret": None}
        mock_db.execute = AsyncMock()

        with patch(
            "torale.api.routers.webhooks.WebhookSignature.generate_secret",
            return_value="generated_secret_123",
        ):
            result = await update_user_webhook_config(config, mock_user, mock_db)

            assert result["success"] is True
            assert result["webhook_secret"] == "generated_secret_123"

            # Verify database update was called
            mock_db.execute.assert_called_once()
            call_args = mock_db.execute.call_args[0]
            assert "generated_secret_123" in call_args

    @pytest.mark.asyncio
    async def test_enable_webhook_with_existing_secret(self, mock_user, mock_db):
        """Test enabling webhook when secret already exists."""
        config = WebhookConfig(webhook_url="https://example.com/webhook", enabled=True)

        # Mock: user already has a secret
        mock_db.fetch_one.return_value = {"webhook_secret": "existing_secret"}
        mock_db.execute = AsyncMock()

        result = await update_user_webhook_config(config, mock_user, mock_db)

        assert result["success"] is True
        assert result["webhook_secret"] == "existing_secret"

        # Verify database update preserves existing secret
        call_args = mock_db.execute.call_args[0]
        assert "existing_secret" in call_args

    @pytest.mark.asyncio
    async def test_disable_webhook(self, mock_user, mock_db):
        """Test disabling webhook."""
        config = WebhookConfig(webhook_url="https://example.com/webhook", enabled=False)

        # Mock: user has existing secret
        mock_db.fetch_one.return_value = {"webhook_secret": "existing_secret"}
        mock_db.execute = AsyncMock()

        result = await update_user_webhook_config(config, mock_user, mock_db)

        assert result["success"] is True
        assert result["webhook_secret"] is None  # Secret not returned when disabled

    @pytest.mark.asyncio
    async def test_update_webhook_url(self, mock_user, mock_db):
        """Test updating webhook URL."""
        config = WebhookConfig(webhook_url="https://newurl.com/webhook", enabled=True)

        # Mock: user has existing config
        mock_db.fetch_one.return_value = {"webhook_secret": "existing_secret"}
        mock_db.execute = AsyncMock()

        result = await update_user_webhook_config(config, mock_user, mock_db)

        # Verify new URL was passed to database
        call_args = mock_db.execute.call_args[0]
        assert "https://newurl.com/webhook" in call_args[1]  # URL is 2nd parameter


class TestTestWebhook:
    """Tests for test_webhook endpoint."""

    @pytest.mark.asyncio
    async def test_successful_test_delivery(self, mock_user):
        """Test successful webhook test delivery."""
        test_req = WebhookTestRequest(
            webhook_url="https://example.com/webhook", webhook_secret="test_secret"
        )

        # Mock: successful delivery
        mock_service = MagicMock()
        mock_service.deliver = AsyncMock(return_value=(True, 200, None, None))
        mock_service.close = AsyncMock()

        with patch(
            "torale.api.routers.webhooks.WebhookDeliveryService", return_value=mock_service
        ):
            result = await test_webhook(test_req, mock_user)

            assert result["success"] is True
            assert "200" in result["message"]
            mock_service.deliver.assert_called_once()
            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_test_delivery(self, mock_user):
        """Test failed webhook test delivery."""
        test_req = WebhookTestRequest(
            webhook_url="https://example.com/webhook", webhook_secret="test_secret"
        )

        # Mock: failed delivery
        mock_service = MagicMock()
        mock_service.deliver = AsyncMock(
            return_value=(False, 500, "Connection timeout", None)
        )
        mock_service.close = AsyncMock()

        with patch(
            "torale.api.routers.webhooks.WebhookDeliveryService", return_value=mock_service
        ):
            with pytest.raises(HTTPException) as exc_info:
                await test_webhook(test_req, mock_user)

            assert exc_info.value.status_code == 400
            assert "Connection timeout" in exc_info.value.detail
            mock_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_webhook_payload_structure(self, mock_user):
        """Test that test webhook sends correct payload structure."""
        test_req = WebhookTestRequest(
            webhook_url="https://example.com/webhook", webhook_secret="test_secret"
        )

        mock_service = MagicMock()

        async def capture_deliver(*args, **kwargs):
            # Capture the payload argument
            payload = args[1]
            # Verify payload structure
            assert payload.event_type == "task.condition_met"
            assert "task" in payload.data
            assert "execution" in payload.data
            assert payload.data["execution"]["condition_met"] is True
            return (True, 200, None, None)

        mock_service.deliver = AsyncMock(side_effect=capture_deliver)
        mock_service.close = AsyncMock()

        with patch(
            "torale.api.routers.webhooks.WebhookDeliveryService", return_value=mock_service
        ):
            await test_webhook(test_req, mock_user)


class TestListWebhookDeliveries:
    """Tests for list_webhook_deliveries endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_user_deliveries(self, mock_user, mock_db):
        """Test listing all webhook deliveries for a user."""
        # Mock: user has several deliveries
        mock_deliveries = [
            {
                "id": uuid4(),
                "task_id": uuid4(),
                "webhook_url": "https://example.com/webhook",
                "http_status": 200,
                "attempt_number": 1,
                "delivered_at": "2024-01-01T00:00:00",
                "failed_at": None,
                "error_message": None,
                "created_at": "2024-01-01T00:00:00",
            },
            {
                "id": uuid4(),
                "task_id": uuid4(),
                "webhook_url": "https://example.com/webhook",
                "http_status": 500,
                "attempt_number": 2,
                "delivered_at": None,
                "failed_at": "2024-01-01T01:00:00",
                "error_message": "Internal Server Error",
                "created_at": "2024-01-01T01:00:00",
            },
        ]

        mock_db.fetch_all.return_value = mock_deliveries

        result = await list_webhook_deliveries(mock_user, db=mock_db)

        assert len(result) == 2
        assert result[0]["http_status"] == 200
        assert result[1]["http_status"] == 500
        assert result[1]["error_message"] == "Internal Server Error"

    @pytest.mark.asyncio
    async def test_list_deliveries_for_specific_task(self, mock_user, mock_db):
        """Test listing webhook deliveries for a specific task."""
        task_id = str(uuid4())

        # Mock: task exists and belongs to user
        mock_db.fetch_one.return_value = {"id": UUID(task_id)}

        mock_deliveries = [
            {
                "id": uuid4(),
                "task_id": UUID(task_id),
                "webhook_url": "https://example.com/webhook",
                "http_status": 200,
                "attempt_number": 1,
                "delivered_at": "2024-01-01T00:00:00",
                "failed_at": None,
                "error_message": None,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        mock_db.fetch_all.return_value = mock_deliveries

        result = await list_webhook_deliveries(mock_user, task_id=task_id, db=mock_db)

        assert len(result) == 1
        assert result[0]["task_id"] == UUID(task_id)

    @pytest.mark.asyncio
    async def test_list_deliveries_task_not_found(self, mock_user, mock_db):
        """Test listing deliveries for non-existent or unauthorized task."""
        task_id = str(uuid4())

        # Mock: task not found or doesn't belong to user
        mock_db.fetch_one.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await list_webhook_deliveries(mock_user, task_id=task_id, db=mock_db)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_list_deliveries_respects_limit(self, mock_user, mock_db):
        """Test that limit parameter is respected."""
        mock_db.fetch_all.return_value = []

        await list_webhook_deliveries(mock_user, limit=10, db=mock_db)

        # Verify limit was passed to database query
        call_args = mock_db.fetch_all.call_args[0]
        assert 10 in call_args

    @pytest.mark.asyncio
    async def test_list_deliveries_empty_result(self, mock_user, mock_db):
        """Test listing deliveries when user has none."""
        mock_db.fetch_all.return_value = []

        result = await list_webhook_deliveries(mock_user, db=mock_db)

        assert result == []
