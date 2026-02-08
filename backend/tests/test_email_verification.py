"""Tests for email verification service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from torale.notifications import EmailVerificationService

from .conftest import MockTransaction


@pytest.fixture
def mock_conn():
    """Mock database connection."""
    return AsyncMock()


def _make_verification_record(sample_user, *, expires_delta=timedelta(minutes=10), attempts=0):
    """Build a verification record dict with sensible defaults."""
    return {
        "id": uuid4(),
        "user_id": sample_user.id,
        "email": "test@example.com",
        "verification_code": "123456",
        "expires_at": datetime.utcnow() + expires_delta,
        "attempts": attempts,
        "verified": False,
    }


class TestCanSendVerification:
    """Tests for can_send_verification method."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "count,expected_allowed",
        [(0, True), (2, True), (3, False)],
        ids=["first_request", "under_limit", "at_limit"],
    )
    async def test_rate_limit_enforcement(self, mock_conn, sample_user, count, expected_allowed):
        """Rate limit allows < 3 requests/hour and blocks at 3."""
        mock_conn.fetchval = AsyncMock(return_value=count)

        can_send, error = await EmailVerificationService.can_send_verification(
            mock_conn, str(sample_user.id)
        )

        assert can_send is expected_allowed
        if expected_allowed:
            assert error is None
        else:
            assert "Too many verification requests" in error


class TestCreateVerification:
    """Tests for create_verification method."""

    @pytest.mark.asyncio
    async def test_creates_verification_record(self, mock_conn, sample_user):
        """Test that verification record is created successfully."""
        mock_conn.fetchval = AsyncMock(return_value=0)
        mock_conn.execute = AsyncMock()

        success, code, error = await EmailVerificationService.create_verification(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert success is True
        assert len(code) == 6
        assert code.isdigit()
        assert error is None
        assert mock_conn.execute.call_count == 2  # DELETE + INSERT

    @pytest.mark.asyncio
    async def test_sets_expiration_15_minutes(self, mock_conn, sample_user):
        """Test that verification uses 15 minute expiry (constant is 15)."""
        mock_conn.fetchval = AsyncMock(return_value=0)
        mock_conn.execute = AsyncMock()

        success, code, error = await EmailVerificationService.create_verification(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert success is True
        assert EmailVerificationService.VERIFICATION_EXPIRY_MINUTES == 15


class TestVerifyCode:
    """Tests for verify_code method."""

    @pytest.mark.asyncio
    async def test_successful_verification(self, mock_conn, sample_user):
        """Test successful code verification."""
        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value=_make_verification_record(sample_user))
        mock_conn.execute = AsyncMock()

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_invalid_code(self, mock_conn, sample_user):
        """Test verification with wrong code."""
        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value=_make_verification_record(sample_user))
        mock_conn.execute = AsyncMock()

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "999999"
        )

        assert success is False
        assert "Invalid code" in error

    @pytest.mark.asyncio
    async def test_expired_code(self, mock_conn, sample_user):
        """Test verification with expired code."""
        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(
            return_value=_make_verification_record(sample_user, expires_delta=timedelta(minutes=-1))
        )

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is False
        assert "expired" in error.lower()

    @pytest.mark.asyncio
    async def test_no_attempts_left(self, mock_conn, sample_user):
        """Test verification when no attempts remaining."""
        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(
            return_value=_make_verification_record(sample_user, attempts=5)
        )

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is False
        assert "Too many" in error

    @pytest.mark.asyncio
    async def test_verification_not_found(self, mock_conn, sample_user):
        """Test verification when record doesn't exist."""
        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value=None)

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is False
        assert "No verification pending" in error


class TestIsEmailVerified:
    """Tests for is_email_verified method."""

    @pytest.mark.asyncio
    async def test_clerk_email_always_verified(self, mock_conn, sample_user):
        """Test that Clerk email is automatically verified."""
        mock_conn.fetchrow = AsyncMock(
            return_value={"clerk_email": sample_user.email, "in_verified_array": False}
        )

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), sample_user.email
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verified_custom_email(self, mock_conn, sample_user):
        """Test that verified custom email returns True."""
        mock_conn.fetchrow = AsyncMock(
            return_value={"clerk_email": sample_user.email, "in_verified_array": True}
        )

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), "custom@example.com"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_unverified_custom_email(self, mock_conn, sample_user):
        """Test that unverified custom email returns False."""
        mock_conn.fetchrow = AsyncMock(
            return_value={"clerk_email": sample_user.email, "in_verified_array": False}
        )

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), "custom@example.com"
        )

        assert result is False


class TestCheckSpamLimits:
    """Tests for check_spam_limits method."""

    @pytest.mark.asyncio
    async def test_allows_within_daily_limit(self, mock_conn, sample_user):
        """Test that notifications under daily limit are allowed."""
        mock_conn.fetchval = AsyncMock(side_effect=[50, 5])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_blocks_at_daily_limit(self, mock_conn, sample_user):
        """Test that notifications at daily limit (100) are blocked."""
        mock_conn.fetchval = AsyncMock(return_value=100)

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Daily notification limit" in error

    @pytest.mark.asyncio
    async def test_blocks_at_hourly_limit(self, mock_conn, sample_user):
        """Test that notifications at hourly limit (10) are blocked."""
        mock_conn.fetchval = AsyncMock(side_effect=[50, 10])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Too many notifications" in error
