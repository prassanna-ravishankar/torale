"""Tests for email verification service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from torale.core.email_verification import EmailVerificationService


@pytest.fixture
def mock_conn():
    """Mock database connection."""
    conn = AsyncMock()
    return conn


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = MagicMock()
    user.id = uuid4()
    user.clerk_user_id = "user_test123"
    user.email = "user@example.com"
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


class TestGenerateCode:
    """Tests for generate_code method."""

    def test_generates_six_digit_code(self):
        """Test that code is exactly 6 digits."""
        code = EmailVerificationService.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generates_different_codes(self):
        """Test that multiple calls generate different codes."""
        codes = [EmailVerificationService.generate_code() for _ in range(10)]
        # Statistically very unlikely to get duplicates
        assert len(set(codes)) > 5


class TestCanSendVerification:
    """Tests for can_send_verification method."""

    @pytest.mark.asyncio
    async def test_allows_first_verification(self, mock_conn, sample_user):
        """Test that first verification is always allowed."""
        mock_conn.fetchval = AsyncMock(return_value=0)

        can_send, error = await EmailVerificationService.can_send_verification(mock_conn, str(sample_user.id))

        assert can_send is True
        assert error is None

    @pytest.mark.asyncio
    async def test_blocks_after_rate_limit(self, mock_conn, sample_user):
        """Test that rate limit (3/hour) is enforced."""
        # Return 3 recent verifications
        mock_conn.fetchval = AsyncMock(return_value=3)

        can_send, error = await EmailVerificationService.can_send_verification(mock_conn, str(sample_user.id))

        assert can_send is False
        assert "Too many verification requests" in error

    @pytest.mark.asyncio
    async def test_allows_after_rate_limit_window(self, mock_conn, sample_user):
        """Test that verifications are allowed after 1 hour window."""
        # Return 2 recent verifications (under limit)
        mock_conn.fetchval = AsyncMock(return_value=2)

        can_send, error = await EmailVerificationService.can_send_verification(mock_conn, str(sample_user.id))

        assert can_send is True
        assert error is None


class TestCreateVerification:
    """Tests for create_verification method."""

    @pytest.mark.asyncio
    async def test_creates_verification_record(self, mock_conn, sample_user):
        """Test that verification record is created successfully."""
        email = "test@example.com"

        # Mock rate limit check - allow sending
        mock_conn.fetchval = AsyncMock(return_value=0)
        mock_conn.execute = AsyncMock()

        success, code, error = await EmailVerificationService.create_verification(
            mock_conn, str(sample_user.id), email
        )

        assert success is True
        assert len(code) == 6
        assert code.isdigit()
        assert error is None
        # Verify database calls were made
        assert mock_conn.execute.call_count == 2  # DELETE + INSERT

    @pytest.mark.asyncio
    async def test_sets_expiration_15_minutes(self, mock_conn, sample_user):
        """Test that verification uses 15 minute expiry (constant is 15)."""
        # Mock rate limit check
        mock_conn.fetchval = AsyncMock(return_value=0)
        mock_conn.execute = AsyncMock()

        success, code, error = await EmailVerificationService.create_verification(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert success is True
        # Just verify the constant is set to 15 minutes
        assert EmailVerificationService.VERIFICATION_EXPIRY_MINUTES == 15


class TestVerifyCode:
    """Tests for verify_code method."""

    @pytest.mark.asyncio
    async def test_successful_verification(self, mock_conn, sample_user):
        """Test successful code verification."""
        # Mock transaction context
        class MockTransaction:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_conn.transaction = MagicMock(return_value=MockTransaction())

        # Mock verification record (not expired, has attempts left, correct code)
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": uuid4(),
            "user_id": sample_user.id,
            "email": "test@example.com",
            "verification_code": "123456",
            "expires_at": datetime.utcnow() + timedelta(minutes=10),
            "attempts": 0,
            "verified": False,
        })
        mock_conn.execute = AsyncMock()

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_invalid_code(self, mock_conn, sample_user):
        """Test verification with wrong code."""
        class MockTransaction:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": uuid4(),
            "user_id": sample_user.id,
            "email": "test@example.com",
            "verification_code": "123456",
            "expires_at": datetime.utcnow() + timedelta(minutes=10),
            "attempts": 0,
            "verified": False,
        })
        mock_conn.execute = AsyncMock()

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "999999"
        )

        assert success is False
        assert "Invalid code" in error

    @pytest.mark.asyncio
    async def test_expired_code(self, mock_conn, sample_user):
        """Test verification with expired code."""
        class MockTransaction:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": uuid4(),
            "user_id": sample_user.id,
            "email": "test@example.com",
            "verification_code": "123456",
            "expires_at": datetime.utcnow() - timedelta(minutes=1),  # Already expired
            "attempts": 0,
            "verified": False,
        })

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is False
        assert "expired" in error.lower()

    @pytest.mark.asyncio
    async def test_no_attempts_left(self, mock_conn, sample_user):
        """Test verification when no attempts remaining."""
        class MockTransaction:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_conn.transaction = MagicMock(return_value=MockTransaction())
        mock_conn.fetchrow = AsyncMock(return_value={
            "id": uuid4(),
            "user_id": sample_user.id,
            "email": "test@example.com",
            "verification_code": "123456",
            "expires_at": datetime.utcnow() + timedelta(minutes=10),
            "attempts": 5,  # Max attempts reached
            "verified": False,
        })

        success, error = await EmailVerificationService.verify_code(
            mock_conn, str(sample_user.id), "test@example.com", "123456"
        )

        assert success is False
        assert "Too many" in error

    @pytest.mark.asyncio
    async def test_verification_not_found(self, mock_conn, sample_user):
        """Test verification when record doesn't exist."""
        class MockTransaction:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

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
        # Mock return: email matches clerk_email
        mock_conn.fetchrow = AsyncMock(return_value={
            "clerk_email": sample_user.email,
            "in_verified_array": False,
        })

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), sample_user.email
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verified_custom_email(self, mock_conn, sample_user):
        """Test that verified custom email returns True."""
        custom_email = "custom@example.com"

        # Mock return: custom email is in verified array
        mock_conn.fetchrow = AsyncMock(return_value={
            "clerk_email": sample_user.email,
            "in_verified_array": True,
        })

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), custom_email
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_unverified_custom_email(self, mock_conn, sample_user):
        """Test that unverified custom email returns False."""
        custom_email = "custom@example.com"

        # Mock return: custom email not in verified array
        mock_conn.fetchrow = AsyncMock(return_value={
            "clerk_email": sample_user.email,
            "in_verified_array": False,
        })

        result = await EmailVerificationService.is_email_verified(
            mock_conn, str(sample_user.id), custom_email
        )

        assert result is False


class TestCheckSpamLimits:
    """Tests for check_spam_limits method."""

    @pytest.mark.asyncio
    async def test_allows_within_daily_limit(self, mock_conn, sample_user):
        """Test that notifications under daily limit are allowed."""
        # Mock fetchval to return counts: 50 daily, 5 hourly (both under limit)
        mock_conn.fetchval = AsyncMock(side_effect=[50, 5])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_blocks_at_daily_limit(self, mock_conn, sample_user):
        """Test that notifications at daily limit (100) are blocked."""
        # Mock fetchval to return 100 for daily count (at limit)
        mock_conn.fetchval = AsyncMock(return_value=100)

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Daily notification limit" in error

    @pytest.mark.asyncio
    async def test_allows_within_hourly_limit(self, mock_conn, sample_user):
        """Test that notifications under hourly limit are allowed."""
        # Mock fetchval: 50 daily (OK), 5 hourly (OK)
        mock_conn.fetchval = AsyncMock(side_effect=[50, 5])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_blocks_at_hourly_limit(self, mock_conn, sample_user):
        """Test that notifications at hourly limit (10) are blocked."""
        # Mock fetchval: 50 daily (OK), 10 hourly (at limit)
        mock_conn.fetchval = AsyncMock(side_effect=[50, 10])

        allowed, error = await EmailVerificationService.check_spam_limits(
            mock_conn, str(sample_user.id), "test@example.com"
        )

        assert allowed is False
        assert "Too many notifications" in error
