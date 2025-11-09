"""Webhook API endpoints."""

import json
import secrets
import time
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from torale.api.auth import CurrentUserOrTestUser
from torale.core.database import Database, get_db
from torale.core.webhook import (
    WebhookDeliveryService,
    WebhookPayload,
    WebhookSignature,
)

CurrentUser = CurrentUserOrTestUser
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response Models
class WebhookConfig(BaseModel):
    """Webhook configuration."""

    webhook_url: HttpUrl | None = None
    enabled: bool = False


class WebhookTestRequest(BaseModel):
    """Test webhook request."""

    webhook_url: HttpUrl
    webhook_secret: str


# User-level webhook endpoints
@router.get("/config", response_model=WebhookConfig)
async def get_user_webhook_config(user: CurrentUser, db: Database = Depends(get_db)):
    """Get user's default webhook configuration."""
    row = await db.fetch_one(
        "SELECT webhook_url, webhook_enabled FROM users WHERE id = $1", user.id
    )
    return {"webhook_url": row["webhook_url"], "enabled": row["webhook_enabled"]}


@router.put("/config")
async def update_user_webhook_config(
    config: WebhookConfig, user: CurrentUser, db: Database = Depends(get_db)
):
    """
    Update user's default webhook configuration.

    Generates new secret if webhook is being enabled for the first time.
    """
    # Get current config
    current = await db.fetch_one("SELECT webhook_secret FROM users WHERE id = $1", user.id)

    # Generate secret if enabling webhook for first time
    secret = current["webhook_secret"]
    if config.enabled and not secret:
        secret = WebhookSignature.generate_secret()

    # Update config
    await db.execute(
        """
        UPDATE users
        SET webhook_url = $1, webhook_enabled = $2, webhook_secret = $3
        WHERE id = $4
        """,
        str(config.webhook_url) if config.webhook_url else None,
        config.enabled,
        secret,
        user.id,
    )

    return {"success": True, "webhook_secret": secret if config.enabled else None}


@router.post("/test")
async def test_webhook(test_req: WebhookTestRequest, user: CurrentUser):
    """
    Test webhook delivery with sample payload.

    Useful for users to verify their webhook endpoint works.
    """
    # Build test payload
    payload = WebhookPayload(
        id="test_" + secrets.token_hex(8),
        event_type="task.condition_met",
        created_at=int(time.time()),
        data={
            "task": {
                "id": "test_task_id",
                "name": "Test Task",
                "search_query": "Test query",
                "condition_description": "Test condition",
            },
            "execution": {
                "id": "test_execution_id",
                "condition_met": True,
                "change_summary": "This is a test webhook",
                "completed_at": datetime.utcnow().isoformat(),
            },
            "result": {"answer": "Test answer", "grounding_sources": []},
        },
    )

    # Attempt delivery
    service = WebhookDeliveryService()
    success, http_status, error, _ = await service.deliver(
        str(test_req.webhook_url), payload, test_req.webhook_secret, attempt=1
    )
    await service.close()

    if success:
        return {
            "success": True,
            "message": f"Webhook delivered successfully (HTTP {http_status})",
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook delivery failed: {error}",
        )


# Webhook verification endpoint (for Slack, Discord, etc.)
@router.post("/verify")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint.

    Services like Slack send a verification challenge that must be echoed back.
    This endpoint handles the standard verification pattern.
    """
    try:
        body = await request.json()

        # Handle challenge-response verification
        if "challenge" in body:
            return {"challenge": body["challenge"]}

        # Handle other verification formats
        if "type" in body and body["type"] == "url_verification":
            return {"challenge": body.get("challenge", "")}

        return {"message": "Verification endpoint"}

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification request: not valid JSON",
        ) from e


# Webhook delivery history
@router.get("/deliveries")
async def list_webhook_deliveries(
    user: CurrentUser,
    task_id: str | None = None,
    limit: int = 50,
    db: Database = Depends(get_db),
):
    """
    List webhook delivery attempts for user's tasks.

    Useful for debugging webhook issues.
    """
    if task_id:
        # Verify task belongs to user
        task = await db.fetch_one(
            "SELECT id FROM tasks WHERE id = $1 AND user_id = $2",
            UUID(task_id),
            user.id,
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        query = """
            SELECT id, task_id, webhook_url, http_status, attempt_number,
                   delivered_at, failed_at, error_message, created_at
            FROM webhook_deliveries
            WHERE task_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await db.fetch_all(query, UUID(task_id), limit)
    else:
        query = """
            SELECT wd.id, wd.task_id, wd.webhook_url, wd.http_status,
                   wd.attempt_number, wd.delivered_at, wd.failed_at,
                   wd.error_message, wd.created_at
            FROM webhook_deliveries wd
            JOIN tasks t ON wd.task_id = t.id
            WHERE t.user_id = $1
            ORDER BY wd.created_at DESC
            LIMIT $2
        """
        rows = await db.fetch_all(query, user.id, limit)

    return [dict(row) for row in rows]
