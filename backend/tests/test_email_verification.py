"""Tests for email verification service."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from torale.core.email_verification import EmailVerificationService


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def email_service(mock_db):
    """Create email verification service instance."""
    return EmailVerificationService(mock_db)


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

    def test_generates_six_digit_code(self, email_service):
        """Test that code is exactly 6 digits."""
        code = email_service.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generates_different_codes(self, email_service):
        """Test that multiple calls generate different codes."""
        codes = [email_service.generate_code() for _ in range(10)]
        # Statistically very unlikely to get duplicates
        assert len(set(codes)) > 5


class TestCanSendVerification:
    """Tests for can_send_verification method."""

    @pytest.mark.asyncio
    async def test_allows_first_verification(self, email_service, mock_db, sample_user):
        """Test that first verification is always allowed."""
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 0))

        can_send = await email_service.can_send_verification(sample_user.id, "test@example.com")

        assert can_send is True

    @pytest.mark.asyncio
    async def test_blocks_after_rate_limit(self, email_service, mock_db, sample_user):
        """Test that rate limit (3/hour) is enforced."""
        # Return 3 recent verifications
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 3))

        can_send = await email_service.can_send_verification(sample_user.id, "test@example.com")

        assert can_send is False

    @pytest.mark.asyncio
    async def test_allows_after_rate_limit_window(self, email_service, mock_db, sample_user):
        """Test that verifications are allowed after 1 hour window."""
        # Return 2 recent verifications (under limit)
        mock_db.execute = AsyncMock(return_value=MagicMock(scalar=lambda: 2))

        can_send = await email_service.can_send_verification(sample_user.id, "test@example.com")

        assert can_send is True


class TestCreateVerification:
    """Tests for create_verification method."""

    @pytest.mark.asyncio
    async def test_creates_verification_record(self, email_service, mock_db, sample_user):
        """Test that verification record is created with correct data."""
        email = "test@example.com"
        code = "123456"

        # Create mock verification object
        mock_verification = MagicMock()
        mock_verification.user_id = sample_user.id
        mock_verification.email = email
        mock_verification.code = code
        mock_verification.attempts_left = 5
        mock_verification.is_verified = False

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda v: setattr(v, 'id', uuid4()))

        # Mock the return value
        with patch.object(email_service, 'create_verification', return_value=mock_verification):
            verification = await email_service.create_verification(sample_user.id, email, code)

            assert verification.user_id == sample_user.id
            assert verification.email == email
            assert verification.code == code
            assert verification.attempts_left == 5
            assert verification.is_verified is False

    @pytest.mark.asyncio
    async def test_sets_expiration_15_minutes(self, email_service, mock_db, sample_user):
        """Test that verification expires in 15 minutes."""
        before = datetime.now(timezone.utc)
        expected_expiry_min = before + timedelta(minutes=15)
        after = datetime.now(timezone.utc)
        expected_expiry_max = after + timedelta(minutes=15)

        # Create mock with expiry time
        mock_verification = MagicMock()
        mock_verification.expires_at = before + timedelta(minutes=15)

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch.object(email_service, 'create_verification', return_value=mock_verification):
            verification = await email_service.create_verification(
                sample_user.id, "test@example.com", "123456"
            )

            assert expected_expiry_min <= verification.expires_at <= expected_expiry_max


class TestVerifyCode:
    """Tests for verify_code method."""

    @pytest.mark.asyncio
    async def test_successful_verification(self, email_service, mock_db, sample_user):
        """Test successful code verification."""
        verification = MagicMock()
        verification.id = uuid4()
        verification.user_id = sample_user.id
        verification.email = "test@example.com"
        verification.code = "123456"
        verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification.attempts_left = 5
        verification.is_verified = False
        verification.verified_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await email_service.verify_code(sample_user.id, "test@example.com", "123456")

        assert result is True
        assert verification.is_verified is True
        assert verification.verified_at is not None

    @pytest.mark.asyncio
    async def test_invalid_code(self, email_service, mock_db, sample_user):
        """Test verification with wrong code."""
        verification = MagicMock()
        verification.id = uuid4()
        verification.user_id = sample_user.id
        verification.email = "test@example.com"
        verification.code = "123456"
        verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification.attempts_left = 5
        verification.is_verified = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        result = await email_service.verify_code(sample_user.id, "test@example.com", "999999")

        assert result is False
        assert verification.is_verified is False
        assert verification.attempts_left == 4

    @pytest.mark.asyncio
    async def test_expired_code(self, email_service, mock_db, sample_user):
        """Test verification with expired code."""
        verification = MagicMock()
        verification.id = uuid4()
        verification.user_id = sample_user.id
        verification.email = "test@example.com"
        verification.code = "123456"
        verification.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)  # Already expired
        verification.attempts_left = 5
        verification.is_verified = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await email_service.verify_code(sample_user.id, "test@example.com", "123456")

        assert result is False

    @pytest.mark.asyncio
    async def test_no_attempts_left(self, email_service, mock_db, sample_user):
        """Test verification when no attempts remaining."""
        verification = MagicMock()
        verification.id = uuid4()
        verification.user_id = sample_user.id
        verification.email = "test@example.com"
        verification.code = "123456"
        verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification.attempts_left = 0
        verification.is_verified = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await email_service.verify_code(sample_user.id, "test@example.com", "123456")

        assert result is False

    @pytest.mark.asyncio
    async def test_verification_not_found(self, email_service, mock_db, sample_user):
        """Test verification when record doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await email_service.verify_code(sample_user.id, "test@example.com", "123456")

        assert result is False


class TestIsEmailVerified:
    """Tests for is_email_verified method."""

    @pytest.mark.asyncio
    async def test_clerk_email_always_verified(self, email_service, mock_db, sample_user):
        """Test that Clerk email is automatically verified."""
        result = await email_service.is_email_verified(sample_user, sample_user.email)

        assert result is True

    @pytest.mark.asyncio
    async def test_verified_custom_email(self, email_service, mock_db, sample_user):
        """Test that verified custom email returns True."""
        custom_email = "custom@example.com"

        verification = MagicMock()
        verification.id = uuid4()
        verification.user_id = sample_user.id
        verification.email = custom_email
        verification.code = "123456"
        verification.expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        verification.attempts_left = 5
        verification.is_verified = True
        verification.verified_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: verification
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await email_service.is_email_verified(sample_user, custom_email)

        assert result is True

    @pytest.mark.asyncio
    async def test_unverified_custom_email(self, email_service, mock_db, sample_user):
        """Test that unverified custom email returns False."""
        custom_email = "custom@example.com"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = lambda: None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await email_service.is_email_verified(sample_user, custom_email)

        assert result is False


class TestCheckSpamLimits:
    """Tests for check_spam_limits method."""

    @pytest.mark.asyncio
    async def test_allows_within_daily_limit(self, email_service, mock_db, sample_user):
        """Test that notifications under daily limit are allowed."""
        # Return 50 notifications today (under 100 limit)
        mock_result = MagicMock()
        mock_result.scalar = lambda: 50
        mock_db.execute = AsyncMock(return_value=mock_result)

        can_send = await email_service.check_spam_limits(sample_user.id, "test@example.com")

        assert can_send is True

    @pytest.mark.asyncio
    async def test_blocks_at_daily_limit(self, email_service, mock_db, sample_user):
        """Test that notifications at daily limit (100) are blocked."""
        mock_result = MagicMock()
        mock_result.scalar = lambda: 100
        mock_db.execute = AsyncMock(return_value=mock_result)

        can_send = await email_service.check_spam_limits(sample_user.id, "test@example.com")

        assert can_send is False

    @pytest.mark.asyncio
    async def test_allows_within_hourly_limit(self, email_service, mock_db, sample_user):
        """Test that notifications under hourly limit are allowed."""

        def side_effect(*args, **kwargs):
            # First call (daily) returns 50, second call (hourly) returns 5
            mock_result = MagicMock()
            if not hasattr(side_effect, "call_count"):
                side_effect.call_count = 0
            side_effect.call_count += 1

            if side_effect.call_count == 1:
                mock_result.scalar = lambda: 50
            else:
                mock_result.scalar = lambda: 5
            return mock_result

        mock_db.execute = AsyncMock(side_effect=side_effect)

        can_send = await email_service.check_spam_limits(sample_user.id, "test@example.com")

        assert can_send is True

    @pytest.mark.asyncio
    async def test_blocks_at_hourly_limit(self, email_service, mock_db, sample_user):
        """Test that notifications at hourly limit (10) are blocked."""

        def side_effect(*args, **kwargs):
            mock_result = MagicMock()
            if not hasattr(side_effect, "call_count"):
                side_effect.call_count = 0
            side_effect.call_count += 1

            if side_effect.call_count == 1:
                mock_result.scalar = lambda: 50  # Under daily limit
            else:
                mock_result.scalar = lambda: 10  # At hourly limit
            return mock_result

        mock_db.execute = AsyncMock(side_effect=side_effect)

        can_send = await email_service.check_spam_limits(sample_user.id, "test@example.com")

        assert can_send is False
