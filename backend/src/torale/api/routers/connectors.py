"""Connector management endpoints.

Surfaces:
- GET  /connectors/available — supported toolkits (for the settings page grid)
- GET  /connectors            — current user's connections (merged DB + Composio)
- POST /connectors/{toolkit}/connect — start OAuth, return redirect URL
- DELETE /connectors/{toolkit} — revoke connection
- GET  /connectors/callback   — backend HTML page Composio redirects to

See design memo §3 and §10.1. User-facing copy lives here; everything else
about Composio specifics lives in torale.connectors.client.
"""

from __future__ import annotations

import logging
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from torale.access import CurrentUser
from torale.connectors import (
    TOOLKIT_REGISTRY,
    ComposioClientError,
    delete_connection,
    get_toolkit,
    initiate_connection,
    list_user_connections,
)
from torale.connectors.client import ConnectionStatus
from torale.core.config import settings
from torale.core.database import Database, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors", tags=["connectors"])


class AvailableToolkit(BaseModel):
    """One supported toolkit, for the settings page grid."""

    slug: str
    display_name: str
    description: str


class UserConnection(BaseModel):
    """One user's connection to one toolkit, as returned to the frontend."""

    toolkit_slug: str
    display_name: str
    status: ConnectionStatus | None = None
    status_reason: str | None = None
    connected_at: datetime | None = None
    last_used_at: datetime | None = None


class InitiateResponse(BaseModel):
    """Response from POST /connectors/{toolkit}/connect."""

    redirect_url: str


def _callback_url(user_id: str) -> str:
    """Build the absolute callback URL Composio redirects to after auth."""
    base = settings.backend_url.rstrip("/")
    return f"{base}/api/v1/connectors/callback?user_id={quote(user_id)}"


@router.get("/available", response_model=list[AvailableToolkit])
async def list_available_toolkits(user: CurrentUser) -> list[AvailableToolkit]:
    """Supported toolkits for the Connectors settings page grid."""
    del user  # auth required; value unused
    return [
        AvailableToolkit(
            slug=tk.slug,
            display_name=tk.display_name,
            description=tk.description,
        )
        for tk in TOOLKIT_REGISTRY
    ]


@router.get("", response_model=list[UserConnection])
async def list_connections(
    user: CurrentUser, db: Database = Depends(get_db)
) -> list[UserConnection]:
    """Current user's connections, one row per toolkit slug.

    Merges local user_connectors DB state with live Composio status so the UI
    sees the authoritative status (Composio) with our local metadata
    (connected_at, last_used_at).
    """
    rows = await db.fetch_all(
        """
        SELECT toolkit_slug, status, status_reason, connected_at, last_used_at
        FROM user_connectors
        WHERE user_id = $1
        """,
        user.id,
    )
    local_by_slug = {r["toolkit_slug"]: r for r in rows}

    try:
        composio_conns = await list_user_connections(str(user.id))
    except ComposioClientError as e:
        logger.warning("Composio list_user_connections failed: %s", e)
        composio_conns = []
    composio_by_slug = {c.toolkit_slug: c for c in composio_conns}

    result: list[UserConnection] = []
    for tk in TOOLKIT_REGISTRY:
        local = local_by_slug.get(tk.slug)
        remote = composio_by_slug.get(tk.slug)
        if not local and not remote:
            continue
        result.append(
            UserConnection(
                toolkit_slug=tk.slug,
                display_name=tk.display_name,
                status=(remote.status if remote else local["status"] if local else None),
                status_reason=(
                    remote.status_reason
                    if remote and remote.status_reason
                    else local["status_reason"]
                    if local
                    else None
                ),
                connected_at=local["connected_at"] if local else None,
                last_used_at=local["last_used_at"] if local else None,
            )
        )
    return result


@router.post("/{toolkit_slug}/connect", response_model=InitiateResponse)
async def connect_toolkit(
    toolkit_slug: str,
    user: CurrentUser,
    db: Database = Depends(get_db),
) -> InitiateResponse:
    """Start the OAuth flow for a toolkit. Returns the URL to redirect the user to."""
    if get_toolkit(toolkit_slug) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown toolkit: {toolkit_slug}")

    try:
        initiation = await initiate_connection(
            user_id=str(user.id),
            toolkit_slug=toolkit_slug,
            callback_url=_callback_url(str(user.id)),
        )
    except ComposioClientError as e:
        logger.error("initiate_connection failed: %s", e)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Connection service unavailable") from e

    await db.execute(
        """
        INSERT INTO user_connectors (user_id, toolkit_slug, connected_account_id, status)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, toolkit_slug) DO UPDATE
            SET connected_account_id = EXCLUDED.connected_account_id,
                status = EXCLUDED.status,
                status_reason = NULL,
                updated_at = NOW()
        """,
        user.id,
        toolkit_slug,
        initiation.connected_account_id,
        initiation.status,
    )

    if not initiation.redirect_url:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Composio returned no redirect URL")
    return InitiateResponse(redirect_url=initiation.redirect_url)


@router.delete("/{toolkit_slug}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_toolkit(
    toolkit_slug: str,
    user: CurrentUser,
    db: Database = Depends(get_db),
) -> None:
    """Revoke a connection. Deletes the Composio-side token and our local row."""
    row = await db.fetch_one(
        """
        SELECT connected_account_id FROM user_connectors
        WHERE user_id = $1 AND toolkit_slug = $2
        """,
        user.id,
        toolkit_slug,
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not connected")

    if row["connected_account_id"]:
        try:
            await delete_connection(row["connected_account_id"])
        except ComposioClientError as e:
            logger.warning(
                "delete_connection failed for %s (continuing with local delete): %s",
                row["connected_account_id"],
                e,
            )

    await db.execute(
        "DELETE FROM user_connectors WHERE user_id = $1 AND toolkit_slug = $2",
        user.id,
        toolkit_slug,
    )


_CALLBACK_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Connection complete</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; background: #fafafa;
         color: #18181b; display: grid; place-items: center; min-height: 100vh;
         margin: 0; }}
  .panel {{ max-width: 420px; padding: 2rem; border: 2px solid #18181b;
           background: white; }}
  h1 {{ font-size: 1.25rem; margin: 0 0 0.5rem; }}
  p {{ margin: 0; color: #52525b; font-size: 0.9rem; }}
  .status-{status_class} {{ border-color: {border_color}; }}
</style>
</head>
<body>
  <div class="panel status-{status_class}">
    <h1>{title}</h1>
    <p>{body}</p>
  </div>
</body>
</html>"""


@router.get("/callback", response_class=HTMLResponse)
async def connector_callback(
    user_id: str = Query(...),
    status_param: str = Query(..., alias="status"),
    connected_account_id: str | None = Query(None),
    db: Database = Depends(get_db),
) -> HTMLResponse:
    """Composio redirects here after the user completes auth.

    Updates the corresponding user_connectors row and renders a minimal HTML
    page telling the user they can close the tab. Rendered by backend (not
    frontend) so it's a plain static page, no Clerk/auth roundtrip needed.
    """
    if status_param == "success":
        await db.execute(
            """
            UPDATE user_connectors
            SET status = 'ACTIVE',
                status_reason = NULL,
                connected_at = COALESCE(connected_at, NOW()),
                updated_at = NOW(),
                connected_account_id = COALESCE($3, connected_account_id)
            WHERE user_id = $1::uuid
                AND connected_account_id = $2
            """,
            user_id,
            connected_account_id,
            connected_account_id,
        )
        html = _CALLBACK_HTML.format(
            status_class="success",
            border_color="#10b981",
            title="Connection complete",
            body="You can close this tab and return to Torale.",
        )
    else:
        await db.execute(
            """
            UPDATE user_connectors
            SET status = 'FAILED',
                status_reason = $3,
                updated_at = NOW()
            WHERE user_id = $1::uuid
                AND connected_account_id = $2
            """,
            user_id,
            connected_account_id,
            f"callback_status={status_param}",
        )
        html = _CALLBACK_HTML.format(
            status_class="failed",
            border_color="#ef4444",
            title="Connection failed",
            body="Something went wrong. Close this tab and try again from Torale.",
        )
    return HTMLResponse(html)
