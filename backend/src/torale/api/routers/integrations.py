"""OAuth integrations API endpoints."""

import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from torale.access import CurrentUser
from torale.core.database import Database, get_db
from torale.integrations.slack import SlackOAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["integrations"])

SLACK_PROVIDER = "slack"


class ChannelSelectRequest(BaseModel):
    """Request to select a Slack channel."""

    channel_id: str
    channel_name: str


async def _get_slack_integration(db: Database, user_id: UUID) -> dict:
    """Fetch Slack integration for a user or raise 404."""
    integration = await db.fetch_one(
        "SELECT * FROM oauth_integrations WHERE user_id = $1 AND provider = $2",
        user_id,
        SLACK_PROVIDER,
    )
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slack integration not found. Please connect Slack first.",
        )
    return integration


@router.get("/slack/authorize")
async def slack_authorize(user: CurrentUser, db: Database = Depends(get_db)):
    """Initiate Slack OAuth flow with CSRF protection."""
    import jwt

    from torale.core.config import settings

    # Generate JWT state token with user_id and expiration (5 minutes)
    state_payload = {
        "user_id": str(user.id),
        "exp": int(time.time()) + 300,  # 5 minutes
    }
    state = jwt.encode(state_payload, settings.oauth_encryption_key, algorithm="HS256")

    service = SlackOAuthService(db)
    return {"authorization_url": service.get_authorize_url(state), "state": state}


@router.get("/slack/callback")
async def slack_callback(
    user: CurrentUser,
    code: str = Query(...),
    state: str = Query(...),
    db: Database = Depends(get_db),
):
    """Handle Slack OAuth callback with CSRF validation."""
    import jwt

    from torale.core.config import settings

    # Validate CSRF state token
    try:
        state_payload = jwt.decode(state, settings.oauth_encryption_key, algorithms=["HS256"])
        if state_payload["user_id"] != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="State token user mismatch (CSRF protection)",
            )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth state expired (>5min)"
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid OAuth state: {e}"
        ) from e

    service = SlackOAuthService(db)

    try:
        oauth_data = await service.exchange_code_for_token(code)
    except Exception as e:
        logger.error(f"Slack OAuth token exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Slack OAuth failed: {e}"
        ) from e

    encrypted_token = service.encrypt_token(oauth_data["access_token"])

    await db.execute(
        """
        INSERT INTO oauth_integrations
        (user_id, provider, access_token, workspace_id, workspace_name)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (user_id, provider)
        DO UPDATE SET
            access_token = EXCLUDED.access_token,
            workspace_id = EXCLUDED.workspace_id,
            workspace_name = EXCLUDED.workspace_name,
            updated_at = NOW()
        """,
        user.id,
        SLACK_PROVIDER,
        encrypted_token,
        oauth_data["workspace_id"],
        oauth_data["workspace_name"],
    )

    return {"success": True, "workspace_name": oauth_data["workspace_name"]}


@router.get("/slack/channels")
async def list_slack_channels(user: CurrentUser, db: Database = Depends(get_db)):
    """List user's Slack channels for selection."""
    integration = await _get_slack_integration(db, user.id)
    service = SlackOAuthService(db)
    channels = await service.list_channels(integration["access_token"])
    return {"channels": channels}


@router.post("/slack/select-channel")
async def select_slack_channel(
    request: ChannelSelectRequest, user: CurrentUser, db: Database = Depends(get_db)
):
    """Select Slack channel for notifications."""
    await _get_slack_integration(db, user.id)
    await db.execute(
        """
        UPDATE oauth_integrations
        SET channel_id = $1, channel_name = $2, updated_at = NOW()
        WHERE user_id = $3 AND provider = $4
        """,
        request.channel_id,
        request.channel_name,
        user.id,
        SLACK_PROVIDER,
    )
    return {"success": True}


@router.delete("/slack")
async def revoke_slack_integration(user: CurrentUser, db: Database = Depends(get_db)):
    """Revoke Slack integration (deletes stored tokens)."""
    await db.execute(
        "DELETE FROM oauth_integrations WHERE user_id = $1 AND provider = $2",
        user.id,
        SLACK_PROVIDER,
    )
    return {"success": True}


@router.get("/slack")
async def get_slack_integration(user: CurrentUser, db: Database = Depends(get_db)):
    """Get current Slack integration status."""
    integration = await db.fetch_one(
        """
        SELECT workspace_name, channel_name, created_at, last_used_at
        FROM oauth_integrations
        WHERE user_id = $1 AND provider = $2
        """,
        user.id,
        SLACK_PROVIDER,
    )

    if not integration:
        return {"connected": False}

    return {
        "connected": True,
        "workspace_name": integration["workspace_name"],
        "channel_name": integration["channel_name"],
        "connected_at": integration["created_at"],
        "last_used_at": integration["last_used_at"],
    }
