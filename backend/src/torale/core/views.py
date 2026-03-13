import asyncio
import logging
from uuid import UUID

from redis.exceptions import RedisError, ResponseError

from torale.core.database import db
from torale.core.redis import redis_client

logger = logging.getLogger(__name__)

TASK_VIEWS_KEY = "task_views"
_PROCESSING_KEY = f"{TASK_VIEWS_KEY}:processing"


async def _increment_view(task_id: UUID) -> None:
    try:
        await redis_client.client.hincrby(TASK_VIEWS_KEY, str(task_id), 1)
    except RedisError:
        logger.debug("Redis view increment failed", exc_info=True)


def increment_view(task_id: UUID) -> None:
    """Fire-and-forget view count increment. Does not block the caller."""
    if redis_client.client is None:
        return
    asyncio.create_task(_increment_view(task_id))


async def flush_views_to_postgres() -> None:
    """Sync accumulated Redis view counts to Postgres, then clear."""
    if redis_client.client is None:
        return

    # Atomically swap the key so no increments are lost during flush
    try:
        await redis_client.client.rename(TASK_VIEWS_KEY, _PROCESSING_KEY)
    except ResponseError as e:
        if "no such key" in str(e).lower():
            return  # Nothing to flush
        logger.warning("Failed to rename task_views key", exc_info=True)
        return

    try:
        counts = await redis_client.client.hgetall(_PROCESSING_KEY)
        if not counts:
            await redis_client.client.delete(_PROCESSING_KEY)
            return

        updates = []
        for task_id, count_str in counts.items():
            n = int(count_str)
            if n > 0:
                updates.append((n, task_id))

        if not updates:
            await redis_client.client.delete(_PROCESSING_KEY)
            return

        await db.executemany(
            "UPDATE tasks SET view_count = view_count + $1 WHERE id = $2::uuid",
            updates,
        )
        await redis_client.client.delete(_PROCESSING_KEY)
        logger.info("Flushed view counts for %d tasks", len(updates))
    except Exception:
        logger.error(
            "Failed to flush view counts. Counts remain in '%s' for recovery.",
            _PROCESSING_KEY,
            exc_info=True,
        )
