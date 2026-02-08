from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from torale.access import UserRepository


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return AsyncMock()


@pytest.fixture
def user_repo(mock_db):
    """Create a UserRepository instance with mock database."""
    return UserRepository(mock_db)


class TestUserRepositoryUpdateOperations:
    """Tests for user update operations."""

    @pytest.mark.asyncio
    async def test_update_user_no_changes(self, user_repo, mock_db):
        """Test updating a user with no changes returns current user."""
        user_id = uuid4()
        current_user = {
            "id": user_id,
            "email": "test@example.com",
        }
        mock_db.fetch_one.return_value = current_user

        result = await user_repo.update_user(user_id)

        assert result == current_user
        # Should use find_by_id, not update
        assert "SELECT" in mock_db.fetch_one.call_args[0][0]


class TestUserRepositoryWebhookOperations:
    """Tests for webhook configuration operations."""

    @pytest.mark.asyncio
    async def test_get_webhook_config(self, user_repo, mock_db):
        """Test getting webhook configuration."""
        user_id = uuid4()
        webhook_row = {
            "webhook_url": "https://example.com/webhook",
            "webhook_enabled": True,
            "webhook_secret": "secret_123",
        }
        mock_db.fetch_one.return_value = webhook_row

        result = await user_repo.get_webhook_config(user_id)

        assert result["url"] == "https://example.com/webhook"
        assert result["enabled"] is True
        assert result["secret"] == "secret_123"

    @pytest.mark.asyncio
    async def test_get_webhook_config_no_url(self, user_repo, mock_db):
        """Test getting webhook config when URL is None."""
        user_id = uuid4()
        webhook_row = {
            "webhook_url": None,
            "webhook_enabled": False,
            "webhook_secret": None,
        }
        mock_db.fetch_one.return_value = webhook_row

        result = await user_repo.get_webhook_config(user_id)

        assert result["url"] is None
        assert result["enabled"] is False

    @pytest.mark.asyncio
    async def test_update_webhook_config(self, user_repo, mock_db):
        """Test updating webhook configuration."""
        user_id = uuid4()
        updated_row = {
            "webhook_url": "https://new.com/webhook",
            "webhook_enabled": True,
            "webhook_secret": "secret_123",
        }

        # Now uses RETURNING clause, single fetch_one call
        mock_db.fetch_one.return_value = updated_row

        result = await user_repo.update_webhook_config(
            user_id, webhook_url="https://new.com/webhook", webhook_enabled=True
        )

        assert result["url"] == "https://new.com/webhook"
        assert result["enabled"] is True
        assert result["secret"] == "secret_123"
        mock_db.fetch_one.assert_called_once()
