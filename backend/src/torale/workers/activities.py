import json
import logging
from datetime import datetime
from uuid import UUID

import asyncpg
from temporalio import activity

from torale.core.config import settings
from torale.core.email_verification import EmailVerificationService
from torale.core.models import NotifyBehavior, TaskStatus
from torale.core.webhook import WebhookDeliveryService, build_webhook_payload
from torale.executors import GroundedSearchExecutor
from torale.notifications.novu_service import novu_service

logger = logging.getLogger(__name__)


async def get_db_connection():
    """Get a database connection for workers"""
    return await asyncpg.connect(settings.database_url)


@activity.defn
async def execute_task(task_id: str, execution_id: str) -> dict:
    conn = await get_db_connection()

    try:
        # Get task details
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", UUID(task_id))

        if not task:
            # Task was deleted but schedule still exists (orphaned schedule)
            # Log warning and return gracefully to avoid retries
            logger.warning(
                f"Task {task_id} not found in database (likely deleted). "
                f"Skipping execution. Schedule should be cleaned up."
            )
            return {
                "status": "skipped",
                "reason": "task_deleted",
                "message": f"Task {task_id} was deleted but schedule still exists",
            }

        # Parse config if it's a JSON string
        config = task["config"]
        if isinstance(config, str):
            config = json.loads(config)

        # Parse last_known_state if it's a JSON string
        last_known_state = task.get("last_known_state")
        if isinstance(last_known_state, str):
            last_known_state = json.loads(last_known_state) if last_known_state else None

        # Create execution record if not provided (scheduled execution)
        if not execution_id:
            row = await conn.fetchrow(
                """
                INSERT INTO task_executions (task_id, status)
                VALUES ($1, $2)
                RETURNING id
                """,
                UUID(task_id),
                TaskStatus.PENDING.value,
            )
            execution_id = str(row["id"])

        # Update execution status to running
        await conn.execute(
            """
            UPDATE task_executions
            SET status = $1
            WHERE id = $2
            """,
            TaskStatus.RUNNING.value,
            UUID(execution_id),
        )

        # Execute based on executor type
        executor_result = None
        try:
            if task["executor_type"] == "llm_grounded_search":
                # Prepare config for grounded search executor
                executor_config = {
                    **config,
                    "search_query": task["search_query"],
                    "condition_description": task["condition_description"],
                    "last_known_state": last_known_state,
                }

                executor = GroundedSearchExecutor()
                executor_result = await executor.execute(executor_config)

                # Extract grounded search fields
                condition_met = executor_result.get("condition_met", False)
                change_summary = executor_result.get("change_summary")
                grounding_sources = executor_result.get("grounding_sources", [])
                current_state = executor_result.get("current_state", {})

                # Update execution with grounded search fields
                await conn.execute(
                    """
                    UPDATE task_executions
                    SET status = $1, result = $2, completed_at = $3,
                        condition_met = $4, change_summary = $5, grounding_sources = $6
                    WHERE id = $7
                    """,
                    TaskStatus.SUCCESS.value,
                    json.dumps(executor_result),
                    datetime.utcnow(),
                    condition_met,
                    change_summary,
                    json.dumps(grounding_sources),
                    UUID(execution_id),
                )

                # Update task state tracking
                await conn.execute(
                    """
                    UPDATE tasks
                    SET last_known_state = $1, condition_met = $2, updated_at = $3
                    WHERE id = $4
                    """,
                    json.dumps(current_state),
                    condition_met,
                    datetime.utcnow(),
                    UUID(task_id),
                )

                # Handle notify behavior if condition is met
                if condition_met:
                    notify_behavior = task.get("notify_behavior", "once")

                    # Update last_notified_at
                    await conn.execute(
                        """
                        UPDATE tasks
                        SET last_notified_at = $1
                        WHERE id = $2
                        """,
                        datetime.utcnow(),
                        UUID(task_id),
                    )

                    # Auto-disable task if notify_behavior is "once"
                    if notify_behavior == NotifyBehavior.ONCE.value:
                        await conn.execute(
                            """
                            UPDATE tasks
                            SET is_active = false
                            WHERE id = $1
                            """,
                            UUID(task_id),
                        )

            else:
                raise ValueError(f"Unsupported executor type: {task['executor_type']}")

            # Add metadata for notifications
            executor_result["task_id"] = str(task_id)
            executor_result["execution_id"] = str(execution_id)
            executor_result["search_query"] = task["search_query"]

            return executor_result

        except Exception as e:
            # Update execution with failure
            await conn.execute(
                """
                UPDATE task_executions
                SET status = $1, error_message = $2, completed_at = $3
                WHERE id = $4
                """,
                TaskStatus.FAILED.value,
                str(e),
                datetime.utcnow(),
                UUID(execution_id),
            )

            raise

    finally:
        await conn.close()


@activity.defn
async def send_notification(user_id: str, task_name: str, result: dict) -> None:
    """
    Send notifications based on task configuration.

    Supports multiple channels: email (via Novu), webhook, or both.
    Never fails the workflow - all errors are caught and logged.
    """
    conn = await get_db_connection()

    try:
        # Extract task and execution IDs from result
        task_id = result.get("task_id")
        execution_id = result.get("execution_id")

        if not task_id or not execution_id:
            activity.logger.error("Missing task_id or execution_id in result")
            return

        # Get task details including notification channels
        task = await conn.fetchrow(
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
            activity.logger.warning(f"Task {task_id} not found")
            return

        # Get execution details
        execution = await conn.fetchrow(
            "SELECT * FROM task_executions WHERE id = $1", UUID(execution_id)
        )

        if not execution:
            activity.logger.warning(f"Execution {execution_id} not found")
            return

        clerk_email = task["clerk_email"]
        verified_emails = task["verified_notification_emails"] or []
        notification_channels = task.get("notification_channels") or ["email"]

        # EMAIL NOTIFICATION
        if "email" in notification_channels:
            # Determine recipient email (Clerk email is always verified)
            recipient_email = clerk_email  # Default to Clerk email

            # If task has custom notification email, verify it's validated
            custom_email = task.get("notification_email")
            if custom_email and custom_email != clerk_email:
                # Check if verified
                if custom_email not in verified_emails:
                    activity.logger.error(
                        f"Email {custom_email} not verified for user {user_id}. "
                        f"Using Clerk email instead: {clerk_email}"
                    )
                    recipient_email = clerk_email
                else:
                    recipient_email = custom_email

            # Check spam limits
            allowed, error = await EmailVerificationService.check_spam_limits(
                conn, user_id, recipient_email
            )

            if not allowed:
                activity.logger.error(f"Spam limit hit: {error}")
                return

            # Send email via Novu
            novu_result = await novu_service.send_condition_met_notification(
                subscriber_id=recipient_email,
                task_name=task_name,
                search_query=task.get("search_query", ""),
                answer=result.get("answer", ""),
                change_summary=result.get("change_summary"),
                grounding_sources=result.get("grounding_sources", []),
                task_id=task_id,
                execution_id=execution_id,
            )

            if novu_result["success"]:
                activity.logger.info(
                    f"Email sent to {recipient_email}: {novu_result.get('transaction_id')}"
                )
            elif novu_result.get("skipped"):
                activity.logger.info("Email notification skipped (Novu not configured)")
            else:
                activity.logger.error(f"Failed to send email: {novu_result.get('error')}")

            # Track notification send
            await conn.execute(
                """
                INSERT INTO notification_sends
                (user_id, task_id, recipient_email, notification_type)
                VALUES ($1, $2, $3, 'email')
                """,
                UUID(user_id),
                UUID(task_id),
                recipient_email,
            )

        # WEBHOOK NOTIFICATION
        if "webhook" in notification_channels:
            # Determine webhook URL and secret (task-level overrides user-level)
            webhook_url = task.get("webhook_url") or task.get("user_webhook_url")
            webhook_secret = task.get("webhook_secret") or task.get("user_webhook_secret")

            if webhook_url and webhook_secret:
                # Build payload
                payload = build_webhook_payload(execution_id, dict(task), dict(execution), result)

                # Attempt delivery with proper resource cleanup
                service = WebhookDeliveryService()
                signature: str | None = None
                try:
                    success, http_status, error, signature = await service.deliver(
                        webhook_url, payload, webhook_secret, attempt=1
                    )
                finally:
                    await service.close()

                # Record delivery attempt
                if success:
                    await conn.execute(
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
                    activity.logger.info(f"Webhook delivered to {webhook_url}")
                else:
                    # Schedule retry
                    next_retry = WebhookDeliveryService.get_next_retry_time(1)
                    await conn.execute(
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
                    activity.logger.error(f"Webhook delivery failed: {error}")
            else:
                activity.logger.warning("Webhook enabled but no URL/secret configured")

    except Exception:
        # Never fail the workflow due to notification errors
        activity.logger.error("Notification activity error", exc_info=True)

    finally:
        await conn.close()
