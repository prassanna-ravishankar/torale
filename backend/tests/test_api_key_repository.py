from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from torale.access import ApiKeyRepository


@pytest.fixture
def mock_db():
    """Create a mock database instance."""
    return AsyncMock()


@pytest.fixture
def api_key_repo(mock_db):
    """Create an ApiKeyRepository instance with mock database."""
    return ApiKeyRepository(mock_db)


class TestApiKeyRepositoryFindOperations:
    """Tests for API key find operations."""

    @pytest.mark.asyncio
    async def test_find_by_hash_success(self, api_key_repo, mock_db):
        """Test finding an active API key by hash."""
        key_hash = "abc123hash"
        expected_key = {
            "key_id": uuid4(),
            "user_id": uuid4(),
            "clerk_user_id": "clerk_123",
            "email": "test@example.com",
        }
        mock_db.fetch_one.return_value = expected_key

        result = await api_key_repo.find_by_hash(key_hash)

        assert result == expected_key
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "is_active" in call_args[0]

    @pytest.mark.asyncio
    async def test_find_by_hash_not_found(self, api_key_repo, mock_db):
        """Test finding API key when not found."""
        mock_db.fetch_one.return_value = None

        result = await api_key_repo.find_by_hash("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_find_by_user(self, api_key_repo, mock_db):
        """Test finding all API keys for a user."""
        user_id = uuid4()
        expected_keys = [
            {"id": uuid4(), "name": "Key 1", "is_active": True},
            {"id": uuid4(), "name": "Key 2", "is_active": True},
        ]
        mock_db.fetch_all.return_value = expected_keys

        result = await api_key_repo.find_by_user(user_id)

        assert result == expected_keys
        mock_db.fetch_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_user_include_inactive(self, api_key_repo, mock_db):
        """Test finding all API keys including inactive ones."""
        user_id = uuid4()
        expected_keys = [
            {"id": uuid4(), "name": "Key 1", "is_active": True},
            {"id": uuid4(), "name": "Key 2", "is_active": False},
        ]
        mock_db.fetch_all.return_value = expected_keys

        result = await api_key_repo.find_by_user(user_id, include_inactive=True)

        assert result == expected_keys


class TestApiKeyRepositoryCreateOperations:
    """Tests for API key creation operations."""

    @pytest.mark.asyncio
    async def test_create_key(self, api_key_repo, mock_db):
        """Test creating a new API key."""
        user_id = uuid4()
        created_key = {
            "id": uuid4(),
            "user_id": user_id,
            "key_prefix": "sk_...abc123",
            "key_hash": "hash123",
            "name": "CLI Key",
            "is_active": True,
        }
        mock_db.fetch_one.return_value = created_key

        result = await api_key_repo.create_key(
            user_id=user_id,
            key_prefix="sk_...abc123",
            key_hash="hash123",
            name="CLI Key",
        )

        assert result == created_key
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "INSERT INTO" in call_args[0]


class TestApiKeyRepositoryUpdateOperations:
    """Tests for API key update operations."""

    @pytest.mark.asyncio
    async def test_update_last_used(self, api_key_repo, mock_db):
        """Test updating the last_used_at timestamp."""
        key_id = uuid4()

        await api_key_repo.update_last_used(key_id)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        # PyPika generates no spaces around = sign
        assert "last_used_at" in call_args[0] and "NOW()" in call_args[0]

    @pytest.mark.asyncio
    async def test_revoke_key(self, api_key_repo, mock_db):
        """Test revoking an API key."""
        key_id = uuid4()
        revoked_key = {
            "id": key_id,
            "is_active": False,
        }
        mock_db.fetch_one.return_value = revoked_key

        result = await api_key_repo.revoke_key(key_id)

        assert result["is_active"] is False
        mock_db.fetch_one.assert_called_once()
        call_args = mock_db.fetch_one.call_args[0]
        assert "UPDATE" in call_args[0]
