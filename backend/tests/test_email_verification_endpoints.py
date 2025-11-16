"""Tests for email verification API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.email_verification import (
    VerificationConfirm,
    VerificationRequest,
    list_verified_emails,
    remove_verified_email,
    send_verification_email,
    verify_email_code,
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
    """Create a mock database connection."""
    from unittest.mock import MagicMock

    db = MagicMock()
    conn = AsyncMock()

    # Mock the acquire() context manager
    class MockAcquire:
        async def __aenter__(self):
            return conn

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    db.acquire = MagicMock(return_value=MockAcquire())
    db.fetch_one = AsyncMock()
    db.fetch_val = AsyncMock()
    db.execute = AsyncMock()
    db.get_connection = AsyncMock(return_value=conn)  # Keep for backward compatibility
    return db


class TestSendVerificationEmail:
    """Tests for send_verification_email endpoint."""

    @pytest.mark.asyncio
    async def test_send_to_new_email(self, mock_user, mock_db):
        """Test sending verification code to new email."""
        request = VerificationRequest(email="new@example.com")

        # Get the connection that will be returned by the context manager
        conn = await mock_db.acquire().__aenter__()

        # Mock: email not already verified
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.is_email_verified",
            return_value=False,
        ):
            # Mock: verification creation success
            with patch(
                "torale.api.routers.email_verification.EmailVerificationService.create_verification",
                return_value=(True, "123456", None),
            ):
                # Mock: user lookup
                conn.fetchrow.return_value = {"first_name": "Test"}

                # Mock: Novu service
                with patch(
                    "torale.api.routers.email_verification.novu_service.send_verification_email",
                    new_callable=AsyncMock,
                ) as mock_novu:
                    result = await send_verification_email(request, mock_user, mock_db)

                    assert "Verification code sent" in result["message"]
                    assert result["expires_in_minutes"] == 15
                    mock_novu.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_verified_email(self, mock_user, mock_db):
        """Test sending verification code to already verified email."""
        request = VerificationRequest(email="verified@example.com")

        # Mock: email already verified
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.is_email_verified",
            return_value=True,
        ):
            result = await send_verification_email(request, mock_user, mock_db)

            assert result["message"] == "Email already verified"

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, mock_user, mock_db):
        """Test rate limit enforcement (3 verifications/hour)."""
        request = VerificationRequest(email="new@example.com")

        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.is_email_verified",
            return_value=False,
        ):
            # Mock: rate limit exceeded
            with patch(
                "torale.api.routers.email_verification.EmailVerificationService.create_verification",
                return_value=(False, None, "Rate limit exceeded. Please try again later."),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await send_verification_email(request, mock_user, mock_db)

                assert exc_info.value.status_code == 429
                assert "Rate limit" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_user_name_fallback(self, mock_user, mock_db):
        """Test fallback to email prefix when user has no first name."""
        request = VerificationRequest(email="new@example.com")
        conn = await mock_db.acquire().__aenter__()

        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.is_email_verified",
            return_value=False,
        ):
            with patch(
                "torale.api.routers.email_verification.EmailVerificationService.create_verification",
                return_value=(True, "123456", None),
            ):
                # Mock: user without first_name
                conn.fetchrow.return_value = {"first_name": None}

                with patch(
                    "torale.api.routers.email_verification.novu_service.send_verification_email",
                    new_callable=AsyncMock,
                ) as mock_novu:
                    await send_verification_email(request, mock_user, mock_db)

                    # Should use email prefix as fallback
                    call_args = mock_novu.call_args[1]
                    assert call_args["user_name"] == "user"  # From user@example.com


class TestVerifyEmailCode:
    """Tests for verify_email_code endpoint."""

    @pytest.mark.asyncio
    async def test_successful_verification(self, mock_user, mock_db):
        """Test successful email verification with correct code."""
        request = VerificationConfirm(email="test@example.com", code="123456")

        # Mock: verification success
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.verify_code",
            return_value=(True, None),
        ):
            result = await verify_email_code(request, mock_user, mock_db)

            assert result["message"] == "Email verified successfully"

    @pytest.mark.asyncio
    async def test_invalid_code(self, mock_user, mock_db):
        """Test verification with incorrect code."""
        request = VerificationConfirm(email="test@example.com", code="999999")

        # Mock: verification failure
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.verify_code",
            return_value=(False, "Invalid verification code"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await verify_email_code(request, mock_user, mock_db)

            assert exc_info.value.status_code == 400
            assert "Invalid" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_expired_code(self, mock_user, mock_db):
        """Test verification with expired code."""
        request = VerificationConfirm(email="test@example.com", code="123456")

        # Mock: verification failure due to expiry
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.verify_code",
            return_value=(False, "Verification code has expired"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await verify_email_code(request, mock_user, mock_db)

            assert exc_info.value.status_code == 400
            assert "expired" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_no_attempts_remaining(self, mock_user, mock_db):
        """Test verification when max attempts exceeded."""
        request = VerificationConfirm(email="test@example.com", code="123456")

        # Mock: no attempts left
        with patch(
            "torale.api.routers.email_verification.EmailVerificationService.verify_code",
            return_value=(False, "No verification attempts remaining"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await verify_email_code(request, mock_user, mock_db)

            assert exc_info.value.status_code == 400
            assert "attempts" in exc_info.value.detail.lower()


class TestListVerifiedEmails:
    """Tests for list_verified_emails endpoint."""

    @pytest.mark.asyncio
    async def test_list_only_clerk_email(self, mock_user, mock_db):
        """Test listing when only Clerk email is verified."""
        # Mock: only Clerk email, no custom verified emails
        mock_db.fetch_one.return_value = {
            "email": "user@example.com",
            "verified_notification_emails": None,
        }

        result = await list_verified_emails(mock_user, mock_db)

        assert "user@example.com" in result["verified_emails"]
        assert result["primary_email"] == "user@example.com"
        assert len(result["verified_emails"]) == 1

    @pytest.mark.asyncio
    async def test_list_with_custom_emails(self, mock_user, mock_db):
        """Test listing with both Clerk and custom verified emails."""
        # Mock: Clerk email + custom verified emails
        mock_db.fetch_one.return_value = {
            "email": "user@example.com",
            "verified_notification_emails": ["custom1@example.com", "custom2@example.com"],
        }

        result = await list_verified_emails(mock_user, mock_db)

        assert len(result["verified_emails"]) == 3
        assert "user@example.com" in result["verified_emails"]
        assert "custom1@example.com" in result["verified_emails"]
        assert "custom2@example.com" in result["verified_emails"]
        assert result["primary_email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_deduplication(self, mock_user, mock_db):
        """Test that duplicate emails are removed."""
        # Mock: Clerk email appears in both places (shouldn't happen, but handle gracefully)
        mock_db.fetch_one.return_value = {
            "email": "user@example.com",
            "verified_notification_emails": ["user@example.com", "custom@example.com"],
        }

        result = await list_verified_emails(mock_user, mock_db)

        # Should deduplicate
        assert len(result["verified_emails"]) == 2
        assert result["verified_emails"].count("user@example.com") == 1


class TestRemoveVerifiedEmail:
    """Tests for remove_verified_email endpoint."""

    @pytest.mark.asyncio
    async def test_remove_custom_email(self, mock_user, mock_db):
        """Test removing a custom verified email."""
        # Mock: Clerk email lookup
        mock_db.fetch_val.return_value = "user@example.com"

        result = await remove_verified_email("custom@example.com", mock_user, mock_db)

        assert result["message"] == "Email removed from verified list"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_cannot_remove_clerk_email(self, mock_user, mock_db):
        """Test that Clerk email cannot be removed."""
        # Mock: Clerk email lookup
        mock_db.fetch_val.return_value = "user@example.com"

        with pytest.raises(HTTPException) as exc_info:
            await remove_verified_email("user@example.com", mock_user, mock_db)

        assert exc_info.value.status_code == 400
        assert "Cannot remove primary Clerk email" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_remove_nonexistent_email(self, mock_user, mock_db):
        """Test removing an email that wasn't verified (should succeed silently)."""
        # Mock: Clerk email lookup
        mock_db.fetch_val.return_value = "user@example.com"

        # Should still succeed (array_remove is idempotent)
        result = await remove_verified_email("notverified@example.com", mock_user, mock_db)

        assert result["message"] == "Email removed from verified list"
        mock_db.execute.assert_called_once()
