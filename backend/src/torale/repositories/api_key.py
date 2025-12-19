from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Now

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class ApiKeyRepository(BaseRepository):
    """Repository for API key operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.api_keys = tables.api_keys
        self.users = tables.users

    async def find_by_hash(self, key_hash: str) -> dict | None:
        """Find active API key by hash with user info.

        Args:
            key_hash: SHA256 hash of the API key

        Returns:
            Dict with key and user info or None
        """
        query = PostgreSQLQuery.from_(self.api_keys).select(
            self.api_keys.id.as_("key_id"),
            self.api_keys.user_id,
            self.users.clerk_user_id,
            self.users.email,
        )
        query = query.join(self.users).on(self.api_keys.user_id == self.users.id)
        query = query.where(self.api_keys.key_hash == Parameter("$1"))
        query = query.where(self.api_keys.is_active.eq(True))

        return await self.db.fetch_one(str(query), key_hash)

    async def create_key(self, user_id: UUID, key_prefix: str, key_hash: str, name: str) -> dict:
        """Create a new API key.

        Args:
            user_id: User UUID
            key_prefix: Display prefix (e.g., "sk_...abc123")
            key_hash: SHA256 hash of the actual key
            name: User-defined name

        Returns:
            Created API key record
        """
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
        """Update the last_used_at timestamp for an API key.

        Args:
            key_id: API key UUID
        """
        query = (
            PostgreSQLQuery.update(self.api_keys)
            .set(self.api_keys.last_used_at, Now())
            .where(self.api_keys.id == Parameter("$1"))
        )
        await self.db.execute(str(query), key_id)

    async def revoke_key(self, key_id: UUID) -> dict:
        """Revoke (deactivate) an API key.

        Args:
            key_id: API key UUID

        Returns:
            Updated API key record
        """
        data = {"is_active": False}
        sql, params = self._build_update_query(self.api_keys, key_id, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_user(self, user_id: UUID, include_inactive: bool = False) -> list[dict]:
        """Find all API keys for a user.

        Args:
            user_id: User UUID
            include_inactive: Whether to include revoked keys

        Returns:
            List of API key records
        """
        query = PostgreSQLQuery.from_(self.api_keys).select("*")
        query = query.where(self.api_keys.user_id == Parameter("$1"))

        if not include_inactive:
            query = query.where(self.api_keys.is_active.eq(True))

        query = query.orderby(self.api_keys.created_at, order=Order.desc)

        return await self.db.fetch_all(str(query), user_id)
