import json
import logging
from datetime import datetime
from uuid import UUID

import asyncpg
from temporalio import activity

from torale.core.config import settings
from torale.core.email_verification import EmailVerificationService
from torale.core.models import TaskState, TaskStatus
from torale.core.task_state_machine import TaskStateMachine
from torale.core.webhook import WebhookDeliveryService, build_webhook_payload
from torale.notifications.novu_service import novu_service

logger = logging.getLogger(__name__)


async def get_db_connection():
    """Get a database connection for workers"""
    return await asyncpg.connect(settings.database_url)


@activity.defn
async def send_notification(user_id: str, task_name: str, result: dict) -> None:
    """
    Send notifications based on task configuration.

    Entry point for all notification logic:
    - First execution: sends welcome email with execution results
    - Subsequent executions: sends condition met email (if condition met)

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

        # FIRST EXECUTION: Send welcome email and/or webhook
        if result.get("is_first_execution"):
            activity.logger.info(f"First execution for task {task_id}")

            if "email" in notification_channels:
                # Use new MonitoringResult format
                answer = result.get("summary", "")
                sources = result.get("sources", [])
                condition_met = result.get("metadata", {}).get("changed", False)

                await novu_service.send_welcome_email(
                    subscriber_id=clerk_email,
                    task_name=task["name"],
                    search_query=task["search_query"],
                    condition_description=task["condition_description"],
                    notify_behavior=task["notify_behavior"],
                    schedule=task["schedule"],
                    first_execution_result={
                        "answer": answer,
                        "condition_met": condition_met,
                        "grounding_sources": sources,
                    },
                    task_id=task_id,
                )
                activity.logger.info(f"Welcome email sent to {clerk_email}")

            # Continue to webhook processing for first execution
            # (Skip regular email notification logic below)

        # EMAIL NOTIFICATION (non-first execution)
        if "email" in notification_channels and not result.get("is_first_execution"):
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

            # Send email via Novu - use new MonitoringResult format
            answer = result.get("summary", "")
            sources = result.get("sources", [])
            change_summary = result.get("metadata", {}).get("change_explanation", "")

            novu_result = await novu_service.send_condition_met_notification(
                subscriber_id=recipient_email,
                task_name=task_name,
                search_query=task.get("search_query", ""),
                answer=answer,
                change_summary=change_summary,
                grounding_sources=sources,
                task_id=task_id,
                execution_id=execution_id,
            )

            # Determine status and error message
            email_status = "success"
            email_error = None

            if novu_result["success"]:
                activity.logger.info(
                    f"Email sent to {recipient_email}: {novu_result.get('transaction_id')}"
                )
            elif novu_result.get("skipped"):
                activity.logger.info("Email notification skipped (Novu not configured)")
                email_status = "skipped"
            else:
                activity.logger.error(f"Failed to send email: {novu_result.get('error')}")
                email_status = "failed"
                email_error = str(novu_result.get("error"))

            # Track notification send with status
            await conn.execute(
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


# New pipeline-based activities


@activity.defn
async def get_task_data(task_id: str) -> dict:
    """
    Fetch task configuration and execution context.

    Returns all data needed for monitoring execution:
    - Task configuration
    - Previous state
    - Last execution timestamp
    """
    conn = await get_db_connection()

    try:
        # Get task details
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", UUID(task_id))

        if not task:
            logger.warning(f"Task {task_id} not found")
            raise ValueError(f"Task {task_id} not found")

        # Check if task is active
        if task["state"] != "active":
            logger.info(f"Task {task_id} is not active (state={task['state']})")
            raise ValueError(f"Task {task_id} is not active")

        # Parse JSON fields
        config = task["config"]
        if isinstance(config, str):
            config = json.loads(config)

        last_known_state = task.get("last_known_state")
        if isinstance(last_known_state, str):
            last_known_state = json.loads(last_known_state) if last_known_state else None

        # Get last execution datetime
        last_execution_row = await conn.fetchrow(
            """
            SELECT completed_at
            FROM task_executions
            WHERE task_id = $1 AND status = $2
            ORDER BY completed_at DESC
            LIMIT 1
            """,
            UUID(task_id),
            TaskStatus.SUCCESS.value,
        )

        last_execution_datetime = None
        if last_execution_row and last_execution_row["completed_at"]:
            last_execution_datetime = last_execution_row["completed_at"]

        return {
            "task": dict(task),
            "config": config,
            "previous_state": last_known_state,
            "last_execution_datetime": last_execution_datetime,
        }

    finally:
        await conn.close()


@activity.defn
async def perform_grounded_search(task_data: dict) -> dict:
    """
    Perform grounded search using Gemini.

    Thin wrapper around GeminiSearchProvider.
    """
    from torale.providers.gemini import GeminiSearchProvider

    task = task_data["task"]
    search_provider = GeminiSearchProvider()

    result = await search_provider.search(
        query=task["search_query"],
        temporal_context={"last_execution_datetime": task_data.get("last_execution_datetime")},
        model=task_data["config"].get("model", "gemini-2.5-flash"),
    )

    return result


@activity.defn
async def execute_monitoring_pipeline(task_data: dict, search_result: dict) -> dict:
    """
    Execute monitoring pipeline: schema generation, extraction, comparison.

    Uses ProviderFactory for dynamic provider selection based on configuration.
    """
    from torale.pipelines import MonitoringPipeline
    from torale.providers import ProviderFactory

    # Get provider type from config (defaults to gemini)
    provider_type = task_data["config"].get("provider", "gemini")

    # Initialize pipeline with providers from factory
    pipeline = MonitoringPipeline(
        schema_provider=ProviderFactory.create_schema_provider(provider_type),
        extraction_provider=ProviderFactory.create_extraction_provider(provider_type),
        comparison_provider=ProviderFactory.create_comparison_provider(provider_type),
    )

    # Execute pipeline
    result = await pipeline.execute(
        task=task_data["task"],
        search_result=search_result,
        previous_state=task_data.get("previous_state"),
    )

    # Convert to dict for Temporal serialization
    return result.model_dump()


@activity.defn
async def persist_execution_result(
    task_id: str, execution_id: str, monitoring_result: dict
) -> None:
    """
    Persist execution result to database.

    Updates both task_executions and tasks tables.
    """
    conn = await get_db_connection()

    try:
        # Extract metadata
        metadata = monitoring_result.get("metadata", {})
        current_state = metadata.get("current_state", {})
        changed = metadata.get("changed", False)

        # Update execution record
        await conn.execute(
            """
            UPDATE task_executions
            SET status = $1, result = $2, completed_at = $3
            WHERE id = $4
            """,
            TaskStatus.SUCCESS.value,
            json.dumps(monitoring_result),
            datetime.utcnow(),
            UUID(execution_id),
        )

        # Update task's last_known_state and last_notified_at if changed
        if changed:
            await conn.execute(
                """
                UPDATE tasks
                SET last_known_state = $1, updated_at = $2, last_execution_id = $3, last_notified_at = $4
                WHERE id = $5
                """,
                json.dumps(current_state),
                datetime.utcnow(),
                UUID(execution_id),
                datetime.utcnow(),
                UUID(task_id),
            )
        else:
            await conn.execute(
                """
                UPDATE tasks
                SET last_known_state = $1, updated_at = $2, last_execution_id = $3
                WHERE id = $4
                """,
                json.dumps(current_state),
                datetime.utcnow(),
                UUID(execution_id),
                UUID(task_id),
            )

    finally:
        await conn.close()


@activity.defn
async def complete_task(task_id: str) -> None:
    """
    Mark task as completed via TaskStateMachine.

    This activity handles the state transition when a task with notify_behavior="once"
    has successfully detected a condition change and sent notification.
    """
    conn = await get_db_connection()

    try:
        state_machine = TaskStateMachine(db_conn=conn)
        result = await state_machine.complete(
            task_id=UUID(task_id),
            current_state=TaskState.ACTIVE,
        )
        logger.info(f"Task {task_id} completed - schedule {result['schedule_action']}")
    except Exception as e:
        logger.error(
            f"Failed to complete task {task_id}: {str(e)}. State machine transition failed."
        )
        raise  # Re-raise to let workflow handle the failure
    finally:
        await conn.close()
