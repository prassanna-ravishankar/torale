from pypika_tortoise import Parameter, PostgreSQLQuery

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class WaitlistRepository(BaseRepository):
    """Repository for waitlist operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.waitlist = tables.waitlist

    async def add_email(self, email: str) -> dict:
        """Add email to waitlist.

        Args:
            email: Email address to add

        Returns:
            Created waitlist record
        """
        data = {"email": email}

        sql, params = self._build_insert_query(self.waitlist, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_email(self, email: str) -> dict | None:
        """Find waitlist entry by email.

        Args:
            email: Email address to find

        Returns:
            Waitlist record or None
        """
        query = PostgreSQLQuery.from_(self.waitlist).select("*")
        query = query.where(self.waitlist.email == Parameter("$1"))

        return await self.db.fetch_one(str(query), email)

    async def email_exists(self, email: str) -> bool:
        """Check if email is already on waitlist.

        Args:
            email: Email to check

        Returns:
            True if email exists
        """
        result = await self.find_by_email(email)
        return result is not None
