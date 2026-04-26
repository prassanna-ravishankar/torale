"""Resolve a task's attached connectors to per-run MCP server descriptors.

Called by the scheduler at run time (not at task-save time) so newly-expired
or newly-connected toolkits are picked up on the next run without touching
the task record. See design memo §10.1 D4.
"""

import asyncio
import logging
from uuid import UUID

from pydantic import BaseModel

from torale.connectors import ComposioClientError, generate_mcp_url, get_toolkit
from torale.core.database import Database

logger = logging.getLogger(__name__)


class McpServerDescriptor(BaseModel):
    """One MCP server endpoint passed to the agent via A2A metadata."""

    toolkit: str
    url: str


async def resolve_mcp_servers(
    db: Database,
    user_id: UUID,
    attached_slugs: list[str] | None,
) -> list[McpServerDescriptor]:
    """Return MCP server descriptors for a task's ACTIVE attached connectors.

    Intersects `attached_slugs` with the user's ACTIVE rows in `user_connectors`.
    Silently drops slugs that are unknown, not connected, or not ACTIVE — the
    agent just sees fewer tools; the UI surfaces the degraded state separately.
    """
    if not attached_slugs:
        return []

    rows = await db.fetch_all(
        """
        SELECT toolkit_slug FROM user_connectors
        WHERE user_id = $1
            AND toolkit_slug = ANY($2::text[])
            AND status = 'ACTIVE'
        """,
        user_id,
        attached_slugs,
    )
    active_slugs = {r["toolkit_slug"] for r in rows}

    slugs_to_resolve: list[str] = []
    for slug in attached_slugs:
        if slug not in active_slugs:
            continue
        if get_toolkit(slug) is None:
            logger.warning("Task references unknown toolkit %r; skipping", slug)
            continue
        slugs_to_resolve.append(slug)

    if not slugs_to_resolve:
        return []

    results = await asyncio.gather(
        *(generate_mcp_url(str(user_id), slug) for slug in slugs_to_resolve),
        return_exceptions=True,
    )

    servers: list[McpServerDescriptor] = []
    for slug, res in zip(slugs_to_resolve, results, strict=True):
        if isinstance(res, ComposioClientError):
            logger.warning("generate_mcp_url failed for %s/%s: %s", user_id, slug, res)
            continue
        if isinstance(res, Exception):
            logger.error(
                "Unexpected error resolving MCP URL for %s/%s",
                user_id,
                slug,
                exc_info=res,
            )
            continue
        servers.append(McpServerDescriptor(toolkit=slug, url=res.url))

    return servers


async def mark_connectors_used(
    db: Database,
    user_id: UUID,
    toolkit_slugs: list[str],
) -> None:
    """Update last_used_at for the given user's connector rows. Best-effort."""
    if not toolkit_slugs:
        return
    try:
        await db.execute(
            """
            UPDATE user_connectors
            SET last_used_at = NOW(), updated_at = NOW()
            WHERE user_id = $1 AND toolkit_slug = ANY($2::text[])
            """,
            user_id,
            toolkit_slugs,
        )
    except Exception as e:
        logger.warning("mark_connectors_used failed for %s: %s", user_id, e)
