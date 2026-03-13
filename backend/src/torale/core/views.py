import asyncio
import logging
from uuid import UUID

from torale.core.database import db
from torale.core.redis import redis_client

logger = logging.getLogger(__name__)

TASK_VIEWS_KEY = "task_views"


async def _increment_view(task_id: UUID) -> None:
    try:
        await redis_client.client.hincrby(TASK_VIEWS_KEY, str(task_id), 1)
    except Exception:
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
    try:
        counts = await redis_client.client.hgetall(TASK_VIEWS_KEY)
        if not counts:
            return

        updates = []
        flushed_keys = []
        for task_id, count in counts.items():
            n = int(count)
            if n > 0:
                updates.append((n, task_id))
                flushed_keys.append(task_id)

        if not updates:
            return

        await db.executemany(
            "UPDATE tasks SET view_count = view_count + $1 WHERE id = $2::uuid",
            updates,
        )
        await redis_client.client.hdel(TASK_VIEWS_KEY, *flushed_keys)
        logger.info("Flushed view counts for %d tasks", len(updates))
    except Exception:
        logger.warning("Failed to flush view counts", exc_info=True)
