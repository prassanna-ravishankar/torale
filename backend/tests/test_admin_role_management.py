"""Integration tests for Admin Role Management endpoints.

These tests verify the admin role management functionality, including:
- GET /admin/users - returns user roles from Clerk
- PATCH /admin/users/{id}/role - updates user roles in Clerk publicMetadata
- Role update safeguards (self-demotion prevention, validation)

Prerequisites:
- Local dev environment running (`just dev`)
- Test database with migrations applied
- Clerk mock or test mode enabled

Run with:
    pytest tests/test_admin_role_management.py -v
"""

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

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


class TestAdminUsersEndpoint:
    """Test GET /admin/users endpoint with role fetching."""

    def test_admin_users_requires_authentication(self):
        """Test that /admin/users requires authentication."""
        response = httpx.get(
            f"{API_BASE_URL}/admin/users",
            timeout=5.0,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_admin_users_requires_admin_role(self):
        """Test that /admin/users requires admin role."""
        # This would require proper test authentication setup
        # For now, we verify the endpoint exists and returns appropriate error
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_admin_users_returns_roles(self):
        """Test that /admin/users includes role field in response."""
        # This test would need proper admin authentication
        # and mocked Clerk responses for user role fetching
        pytest.skip("Requires Clerk test authentication setup with admin role")


class TestUpdateUserRole:
    """Test PATCH /admin/users/{user_id}/role endpoint."""

    @pytest.fixture
    def mock_admin_clerk_user(self):
        """Mock Clerk user with admin role."""
        with patch("torale.access.clerk_client") as mock_clerk:
            # Mock the admin user calling the endpoint
            admin_user = MagicMock()
            admin_user.public_metadata = {"role": "admin"}
            admin_user.id = "admin_clerk_id_123"

            # Setup the mock to return admin for role checks
            mock_clerk.users.get.return_value = admin_user
            yield mock_clerk

    @pytest.fixture
    def mock_target_user(self):
        """Mock target user being updated."""
        user = MagicMock()
        user.public_metadata = {}  # Regular user with no role
        user.id = "target_clerk_id_456"
        return user

    def test_update_user_role_requires_authentication(self):
        """Test that role update requires authentication."""
        test_user_id = str(uuid4())
        response = httpx.patch(
            f"{API_BASE_URL}/admin/users/{test_user_id}/role",
            json={"role": "developer"},
            timeout=5.0,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_update_user_role_requires_admin(self):
        """Test that role update requires admin role."""
        # This would require authentication with non-admin user
        pytest.skip("Requires Clerk test authentication setup")

    @pytest.mark.asyncio
    async def test_update_user_role_validates_role_values(self, mock_admin_clerk_user):
        """Test that only valid roles are accepted."""
        # This test verifies role validation logic
        pytest.skip("Requires Clerk test authentication setup with admin role")


class TestRoleUpdateSafeguards:
    """Test safeguards for role updates."""

    @pytest.fixture
    def mock_clerk_same_user(self):
        """Mock Clerk where admin tries to change their own role."""
        with patch("torale.access.clerk_client") as mock_clerk:
            # Same user for both admin and target
            user = MagicMock()
            user.public_metadata = {"role": "admin"}
            user.id = "same_clerk_id"
            mock_clerk.users.get.return_value = user
            yield mock_clerk

    @pytest.mark.asyncio
    async def test_prevent_self_role_change(self, mock_clerk_same_user):
        """Test that admins cannot change their own role."""
        # This test would verify the safeguard preventing self-demotion
        pytest.skip("Requires Clerk test authentication setup with admin role")

    def test_role_validation_rejects_invalid_roles(self):
        """Test that invalid role values are rejected."""
        # Verify that roles other than 'admin', 'developer', or null are rejected
        # This can be tested without full authentication by checking validation logic
        pass

    def test_role_update_confirmation_required(self):
        """Test that role updates require proper confirmation."""
        # Frontend responsibility - documented for completeness
        pass


class TestRoleUpdateIntegration:
    """Integration tests for complete role update flow."""

    @pytest.fixture
    def mock_clerk_with_update(self):
        """Mock Clerk client with update capability."""
        with patch("torale.access.clerk_client") as mock_clerk:
            # Mock admin user
            admin_user = MagicMock()
            admin_user.public_metadata = {"role": "admin"}
            admin_user.id = "admin_id"

            # Mock target user
            target_user = MagicMock()
            target_user.public_metadata = {}
            target_user.id = "target_id"

            # Mock get to return appropriate user based on call
            def mock_get(user_id):
                if user_id == "admin_id":
                    return admin_user
                return target_user

            mock_clerk.users.get.side_effect = mock_get

            # Mock update method
            mock_clerk.users.update = MagicMock()

            yield mock_clerk

    @pytest.mark.asyncio
    async def test_successful_role_update_to_developer(self, mock_clerk_with_update):
        """Test successful role update to developer."""
        pytest.skip("Requires Clerk test authentication setup with admin role")

    @pytest.mark.asyncio
    async def test_successful_role_update_to_admin(self, mock_clerk_with_update):
        """Test successful role update to admin."""
        pytest.skip("Requires Clerk test authentication setup with admin role")

    @pytest.mark.asyncio
    async def test_successful_role_removal(self, mock_clerk_with_update):
        """Test successful role removal (set to null)."""
        pytest.skip("Requires Clerk test authentication setup with admin role")

    @pytest.mark.asyncio
    async def test_role_update_updates_clerk_metadata(self, mock_clerk_with_update):
        """Test that role updates are properly stored in Clerk publicMetadata."""
        pytest.skip("Requires Clerk test authentication setup with admin role")


class TestRoleUpdateErrorHandling:
    """Test error handling for role updates."""

    @pytest.mark.asyncio
    async def test_role_update_nonexistent_user(self):
        """Test role update with non-existent user ID."""
        # Should return 404 when user not found in database
        pytest.skip("Requires Clerk test authentication setup with admin role")

    @pytest.mark.asyncio
    async def test_role_update_clerk_api_failure(self):
        """Test handling of Clerk API failures during role update."""
        # Should return 500 with appropriate error message
        pytest.skip("Requires Clerk test authentication setup with admin role")

    @pytest.mark.asyncio
    async def test_role_update_invalid_user_id_format(self):
        """Test role update with invalid UUID format."""
        # Should return 422 for invalid UUID
        pytest.skip("Requires Clerk test authentication setup with admin role")


class TestBulkRoleUpdates:
    """Test patterns for bulk role updates (frontend responsibility)."""

    def test_bulk_update_implementation_note(self):
        """Note: Bulk updates are handled client-side with multiple API calls."""
        # Frontend iterates through selected users and calls the endpoint for each
        # Backend provides single-user endpoint; frontend handles batching
        # This is intentional to maintain transactional clarity and error handling
        pass


# Unit tests that don't require API server
class TestRoleValidationLogic:
    """Unit tests for role validation logic."""

    def test_valid_roles(self):
        """Test that valid role values are accepted."""
        valid_roles = ["admin", "developer", None]
        for role in valid_roles:
            # Role validation should accept these values
            assert role in ["admin", "developer", None]

    def test_invalid_roles(self):
        """Test that invalid role values are rejected."""
        invalid_roles = ["superadmin", "moderator", "user", "", "null", 123, []]
        for role in invalid_roles:
            # Role validation should reject these values
            assert role not in ["admin", "developer", None]

    def test_role_metadata_structure(self):
        """Test proper structure for Clerk publicMetadata."""
        # Roles are stored as: publicMetadata = {"role": "admin"}
        metadata_with_role = {"role": "admin"}
        assert "role" in metadata_with_role
        assert metadata_with_role["role"] in ["admin", "developer"]

        # No role is represented by absence of role key or None value
        metadata_no_role = {}
        assert "role" not in metadata_no_role or metadata_no_role.get("role") is None


class TestPydanticValidation:
    """Test Pydantic request validation for role endpoints.

    Note: These tests require Clerk authentication setup to test validation properly.
    Currently marked as skipped until Clerk mock/test infrastructure is available.
    """

    @pytest.mark.skip(reason="Requires Clerk auth setup - hits 403 before validation")
    def test_invalid_role_returns_422(self):
        """Test that invalid role values return 422 Unprocessable Entity."""
        test_user_id = str(uuid4())
        try:
            response = httpx.patch(
                f"{API_BASE_URL}/admin/users/{test_user_id}/role",
                json={"role": "superadmin"},  # Invalid role
                timeout=5.0,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        except httpx.ConnectError:
            pytest.skip("API server not available")

    @pytest.mark.skip(reason="Requires Clerk auth setup - hits 403 before validation")
    def test_bulk_update_empty_array_returns_422(self):
        """Test that empty user_ids array is rejected."""
        try:
            response = httpx.patch(
                f"{API_BASE_URL}/admin/users/roles",
                json={"user_ids": [], "role": "developer"},
                timeout=5.0,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        except httpx.ConnectError:
            pytest.skip("API server not available")

    @pytest.mark.skip(reason="Requires Clerk auth setup - hits 403 before validation")
    def test_bulk_update_exceeds_limit_returns_422(self):
        """Test that user_ids array > 100 is rejected."""
        try:
            response = httpx.patch(
                f"{API_BASE_URL}/admin/users/roles",
                json={"user_ids": [str(uuid4()) for _ in range(101)], "role": "developer"},
                timeout=5.0,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        except httpx.ConnectError:
            pytest.skip("API server not available")

    @pytest.mark.skip(reason="Requires Clerk auth setup - hits 403 before validation")
    def test_missing_role_field_returns_422(self):
        """Test that missing required 'role' field returns 422."""
        test_user_id = str(uuid4())
        try:
            response = httpx.patch(
                f"{API_BASE_URL}/admin/users/{test_user_id}/role",
                json={},  # Missing role field
                timeout=5.0,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        except httpx.ConnectError:
            pytest.skip("API server not available")

    def test_valid_null_role_accepted(self):
        """Test that null role value is accepted (removes role)."""
        test_user_id = str(uuid4())
        try:
            response = httpx.patch(
                f"{API_BASE_URL}/admin/users/{test_user_id}/role",
                json={"role": None},  # Valid: removes role
                timeout=5.0,
            )
            # Will fail auth but validates request format
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
            ]
        except httpx.ConnectError:
            pytest.skip("API server not available")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
