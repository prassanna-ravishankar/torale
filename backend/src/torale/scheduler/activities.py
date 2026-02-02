"""Data access and notification delivery functions.

Pure DB operations and external service calls. No business logic or scheduler awareness.
"""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from torale.core.database import db
from torale.notifications import (
    EmailVerificationService,
    WebhookDeliveryService,
    build_webhook_payload,
    novu_service,
)
from torale.tasks import TaskStatus

logger = logging.getLogger(__name__)


async def create_execution_record(task_id: str) -> str:
    """Create a new execution record for a task.

    Returns the new execution_id as a string.
    """
    task_uuid = UUID(task_id)

    row = await db.fetch_one(
        """
        INSERT INTO task_executions (task_id, status)
        VALUES ($1, $2)
        RETURNING id
        """,
        task_uuid,
        TaskStatus.PENDING.value,
    )
    if not row:
        raise RuntimeError(f"Failed to create execution record for task {task_id}")

    execution_id = str(row["id"])
    logger.info(f"Created execution record {execution_id} for task {task_id}")
    return execution_id


async def persist_execution_result(task_id: str, execution_id: str, agent_result: dict) -> None:
    """Persist agent execution result to database.

    Maps agent response fields:
    - evidence -> last_known_state (narrative string replaces structured JSON)
    - notification, change_summary, grounding_sources -> task_executions columns
    - Full agent_result -> result JSONB
    """
    now_utc = datetime.now(UTC)

    notification_text = agent_result.get("notification")
    change_summary = agent_result.get("change_summary", "")
    grounding_sources = agent_result.get("grounding_sources", [])
    evidence = agent_result.get("evidence", "")
    last_known_state = {"evidence": evidence} if evidence else None

    async with db.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE task_executions
                SET status = $1, result = $2, completed_at = $3,
                    notification = $4, change_summary = $5, grounding_sources = $6
                WHERE id = $7
                """,
                TaskStatus.SUCCESS.value,
                json.dumps(agent_result),
                now_utc,
                notification_text,
                change_summary,
                json.dumps(grounding_sources),
                UUID(execution_id),
            )

            await conn.execute(
                """
                UPDATE tasks
                SET last_known_state = $1,
                    updated_at = $2,
                    last_execution_id = $3
                WHERE id = $4
                """,
                json.dumps(last_known_state) if last_known_state else None,
                now_utc,
                UUID(execution_id),
                UUID(task_id),
            )


async def fetch_notification_context(task_id: str, execution_id: str, user_id: str) -> dict:
    """Fetch notification context: task, user, execution details."""
    task = await db.fetch_one(
        """
        SELECT t.*, u.email as clerk_email,
               u.verified_notification_emails,
               u.webhook_url as user_webhook_url,
               u.webhook_secret as user_webhook_secret
        FROM tasks t
        JOIN users u ON t.user_id = u.id
        WHERE t.id = $1
        """,
        UUID(task_id),
    )

    if not task:
        raise RuntimeError(f"Task {task_id} not found")

    execution = await db.fetch_one(
        "SELECT * FROM task_executions WHERE id = $1", UUID(execution_id)
    )

    if not execution:
        raise RuntimeError(f"Execution {execution_id} not found")

    return {
        "task": dict(task),
        "execution": dict(execution),
        "clerk_email": task["clerk_email"],
        "verified_emails": task["verified_notification_emails"] or [],
        "notification_channels": task.get("notification_channels") or ["email"],
        "webhook_url": task.get("webhook_url") or task.get("user_webhook_url"),
        "webhook_secret": task.get("webhook_secret") or task.get("user_webhook_secret"),
    }


async def send_email_notification(
    user_id: str, task_name: str, notification_context: dict, result: dict
) -> bool:
    """Send email notification (welcome or condition met).

    Returns True if delivered, False if skipped (e.g. Novu not configured).
    Raises on failure.
    """
    task = notification_context["task"]
    task_id = str(task["id"])
    execution_id = result.get("execution_id")
    if not execution_id:
        raise RuntimeError("execution_id required for email notifications")
    clerk_email = notification_context["clerk_email"]
    verified_emails = notification_context["verified_emails"]
    is_first_execution = result.get("is_first_execution", False)

    if is_first_execution:
        logger.info(f"Sending welcome email for task {task_id}")

        await novu_service.send_welcome_email(
            subscriber_id=clerk_email,
            task_name=task["name"],
            search_query=task["search_query"],
            condition_description=task["condition_description"],
            notify_behavior=task["notify_behavior"],
            first_execution_result={
                "answer": result.get("summary", ""),
                "condition_met": result.get("notification") is not None,
                "grounding_sources": result.get("sources", []),
            },
            task_id=str(task_id),
        )
        logger.info(f"Welcome email sent for task {task_id}")
        return True

    # Determine recipient email
    recipient_email = clerk_email
    custom_email = task.get("notification_email")
    if custom_email and custom_email != clerk_email:
        if custom_email in verified_emails:
            recipient_email = custom_email
        else:
            logger.warning("Custom notification email not verified, using default")

    # Check spam limits (needs a raw connection for EmailVerificationService)
    async with db.acquire() as conn:
        allowed, error = await EmailVerificationService.check_spam_limits(
            conn, user_id, recipient_email
        )

    if not allowed:
        logger.warning(f"Spam limit hit for task {task_id}: {error}")
        raise RuntimeError(f"Spam limit exceeded: {error}")

    # Send email via Novu
    answer = result.get("summary", "")
    sources = result.get("sources", [])
    change_summary = result.get("notification") or result.get("summary", "")

    novu_result = await novu_service.send_condition_met_notification(
        subscriber_id=recipient_email,
        task_name=task_name,
        search_query=task.get("search_query", ""),
        answer=answer,
        change_summary=change_summary,
        grounding_sources=sources,
        task_id=str(task_id),
        execution_id=execution_id,
    )

    email_status = "success"
    email_error = None

    if novu_result["success"]:
        logger.info(f"Email sent for task {task_id}")
    elif novu_result.get("skipped"):
        logger.info("Email notification skipped (Novu not configured)")
        email_status = "skipped"
    else:
        logger.error(f"Failed to send email for task {task_id}: {novu_result.get('error')}")
        email_status = "failed"
        email_error = str(novu_result.get("error"))

    await db.execute(
        """
        INSERT INTO notification_sends
        (user_id, task_id, execution_id, recipient_email, notification_type, status, error_message)
        VALUES ($1, $2, $3, $4, 'email', $5, $6)
        """,
        UUID(user_id),
        UUID(task_id),
        UUID(execution_id),
        recipient_email,
        email_status,
        email_error,
    )

    if email_status == "failed":
        raise RuntimeError(f"Email notification failed: {email_error}")

    return email_status == "success"


async def send_webhook_notification(notification_context: dict, result: dict) -> None:
    """Send webhook notification."""
    task = notification_context["task"]
    execution = notification_context["execution"]
    task_id = str(task["id"])
    execution_id = result.get("execution_id")
    if not execution_id:
        raise RuntimeError("execution_id required for webhook notifications")

    webhook_url = notification_context.get("webhook_url")
    webhook_secret = notification_context.get("webhook_secret")

    if not webhook_url or not webhook_secret:
        raise RuntimeError("Webhook URL or secret not configured")

    payload = build_webhook_payload(execution_id, task, execution, result)

    service = WebhookDeliveryService()
    signature: str | None = None
    try:
        success, http_status, error, signature = await service.deliver(
            webhook_url, payload, webhook_secret, attempt=1
        )
    finally:
        await service.close()

    if success:
        await db.execute(
            """
            INSERT INTO webhook_deliveries (
                task_id, execution_id, webhook_url, payload, signature,
                http_status, attempt_number, delivered_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            """,
            UUID(task_id),
            UUID(execution_id),
            webhook_url,
            payload.model_dump_json(),
            signature,
            http_status,
            1,
        )
        logger.info(f"Webhook delivered for task {task_id}")
    else:
        next_retry = WebhookDeliveryService.get_next_retry_time(1)
        await db.execute(
            """
            INSERT INTO webhook_deliveries (
                task_id, execution_id, webhook_url, payload, signature,
                http_status, error_message, attempt_number, next_retry_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            UUID(task_id),
            UUID(execution_id),
            webhook_url,
            payload.model_dump_json(),
            signature,
            http_status,
            error,
            1,
            next_retry,
        )
        logger.error(f"Webhook delivery failed: {error}")
        raise RuntimeError(f"Webhook delivery failed: {error}")
