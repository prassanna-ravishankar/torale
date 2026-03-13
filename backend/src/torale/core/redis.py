import logging

import redis.asyncio as redis

from torale.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis connection manager for async view counting."""

    def __init__(self):
        self.client: redis.Redis | None = None

    async def connect(self):
        """Create Redis connection. No-op if Redis is not configured."""
        if self.client is not None or not settings.redis_host:
            if not settings.redis_host:
                logger.info("Redis not configured, view counting disabled")
            return
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                username="default",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception:
            logger.warning("Redis connection failed, view counting disabled", exc_info=True)
            self.client = None

    async def disconnect(self):
        """Close Redis connection."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None


redis_client = RedisClient()
