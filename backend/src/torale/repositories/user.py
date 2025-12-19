from uuid import UUID

from pypika_tortoise import Parameter, PostgreSQLQuery

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class UserRepository(BaseRepository):
    """Repository for user operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.users = tables.users

    async def find_by_clerk_id(self, clerk_user_id: str) -> dict | None:
        """Find a user by Clerk user ID.

        Args:
            clerk_user_id: Clerk user identifier

        Returns:
            User record dict or None if not found
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select("*")
            .where(self.users.clerk_user_id == Parameter("$1"))
        )
        return await self.db.fetch_one(str(query), clerk_user_id)

    async def find_by_email(self, email: str) -> dict | None:
        """Find a user by email address.

        Args:
            email: User email address

        Returns:
            User record dict or None if not found
        """
        query = (
            PostgreSQLQuery.from_(self.users).select("*").where(self.users.email == Parameter("$1"))
        )
        return await self.db.fetch_one(str(query), email)

    async def find_by_username(self, username: str) -> dict | None:
        """Find a user by username.

        Args:
            username: Username

        Returns:
            User record dict or None if not found
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select("*")
            .where(self.users.username == Parameter("$1"))
        )
        return await self.db.fetch_one(str(query), username)

    async def create_user(
        self, clerk_user_id: str, email: str, first_name: str | None = None
    ) -> dict:
        """Create a new user.

        Args:
            clerk_user_id: Clerk user identifier
            email: User email address
            first_name: User first name (optional)

        Returns:
            Created user record dict
        """
        data = {
            "clerk_user_id": clerk_user_id,
            "email": email,
            "is_active": True,
        }

        if first_name:
            data["first_name"] = first_name

        sql, params = self._build_insert_query(self.users, data)
        return await self.db.fetch_one(sql, *params)

    async def update_user(
        self,
        user_id: UUID,
        email: str | None = None,
        first_name: str | None = None,
        username: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        """Update a user.

        Args:
            user_id: User UUID
            email: New email (optional)
            first_name: New first name (optional)
            username: New username (optional)
            is_active: New active status (optional)

        Returns:
            Updated user record dict
        """
        data = {}

        if email is not None:
            data["email"] = email
        if first_name is not None:
            data["first_name"] = first_name
        if username is not None:
            data["username"] = username
        if is_active is not None:
            data["is_active"] = is_active

        if not data:
            # No fields to update, fetch and return current user
            return await self.find_by_id(self.users, user_id)

        sql, params = self._build_update_query(self.users, user_id, data)
        return await self.db.fetch_one(sql, *params)

    async def get_webhook_config(self, user_id: UUID) -> dict:
        """Get user's webhook configuration.

        Args:
            user_id: User UUID

        Returns:
            Dict with webhook_url, webhook_secret, webhook_enabled
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select(self.users.webhook_url, self.users.webhook_enabled, self.users.webhook_secret)
            .where(self.users.id == Parameter("$1"))
        )

        row = await self.db.fetch_one(str(query), user_id)

        if not row:
            return None

        return {
            "url": str(row["webhook_url"]) if row["webhook_url"] else None,
            "secret": row["webhook_secret"],
            "enabled": row["webhook_enabled"],
        }

    async def update_webhook_config(
        self, user_id: UUID, webhook_url: str | None, webhook_enabled: bool
    ) -> dict:
        """Update user's webhook configuration.

        Args:
            user_id: User UUID
            webhook_url: Webhook URL (can be None to disable)
            webhook_enabled: Whether webhooks are enabled

        Returns:
            Updated webhook config dict
        """
        data = {
            "webhook_url": webhook_url,
            "webhook_enabled": webhook_enabled,
        }

        sql, params = self._build_update_query(self.users, user_id, data)
        await self.db.execute(sql, *params)

        return await self.get_webhook_config(user_id)

    async def username_exists(self, username: str) -> bool:
        """Check if a username already exists.

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select("COUNT(*)")
            .where(self.users.username == Parameter("$1"))
        )

        count = await self.db.fetch_val(str(query), username)
        return count > 0
