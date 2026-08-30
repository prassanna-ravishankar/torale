"""Admin connector-operation routes."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from webwhen.access import ClerkUser, require_admin
from webwhen.connectors import ComposioClientError, delete_connection, list_user_connections
from webwhen.core.database import Database, get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectorResetResponse(BaseModel):
    deleted_composio: int
    failed_composio: list[str]
    deleted_local: int


@router.post("/connectors/reset", response_model=ConnectorResetResponse)
async def admin_reset_connectors(
    user_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
) -> ConnectorResetResponse:
    """Hard-reset all connector state for a user across Composio and local DB."""
    try:
        conns = await list_user_connections(str(user_id))
    except ComposioClientError as e:
        logger.warning("Composio list failed for user %s: %s", user_id, e)
        conns = []

    deleted_composio = 0
    failed_composio: list[str] = []
    if conns:
        results = await asyncio.gather(
            *(delete_connection(conn.connected_account_id) for conn in conns),
            return_exceptions=True,
        )
        for conn, res in zip(conns, results, strict=True):
            if isinstance(res, Exception):
                logger.warning(
                    "Failed to delete Composio ca %s: %s", conn.connected_account_id, res
                )
                failed_composio.append(conn.connected_account_id)
            else:
                deleted_composio += 1
                logger.info(
                    "Admin %s deleted Composio ca %s for user %s",
                    admin.clerk_user_id,
                    conn.connected_account_id,
                    user_id,
                )

    deleted_rows = await db.fetch_all(
        "DELETE FROM user_connectors WHERE user_id = $1 RETURNING id",
        user_id,
    )
    deleted_local = len(deleted_rows)

    logger.info(
        "Admin %s reset connectors for user %s: composio=%d failed=%d local=%d",
        admin.clerk_user_id,
        user_id,
        deleted_composio,
        len(failed_composio),
        deleted_local,
    )
    return ConnectorResetResponse(
        deleted_composio=deleted_composio,
        failed_composio=failed_composio,
        deleted_local=deleted_local,
    )
