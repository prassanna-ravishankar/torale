from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class EmailVerificationRepository(BaseRepository):
    """Repository for email verification operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.verifications = tables.email_verifications

    async def create_verification(
        self,
        user_id: UUID,
        email: str,
        verification_code: str,
        expires_at: str,
    ) -> dict:
        """Create a new email verification.

        Args:
            user_id: User UUID
            email: Email address to verify
            verification_code: Verification code
            expires_at: Expiration timestamp

        Returns:
            Created verification record
        """
        data = {
            "user_id": user_id,
            "email": email,
            "verification_code": verification_code,
            "verified": False,
            "expires_at": expires_at,
            "attempts": 0,
        }

        sql, params = self._build_insert_query(self.verifications, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_code(self, verification_code: str) -> dict | None:
        """Find verification by code.

        Args:
            verification_code: Verification code to find

        Returns:
            Verification record or None
        """
        query = PostgreSQLQuery.from_(self.verifications).select("*")
        query = query.where(self.verifications.verification_code == Parameter("$1"))
        query = query.where(self.verifications.verified == False)  # noqa: E712

        return await self.db.fetch_one(str(query), verification_code)

    async def mark_verified(self, verification_id: UUID) -> dict:
        """Mark verification as verified.

        Args:
            verification_id: Verification UUID

        Returns:
            Updated verification record
        """
        query = f"""
            UPDATE {self.verifications.get_table_name()}
            SET verified = true, verified_at = NOW()
            WHERE id = $1
            RETURNING *
        """
        return await self.db.fetch_one(query, verification_id)

    async def increment_attempts(self, verification_id: UUID) -> dict:
        """Increment verification attempt count.

        Args:
            verification_id: Verification UUID

        Returns:
            Updated verification record
        """
        query = f"""
            UPDATE {self.verifications.get_table_name()}
            SET attempts = attempts + 1
            WHERE id = $1
            RETURNING *
        """
        return await self.db.fetch_one(query, verification_id)

    async def find_pending_by_user_email(self, user_id: UUID, email: str) -> dict | None:
        """Find pending verification for user and email.

        Args:
            user_id: User UUID
            email: Email address

        Returns:
            Verification record or None
        """
        query = PostgreSQLQuery.from_(self.verifications).select("*")
        query = query.where(self.verifications.user_id == Parameter("$1"))
        query = query.where(self.verifications.email == Parameter("$2"))
        query = query.where(self.verifications.verified == False)  # noqa: E712

        return await self.db.fetch_one(str(query), user_id, email)

    async def count_recent_verifications(self, user_id: UUID, hours: int = 24) -> int:
        """Count verifications created in recent hours for spam prevention.

        Args:
            user_id: User UUID
            hours: Number of hours to look back

        Returns:
            Count of recent verifications
        """
        # Use parameterized query to prevent SQL injection
        # PostgreSQL allows INTERVAL with concatenation: INTERVAL '1 hour' * N
        query = f"""
            SELECT COUNT(*)
            FROM {self.verifications.get_table_name()}
            WHERE user_id = $1
              AND created_at > NOW() - (INTERVAL '1 hour' * $2)
        """
        return await self.db.fetch_val(query, user_id, hours) or 0

    async def find_by_user(self, user_id: UUID, limit: int = 50) -> list[dict]:
        """Find all verifications for a user.

        Args:
            user_id: User UUID
            limit: Maximum results

        Returns:
            List of verification records
        """
        query = PostgreSQLQuery.from_(self.verifications).select("*")
        query = query.where(self.verifications.user_id == Parameter("$1"))
        query = query.orderby(self.verifications.created_at, order=Order.desc)
        query = query.limit(limit)

        return await self.db.fetch_all(str(query), user_id)
