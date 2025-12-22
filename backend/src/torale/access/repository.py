from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Now

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class UserRepository(BaseRepository):
    """Repository for user operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.users = tables.users

    async def find_by_clerk_id(self, clerk_user_id: str) -> dict | None:
        """
        Find a user by Clerk user ID.

        Returns:
            User dict with id, clerk_user_id, email, username, first_name,
            is_active, role, created_at, updated_at, or None if not found.
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select("*")
            .where(self.users.clerk_user_id == Parameter("$1"))
        )
        return await self.db.fetch_one(str(query), clerk_user_id)

    async def find_by_email(self, email: str) -> dict | None:
        """
        Find a user by email address.

        Returns:
            User dict or None if not found.
        """
        query = (
            PostgreSQLQuery.from_(self.users).select("*").where(self.users.email == Parameter("$1"))
        )
        return await self.db.fetch_one(str(query), email)

    async def find_by_username(self, username: str) -> dict | None:
        """
        Find a user by username.

        Returns:
            User dict or None if not found.
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
        """
        Create a new user.

        Returns:
            Created user dict with all fields.
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
        """
        Update a user.

        Args:
            user_id: User UUID
            email: New email (optional)
            first_name: New first name (optional)
            username: New username (optional)
            is_active: New active status (optional)

        Returns:
            Updated user record dict.
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
            return await self.find_by_id(self.users, user_id)

        sql, params = self._build_update_query(self.users, user_id, data)
        return await self.db.fetch_one(sql, *params)

    async def get_webhook_config(self, user_id: UUID) -> dict | None:
        """
        Get user's webhook configuration.

        Returns:
            Dict with url, secret, enabled keys, or None if user not found.
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
    ) -> dict | None:
        """
        Update user's webhook configuration.

        Returns:
            Updated user record dict.
        """
        data = {
            "webhook_url": webhook_url,
            "webhook_enabled": webhook_enabled,
        }

        sql, params = self._build_update_query(self.users, user_id, data)
        row = await self.db.fetch_one(sql, *params)

        if not row:
            return None

        return {
            "url": str(row["webhook_url"]) if row["webhook_url"] else None,
            "secret": row["webhook_secret"],
            "enabled": row["webhook_enabled"],
        }

    async def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists.

        Returns:
            True if username is taken, False otherwise.
        """
        query = (
            PostgreSQLQuery.from_(self.users)
            .select("COUNT(*)")
            .where(self.users.username == Parameter("$1"))
        )

        count = await self.db.fetch_val(str(query), username)
        return count > 0


class ApiKeyRepository(BaseRepository):
    """Repository for API key operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.api_keys = tables.api_keys
        self.users = tables.users

    async def find_by_prefix(self, key_prefix: str) -> dict | None:
        """Find active API key by prefix with user info."""
        query = PostgreSQLQuery.from_(self.api_keys).select(
            self.api_keys.id.as_("key_id"),
            self.api_keys.user_id,
            self.api_keys.key_hash,
            self.users.clerk_user_id,
            self.users.email,
        )
        query = query.join(self.users).on(self.api_keys.user_id == self.users.id)
        query = query.where(self.api_keys.key_prefix == Parameter("$1"))
        query = query.where(self.api_keys.is_active.eq(True))

        return await self.db.fetch_one(str(query), key_prefix)

    async def create_key(self, user_id: UUID, key_prefix: str, key_hash: str, name: str) -> dict:
        """Create a new API key."""
        data = {
            "user_id": user_id,
            "key_prefix": key_prefix,
            "key_hash": key_hash,
            "name": name,
            "is_active": True,
        }

        sql, params = self._build_insert_query(self.api_keys, data)
        return await self.db.fetch_one(sql, *params)

    async def update_last_used(self, key_id: UUID) -> None:
        """Update the last_used_at timestamp for an API key."""
        query = (
            PostgreSQLQuery.update(self.api_keys)
            .set(self.api_keys.last_used_at, Now())
            .where(self.api_keys.id == Parameter("$1"))
        )
        await self.db.execute(str(query), key_id)

    async def revoke_key(self, key_id: UUID) -> dict:
        """Revoke (deactivate) an API key."""
        data = {"is_active": False}
        sql, params = self._build_update_query(self.api_keys, key_id, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_user(self, user_id: UUID, include_inactive: bool = False) -> list[dict]:
        """Find all API keys for a user."""
        query = PostgreSQLQuery.from_(self.api_keys).select("*")
        query = query.where(self.api_keys.user_id == Parameter("$1"))

        if not include_inactive:
            query = query.where(self.api_keys.is_active.eq(True))

        query = query.orderby(self.api_keys.created_at, order=Order.desc)

        return await self.db.fetch_all(str(query), user_id)
