"""Thin async wrapper around the Composio SDK.

The SDK is sync; FastAPI is async. All calls go through `asyncio.to_thread` to
avoid blocking the event loop. Return types are Pydantic models (not SDK
objects) so consumers don't couple to SDK internals.

Intended consumers: API routers, scheduler, agent dispatcher.
"""

import asyncio
import logging
from enum import StrEnum

from composio import Composio
from pydantic import BaseModel, Field

from torale.connectors.registry import Toolkit, get_toolkit
from torale.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionStatus(StrEnum):
    """Status of a Composio-managed connection.

    Single source of truth — the migration's CHECK constraint, the in-memory
    LocalConnection model, the callback validator, and the reconcile filter
    all consume this enum. The startup assertion below catches drift between
    this enum and the CHECK constraint.
    """

    INITIALIZING = "INITIALIZING"
    INITIATED = "INITIATED"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    INACTIVE = "INACTIVE"


# Mirror of the CHECK constraint in
# backend/alembic/versions/b2d4e7f89a10_add_user_connectors.py. If you add a
# value to ConnectionStatus, write a new migration that ALTERs the CHECK and
# update this tuple — the assertion below will fire otherwise.
_CHECK_CONSTRAINT_VALUES = (
    "ACTIVE",
    "INITIATED",
    "INITIALIZING",
    "EXPIRED",
    "FAILED",
    "INACTIVE",
)
assert frozenset(s.value for s in ConnectionStatus) == frozenset(_CHECK_CONSTRAINT_VALUES), (
    "ConnectionStatus drifted from the user_connectors CHECK constraint. "
    "Add an alembic migration to update the CHECK and adjust _CHECK_CONSTRAINT_VALUES."
)


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


def _field(item, name):
    """Read a field from a Composio item that may arrive as either an object or a dict."""
    if isinstance(item, dict):
        return item.get(name)
    return getattr(item, name, None)


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
        req_id = _field(req, "id")
        req_status = _field(req, "status")
        if not req_id or not req_status:
            raise ComposioClientError(
                f"initiate response missing id or status for {toolkit_slug}/{user_id}"
            )
        return ConnectionInitiation(
            connected_account_id=req_id,
            status=req_status,
            redirect_url=_field(req, "redirect_url"),
        )

    return await asyncio.to_thread(_call)


async def get_connection(connected_account_id: str) -> Connection:
    """Fetch current status of a single connection."""

    def _call() -> Connection:
        c = _sdk()
        conn = c.connected_accounts.get(connected_account_id)
        toolkit_slug = _normalize_toolkit_slug(_field(conn, "toolkit"))
        if not toolkit_slug:
            raise ComposioClientError(f"Connection {connected_account_id} has no toolkit slug")
        status = _field(conn, "status")
        if not status:
            raise ComposioClientError(f"Connection {connected_account_id} has no status")
        return Connection(
            connected_account_id=connected_account_id,
            toolkit_slug=toolkit_slug,
            status=status,
            status_reason=_field(conn, "status_reason"),
        )

    return await asyncio.to_thread(_call)


async def list_user_connections(user_id: str) -> list[Connection]:
    """List all connections for a given user, across all toolkits.

    Iterates through every page of the Composio response so callers see the
    full set even when a user has more connections than fit in one page (the
    admin reset path is the main case where this matters).
    """

    # Defensive cap so a misbehaving cursor can't pin a worker forever. At the
    # default page size this covers thousands of connections per user, which
    # is far more than we expect.
    max_pages = 50

    def _call() -> list[Connection]:
        c = _sdk()
        connections: list[Connection] = []
        cursor: str | None = None
        for _ in range(max_pages):
            kwargs: dict = {"user_ids": [user_id]}
            if cursor:
                kwargs["cursor"] = cursor
            resp = c.connected_accounts.list(**kwargs)
            items = _field(resp, "items")
            if items is None:
                # Hard-fail rather than silently returning [] — callers already
                # wrap this in try/except ComposioClientError, and surfacing the
                # contract drift loudly is better than UI showing "no connections".
                raise ComposioClientError(
                    f"Composio list response missing 'items' attribute (resp_type={type(resp).__name__}); SDK shape may have changed"
                )
            for item in items:
                item_id = _field(item, "id")
                item_status = _field(item, "status")
                toolkit_slug = _normalize_toolkit_slug(_field(item, "toolkit"))
                if not item_id or not item_status:
                    logger.warning("Skipping malformed Composio item: %r", item)
                    continue
                if not toolkit_slug:
                    logger.warning("Skipping connection %s with missing toolkit", item_id)
                    continue
                connections.append(
                    Connection(
                        connected_account_id=item_id,
                        toolkit_slug=toolkit_slug,
                        status=item_status,
                        status_reason=_field(item, "status_reason"),
                    )
                )
            cursor = _field(resp, "next_cursor")
            if not cursor:
                return connections
        raise ComposioClientError(
            f"list_user_connections exceeded {max_pages} pages for user {user_id}; aborting"
        )

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
        url = _field(instance, "url")
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
