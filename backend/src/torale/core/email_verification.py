"""Email verification service to prevent spam and validate email ownership."""

import random
from datetime import datetime, timedelta
from uuid import UUID


class EmailVerificationService:
    """Handle email verification to prevent spam."""

    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_EXPIRY_MINUTES = 15
    MAX_VERIFICATION_ATTEMPTS = 5
    RATE_LIMIT_WINDOW_MINUTES = 60
    MAX_VERIFICATIONS_PER_HOUR = 3

    @staticmethod
    def generate_code() -> str:
        """Generate 6-digit verification code."""
        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    @staticmethod
    async def can_send_verification(conn, user_id: str) -> tuple[bool, str | None]:
        """
        Check if user can request another verification email.

        Returns: (can_send, error_message)
        """
        # Check rate limit: max 3 verifications per hour
        hour_ago = datetime.utcnow() - timedelta(minutes=60)
        recent_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM email_verifications
            WHERE user_id = $1 AND created_at > $2
            """,
            UUID(user_id),
            hour_ago,
        )

        if recent_count >= 3:
            return False, "Too many verification requests. Please try again later."

        return True, None

    @staticmethod
    async def create_verification(conn, user_id: str, email: str) -> tuple[bool, str, str | None]:
        """
        Create email verification record.

        Returns: (success, code_or_error, error_message)
        """
        # Check rate limit
        can_send, error = await EmailVerificationService.can_send_verification(conn, user_id)
        if not can_send:
            return False, "", error

        # Delete any existing unverified verification for this email
        await conn.execute(
            """
            DELETE FROM email_verifications
            WHERE user_id = $1 AND email = $2 AND verified = false
            """,
            UUID(user_id),
            email,
        )

        # Generate code and expiry
        code = EmailVerificationService.generate_code()
        expires_at = datetime.utcnow() + timedelta(
            minutes=EmailVerificationService.VERIFICATION_EXPIRY_MINUTES
        )

        # Insert verification record
        await conn.execute(
            """
            INSERT INTO email_verifications (user_id, email, verification_code, expires_at)
            VALUES ($1, $2, $3, $4)
            """,
            UUID(user_id),
            email,
            code,
            expires_at,
        )

        return True, code, None

    @staticmethod
    async def verify_code(conn, user_id: str, email: str, code: str) -> tuple[bool, str | None]:
        """
        Verify email with code.

        Returns: (success, error_message)
        """
        # Use transaction and row-level locking to prevent race conditions
        async with conn.transaction():
            # Get verification record and lock the row
            record = await conn.fetchrow(
                """
                SELECT * FROM email_verifications
                WHERE user_id = $1 AND email = $2 AND verified = false
                ORDER BY created_at DESC
                LIMIT 1
                FOR UPDATE
                """,
                UUID(user_id),
                email,
            )

            if not record:
                return False, "No verification pending for this email"

            # Check if expired
            if datetime.utcnow() > record["expires_at"]:
                return False, "Verification code expired. Request a new one."

            # Check attempts
            if record["attempts"] >= EmailVerificationService.MAX_VERIFICATION_ATTEMPTS:
                return False, "Too many failed attempts. Request a new code."

            # Check code
            if record["verification_code"] != code:
                # Increment attempts
                await conn.execute(
                    "UPDATE email_verifications SET attempts = attempts + 1 WHERE id = $1",
                    record["id"],
                )
                remaining = (
                    EmailVerificationService.MAX_VERIFICATION_ATTEMPTS - record["attempts"] - 1
                )
                return False, f"Invalid code. {remaining} attempts remaining."

            # Mark as verified
            await conn.execute(
                """
                UPDATE email_verifications
                SET verified = true, verified_at = NOW()
                WHERE id = $1
                """,
                record["id"],
            )

            # Add to user's verified emails list
            await conn.execute(
                """
                UPDATE users
                SET verified_notification_emails =
                    array_append(
                        COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                        $1
                    )
                WHERE id = $2 AND NOT ($1 = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[])))
                """,
                email,
                UUID(user_id),
            )

            return True, None

    @staticmethod
    async def is_email_verified(conn, user_id: str, email: str) -> bool:
        """
        Check if email is verified for user.

        Auto-verifies Clerk email (from users.email field).
        Also checks verified_notification_emails array for custom emails.
        """
        result = await conn.fetchrow(
            """
            SELECT
                email AS clerk_email,
                $1 = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
                    AS in_verified_array
            FROM users
            WHERE id = $2
            """,
            email,
            UUID(user_id),
        )

        if not result:
            return False

        # Clerk email is always verified
        if email == result["clerk_email"]:
            return True

        # Check verified array for custom emails
        return result["in_verified_array"] or False

    @staticmethod
    async def check_spam_limits(conn, user_id: str, email: str) -> tuple[bool, str | None]:
        """
        Check if user is within spam limits.

        Limits:
        - Max 100 notifications per day per user
        - Max 10 notifications per hour to same email address

        Returns: (allowed, error_message)
        """
        # Check daily limit per user
        day_ago = datetime.utcnow() - timedelta(days=1)
        daily_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM notification_sends
            WHERE user_id = $1 AND sent_at > $2
            """,
            UUID(user_id),
            day_ago,
        )

        if daily_count >= 100:
            return False, "Daily notification limit reached (100/day)"

        # Check hourly limit per email
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        hourly_count = await conn.fetchval(
            """
            SELECT COUNT(*) FROM notification_sends
            WHERE recipient_email = $1 AND sent_at > $2
            """,
            email,
            hour_ago,
        )

        if hourly_count >= 10:
            return False, f"Too many notifications to {email} (max 10/hour)"

        return True, None
