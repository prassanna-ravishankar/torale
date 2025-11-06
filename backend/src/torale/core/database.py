import asyncpg

from torale.core.config import settings


class Database:
    """Database connection pool manager"""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """Create database connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def fetch_one(self, query: str, *args):
        """Fetch a single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch_all(self, query: str, *args):
        """Fetch all rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query: str, *args):
        """Execute a query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args_list):
        """Execute a query multiple times with different parameters"""
        async with self.pool.acquire() as conn:
            return await conn.executemany(query, args_list)


# Global database instance
db = Database()


def get_db() -> Database:
    """Get database instance for dependency injection"""
    return db
