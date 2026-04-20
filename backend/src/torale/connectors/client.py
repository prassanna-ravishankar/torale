"""Thin async wrapper around the Composio SDK.

The SDK is sync; FastAPI is async. All calls go through `asyncio.to_thread` to
avoid blocking the event loop. Return types are Pydantic models (not SDK
objects) so consumers don't couple to SDK internals.

Intended consumers: API routers, scheduler, agent dispatcher.
"""

import asyncio
import logging
from typing import Literal

from composio import Composio
from pydantic import BaseModel, Field

from torale.connectors.registry import Toolkit, get_toolkit
from torale.core.config import settings

logger = logging.getLogger(__name__)


ConnectionStatus = Literal["INITIALIZING", "INITIATED", "ACTIVE", "FAILED", "EXPIRED", "INACTIVE"]


class ConnectionInitiation(BaseModel):
    """Result of starting an OAuth flow. Hand `redirect_url` to the user."""

    connected_account_id: str = Field(description="Composio connection ID (ca_xxx)")
    status: ConnectionStatus
    redirect_url: str | None = Field(
        default=None,
        description="URL to redirect the user to for auth. None if already connected.",
    )


class Connection(BaseModel):
    """One user's connection to one toolkit."""

    connected_account_id: str
    toolkit_slug: str
    status: ConnectionStatus
    status_reason: str | None = None


class MCPInstance(BaseModel):
    """Per-user MCP endpoint the agent calls."""

    url: str
    toolkit_slug: str


class ComposioClientError(RuntimeError):
    """Raised when a Composio call fails or the SDK returns an unexpected shape."""


def _sdk() -> Composio:
    """Build a fresh Composio client. Cheap; safe to call per-request."""
    if not settings.composio_api_key:
        raise ComposioClientError("COMPOSIO_API_KEY is not configured")
    return Composio(api_key=settings.composio_api_key)


def _normalize_toolkit_slug(raw) -> str | None:
    """Composio's list response shapes toolkit as either a str or a nested object."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("slug")
    return getattr(raw, "slug", None)


async def initiate_connection(
    user_id: str,
    toolkit_slug: str,
    callback_url: str | None = None,
) -> ConnectionInitiation:
    """Start an OAuth flow for a user against a toolkit.

    Returns the redirect URL to hand to the user. The connection stays in
    INITIATED state until the user completes auth (within 10min, per Composio).
    """
    toolkit = get_toolkit(toolkit_slug)
    if toolkit is None:
        raise ComposioClientError(f"Unknown toolkit: {toolkit_slug}")

    def _call() -> ConnectionInitiation:
        c = _sdk()
        req = c.connected_accounts.initiate(
            user_id=user_id,
            auth_config_id=toolkit.auth_config_id,
            callback_url=callback_url,
        )
        return ConnectionInitiation(
            connected_account_id=req.id,
            status=req.status,
            redirect_url=req.redirect_url,
        )

    return await asyncio.to_thread(_call)


async def get_connection(connected_account_id: str) -> Connection:
    """Fetch current status of a single connection."""

    def _call() -> Connection:
        c = _sdk()
        conn = c.connected_accounts.get(connected_account_id)
        toolkit_slug = _normalize_toolkit_slug(getattr(conn, "toolkit", None))
        if not toolkit_slug:
            raise ComposioClientError(f"Connection {connected_account_id} has no toolkit slug")
        return Connection(
            connected_account_id=connected_account_id,
            toolkit_slug=toolkit_slug,
            status=conn.status,
            status_reason=getattr(conn, "status_reason", None),
        )

    return await asyncio.to_thread(_call)


async def list_user_connections(user_id: str) -> list[Connection]:
    """List all connections for a given user, across all toolkits."""

    def _call() -> list[Connection]:
        c = _sdk()
        resp = c.connected_accounts.list(user_ids=[user_id])
        items = getattr(resp, "items", None) or []
        connections: list[Connection] = []
        for item in items:
            toolkit_slug = _normalize_toolkit_slug(getattr(item, "toolkit", None))
            if not toolkit_slug:
                logger.warning(
                    "Skipping connection %s with missing toolkit",
                    getattr(item, "id", "<unknown>"),
                )
                continue
            connections.append(
                Connection(
                    connected_account_id=item.id,
                    toolkit_slug=toolkit_slug,
                    status=item.status,
                    status_reason=getattr(item, "status_reason", None),
                )
            )
        return connections

    return await asyncio.to_thread(_call)


async def delete_connection(connected_account_id: str) -> None:
    """Revoke a connection. Composio revokes tokens with the provider too."""

    def _call() -> None:
        c = _sdk()
        c.connected_accounts.delete(connected_account_id)

    await asyncio.to_thread(_call)


async def generate_mcp_url(user_id: str, toolkit_slug: str) -> MCPInstance:
    """Return the per-user MCP endpoint URL for a toolkit.

    The URL + `x-api-key: <COMPOSIO_API_KEY>` header is what the agent needs.
    Caller is responsible for confirming the user has an ACTIVE connection
    for this toolkit before calling the agent with this URL.
    """
    toolkit = get_toolkit(toolkit_slug)
    if toolkit is None:
        raise ComposioClientError(f"Unknown toolkit: {toolkit_slug}")

    def _call() -> MCPInstance:
        c = _sdk()
        instance = c.mcp.generate(
            user_id=user_id,
            mcp_config_id=toolkit.mcp_server_id,
        )
        url = instance["url"] if isinstance(instance, dict) else getattr(instance, "url", None)
        if not url:
            raise ComposioClientError(f"mcp.generate returned no URL for {toolkit_slug}/{user_id}")
        return MCPInstance(url=url, toolkit_slug=toolkit_slug)

    return await asyncio.to_thread(_call)


def verify_webhook(payload: bytes, signature: str | None) -> bool:
    """Verify an incoming Composio webhook signature.

    STUB: real implementation lands with torale-785 (webhook handler bead,
    currently deferred). This placeholder lets callers import the symbol
    without pulling in unvalidated crypto. Returning False fails closed.
    """
    del payload, signature  # appease linters; real impl will use these
    logger.warning("verify_webhook called but is not yet implemented")
    return False


__all__ = [
    "Connection",
    "ConnectionInitiation",
    "ConnectionStatus",
    "ComposioClientError",
    "MCPInstance",
    "Toolkit",
    "delete_connection",
    "generate_mcp_url",
    "get_connection",
    "initiate_connection",
    "list_user_connections",
    "verify_webhook",
]
