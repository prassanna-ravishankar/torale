from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from torale.repositories.user import UserRepository


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return AsyncMock()


@pytest.fixture
def user_repo(mock_db):
    """Create a UserRepository instance with mock database."""
    return UserRepository(mock_db)


class TestUserRepositoryFindOperations:
    """Tests for user find operations."""

    @pytest.mark.asyncio
    async def test_find_by_clerk_id(self, user_repo, mock_db):
        """Test finding a user by Clerk ID."""
        expected_user = {
            "id": uuid4(),
            "clerk_user_id": "clerk_123",
            "email": "test@example.com",
            "is_active": True,
        }
        mock_db.fetch_one.return_value = expected_user

        result = await user_repo.find_by_clerk_id("clerk_123")

        assert result == expected_user
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "clerk_user_id" in call_args[0]

    @pytest.mark.asyncio
    async def test_find_by_clerk_id_not_found(self, user_repo, mock_db):
        """Test finding a user by Clerk ID when not found."""
        mock_db.fetch_one.return_value = None

        result = await user_repo.find_by_clerk_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_email(self, user_repo, mock_db):
        """Test finding a user by email."""
        expected_user = {
            "id": uuid4(),
            "email": "test@example.com",
            "is_active": True,
        }
        mock_db.fetch_one.return_value = expected_user

        result = await user_repo.find_by_email("test@example.com")

        assert result == expected_user
        mock_db.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_username(self, user_repo, mock_db):
        """Test finding a user by username."""
        expected_user = {
            "id": uuid4(),
            "username": "testuser",
            "email": "test@example.com",
        }
        mock_db.fetch_one.return_value = expected_user

        result = await user_repo.find_by_username("testuser")

        assert result == expected_user


class TestUserRepositoryCreateOperations:
    """Tests for user creation operations."""

    @pytest.mark.asyncio
    async def test_create_user_minimal(self, user_repo, mock_db):
        """Test creating a user with minimal required fields."""
        created_user = {
            "id": uuid4(),
            "clerk_user_id": "clerk_123",
            "email": "test@example.com",
            "is_active": True,
            "first_name": None,
        }
        mock_db.fetch_one.return_value = created_user

        result = await user_repo.create_user(clerk_user_id="clerk_123", email="test@example.com")

        assert result == created_user
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "INSERT INTO" in call_args[0]

    @pytest.mark.asyncio
    async def test_create_user_with_first_name(self, user_repo, mock_db):
        """Test creating a user with first name."""
        created_user = {
            "id": uuid4(),
            "clerk_user_id": "clerk_123",
            "email": "test@example.com",
            "first_name": "John",
            "is_active": True,
        }
        mock_db.fetch_one.return_value = created_user

        result = await user_repo.create_user(
            clerk_user_id="clerk_123", email="test@example.com", first_name="John"
        )

        assert result["first_name"] == "John"


class TestUserRepositoryUpdateOperations:
    """Tests for user update operations."""

    @pytest.mark.asyncio
    async def test_update_user_email(self, user_repo, mock_db):
        """Test updating a user's email."""
        user_id = uuid4()
        updated_user = {
            "id": user_id,
            "email": "newemail@example.com",
            "is_active": True,
        }
        mock_db.fetch_one.return_value = updated_user

        result = await user_repo.update_user(user_id, email="newemail@example.com")

        assert result["email"] == "newemail@example.com"
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "UPDATE" in call_args[0]

    @pytest.mark.asyncio
    async def test_update_user_username(self, user_repo, mock_db):
        """Test updating a user's username."""
        user_id = uuid4()
        updated_user = {
            "id": user_id,
            "username": "newusername",
        }
        mock_db.fetch_one.return_value = updated_user

        result = await user_repo.update_user(user_id, username="newusername")

        assert result["username"] == "newusername"

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
        updated_config = {
            "webhook_url": "https://new.com/webhook",
            "webhook_enabled": True,
            "webhook_secret": "secret_123",
        }

        # First call updates, second call fetches
        mock_db.execute.return_value = None
        mock_db.fetch_one.return_value = updated_config

        result = await user_repo.update_webhook_config(
            user_id, webhook_url="https://new.com/webhook", webhook_enabled=True
        )

        assert result["url"] == "https://new.com/webhook"
        assert result["enabled"] is True
        mock_db.execute.assert_called_once()


class TestUserRepositoryUtilities:
    """Tests for utility methods."""

    @pytest.mark.asyncio
    async def test_username_exists_true(self, user_repo, mock_db):
        """Test username_exists when username is taken."""
        mock_db.fetch_val.return_value = 1

        result = await user_repo.username_exists("takenuser")

        assert result is True

    @pytest.mark.asyncio
    async def test_username_exists_false(self, user_repo, mock_db):
        """Test username_exists when username is available."""
        mock_db.fetch_val.return_value = 0

        result = await user_repo.username_exists("availableuser")

        assert result is False
