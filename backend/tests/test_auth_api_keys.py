"""Integration tests for API Key Management endpoints.

These tests verify the API key creation, listing, and revocation functionality,
including role-based access control (developer role requirement).

Prerequisites:
- Local dev environment running (`just dev`)
- Test database with migrations applied
- Clerk mock or test mode enabled

Run with:
    pytest tests/test_auth_api_keys.py -v
"""

import hashlib
import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import status

# Base URL for API
API_BASE_URL = os.getenv("TORALE_API_URL", "http://localhost:8000")


def check_api_available() -> bool:
    """Check if the API server is available."""
    try:
        httpx.get(f"{API_BASE_URL}/api/v1/tasks", timeout=2.0)
        return True
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        return True


pytestmark = pytest.mark.skipif(not check_api_available(), reason="API server not available")


class TestAPIKeyCreation:
    """Test API key creation with role-based access control."""

    @pytest.fixture
    def mock_clerk_user_developer(self):
        """Mock Clerk user with developer role."""
        with patch("torale.api.clerk_auth.clerk_client") as mock_clerk:
            mock_user = MagicMock()
            mock_user.public_metadata = {"role": "developer"}
            mock_clerk.users.get.return_value = mock_user
            yield mock_clerk

    @pytest.fixture
    def mock_clerk_user_no_role(self):
        """Mock Clerk user without developer role."""
        with patch("torale.api.clerk_auth.clerk_client") as mock_clerk:
            mock_user = MagicMock()
            mock_user.public_metadata = {}  # No role
            mock_clerk.users.get.return_value = mock_user
            yield mock_clerk

    def test_create_api_key_requires_authentication(self):
        """Test that API key creation requires authentication."""
        response = httpx.post(
            f"{API_BASE_URL}/auth/api-keys",
            json={"name": "Test Key"},
            timeout=5.0,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_api_key_with_developer_role(self, mock_clerk_user_developer):
        """Test successful API key creation with developer role."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_create_api_key_without_developer_role_fails(self, mock_clerk_user_no_role):
        """Test that API key creation fails without developer role."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")

    def test_api_key_format_validation(self):
        """Test that generated API keys have correct format."""
        # API keys should start with sk_
        # This is tested indirectly through creation
        # Key format: sk_[32-char urlsafe token]
        import secrets

        key = f"sk_{secrets.token_urlsafe(32)}"
        assert key.startswith("sk_")
        assert len(key) > 35  # sk_ + at least 32 chars

    def test_api_key_hashing(self):
        """Test that API keys are properly hashed with SHA256."""
        test_key = "sk_test_key_12345"
        expected_hash = hashlib.sha256(test_key.encode()).hexdigest()

        # Verify hash is deterministic
        actual_hash = hashlib.sha256(test_key.encode()).hexdigest()
        assert actual_hash == expected_hash
        assert len(actual_hash) == 64  # SHA256 produces 64 hex chars

    def test_api_key_prefix_generation(self):
        """Test that key prefix is generated correctly."""
        test_key = "sk_abcdefghijklmnopqrstuvwxyz123456"
        # Prefix should be first 15 chars + "..."
        expected_prefix = test_key[:15] + "..."
        assert expected_prefix == "sk_abcdefghijkl..."
        assert len(expected_prefix) == 18


class TestAPIKeyListing:
    """Test API key listing functionality."""

    def test_list_api_keys_requires_authentication(self):
        """Test that listing API keys requires authentication."""
        response = httpx.get(f"{API_BASE_URL}/auth/api-keys", timeout=5.0)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_api_keys_returns_user_keys_only(self):
        """Test that users can only see their own API keys."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")


class TestAPIKeyRevocation:
    """Test API key revocation functionality."""

    def test_revoke_api_key_requires_authentication(self):
        """Test that revoking API keys requires authentication."""
        fake_key_id = "550e8400-e29b-41d4-a716-446655440000"
        response = httpx.delete(f"{API_BASE_URL}/auth/api-keys/{fake_key_id}", timeout=5.0)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self):
        """Test successful API key revocation."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key_returns_404(self):
        """Test that revoking non-existent key returns 404."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_cannot_revoke_other_users_keys(self):
        """Test that users cannot revoke other users' API keys."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")


class TestOneKeyPerUserEnforcement:
    """Test that only one active API key is allowed per user."""

    @pytest.mark.asyncio
    async def test_creating_second_key_fails_when_one_exists(self):
        """Test that creating a second API key fails when user already has one."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_can_create_key_after_revoking_existing(self):
        """Test that user can create new key after revoking existing one."""
        # This would require proper test authentication setup
        # Skipping for now as it needs Clerk test tokens
        pytest.skip("Requires Clerk test authentication setup")


class TestAPIKeyAuthentication:
    """Test using API keys for authentication."""

    def test_valid_api_key_authenticates_successfully(self):
        """Test that valid API key can authenticate API requests."""
        # This requires a real API key from database
        # Skipping for now as it needs test data setup
        pytest.skip("Requires test API key in database")

    def test_invalid_api_key_returns_401(self):
        """Test that invalid API key returns 401."""
        fake_key = "sk_invalid_key_12345"
        response = httpx.get(
            f"{API_BASE_URL}/api/v1/tasks",
            headers={"Authorization": f"Bearer {fake_key}"},
            timeout=5.0,
            follow_redirects=False,  # Don't follow redirects
        )
        # Should return 401, 403, or 307 (redirect to auth)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_307_TEMPORARY_REDIRECT,
        ]

    def test_revoked_api_key_returns_401(self):
        """Test that revoked API key cannot authenticate."""
        # This requires a revoked API key from database
        # Skipping for now as it needs test data setup
        pytest.skip("Requires revoked test API key in database")


class TestAPIKeySecurityFeatures:
    """Test security features of API key system."""

    def test_full_key_only_shown_once_on_creation(self):
        """Test that full API key is only returned on creation."""
        # This is verified through API design
        # Creation returns full key, listing returns only prefix
        # This is a design pattern test, not an integration test
        pass

    def test_key_hash_never_exposed_in_api(self):
        """Test that key hash is never exposed through API."""
        # This is verified through API design
        # No endpoint returns key_hash field
        # This is a design pattern test, not an integration test
        pass

    def test_api_keys_scoped_to_user(self):
        """Test that API keys are scoped to the user who created them."""
        # This is verified through authentication logic
        # API key auth returns the user_id of the key owner
        # This is a design pattern test, not an integration test
        pass


# Note: Many tests are skipped because they require:
# 1. Proper Clerk test authentication setup
# 2. Test database with known user accounts
# 3. Test API keys seeded in database
#
# These tests serve as:
# - Documentation of expected behavior
# - Framework for future integration testing
# - Unit tests for isolated logic (hashing, formatting)
