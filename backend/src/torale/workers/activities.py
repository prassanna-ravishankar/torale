import json
import logging
from datetime import UTC, datetime
from uuid import UUID

import asyncpg
from temporalio import activity
from temporalio.exceptions import ApplicationError

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


# Pipeline-based activities


@activity.defn
async def get_task_data(task_id: str) -> dict:
    """
    Fetch task configuration and execution context.

    Returns all data needed for monitoring execution:
    - Task configuration
    - Previous state
    - Last execution timestamp
    """
    from torale.core.models import TaskData

    conn = await get_db_connection()

    try:
        # Get task details
        task = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", UUID(task_id))

        if not task:
            logger.warning(f"Task {task_id} not found - likely deleted")
            # Non-retryable error for deleted tasks
            raise ApplicationError(
                f"Task {task_id} not found",
                non_retryable=True,
            )

        # Log non-active manual executions (scheduled executions already filtered by Temporal)
        if task["state"] != "active":
            logger.info(f"Manually executing task {task_id} in {task['state']} state")

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

        task_data = TaskData(
            task=dict(task),
            config=config,
            previous_state=last_known_state,
            last_execution_datetime=last_execution_datetime,
        )

        # Return as dict for Temporal serialization
        return task_data.model_dump()

    finally:
        await conn.close()


@activity.defn
async def perform_grounded_search(task_data: dict) -> dict:
    """
    Perform grounded search using configured provider.

    Uses ProviderFactory for dynamic provider selection.
    Returns SearchResult model serialized as dict.
    """
    from torale.providers import ProviderFactory

    task = task_data["task"]

    # Get provider type from config (defaults to gemini)
    provider_type = task_data["config"].get("provider", "gemini")

    # Create search provider via factory
    search_provider = ProviderFactory.create_search_provider(provider_type)

    result = await search_provider.search(
        query=task["search_query"],
        temporal_context={"last_execution_datetime": task_data.get("last_execution_datetime")},
        model=task_data["config"].get("model"),  # Uses default_gemini_model if None
    )

    # SearchProvider returns plain dict (not Pydantic model)
    # Result is already serializable for Temporal
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
    Also persists extraction_schema if it was generated for the first time.
    """
    conn = await get_db_connection()

    try:
        now_utc = datetime.now(UTC)

        # Extract metadata
        metadata = monitoring_result.get("metadata", {})
        current_state = metadata.get("current_state", {})
        changed = metadata.get("changed", False)
        schema = metadata.get("schema")

        # Update execution record
        await conn.execute(
            """
            UPDATE task_executions
            SET status = $1, result = $2, completed_at = $3
            WHERE id = $4
            """,
            TaskStatus.SUCCESS.value,
            json.dumps(monitoring_result),
            now_utc,
            UUID(execution_id),
        )

        # Check if task has extraction_schema - if not, persist it
        task_row = await conn.fetchrow(
            "SELECT extraction_schema FROM tasks WHERE id = $1", UUID(task_id)
        )

        # Determine which optional fields to update
        should_persist_schema = task_row and not task_row["extraction_schema"] and schema
        new_extraction_schema = json.dumps(schema) if should_persist_schema else None
        new_last_notified_at = now_utc if changed else None

        # Static query with COALESCE for conditional updates
        query = """
            UPDATE tasks
            SET last_known_state = $1,
                updated_at = $2,
                last_execution_id = $3,
                extraction_schema = COALESCE($4, extraction_schema),
                last_notified_at = COALESCE($5, last_notified_at)
            WHERE id = $6
        """

        await conn.execute(
            query,
            json.dumps(current_state),
            now_utc,
            UUID(execution_id),
            new_extraction_schema,
            new_last_notified_at,
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
        # Get the actual current state of the task
        task = await conn.fetchrow("SELECT state FROM tasks WHERE id = $1", UUID(task_id))
        if not task:
            logger.warning(f"Task {task_id} not found")
            raise ApplicationError(f"Task {task_id} not found", non_retryable=True)

        current_state_str = task["state"]
        current_state = TaskState(current_state_str)

        # Only attempt to complete if task is in ACTIVE state
        # PAUSED tasks should remain paused even after manual execution
        if current_state != TaskState.ACTIVE:
            logger.info(
                f"Task {task_id} is in {current_state.value} state. "
                f"Skipping completion for non-active task with notify_behavior='once'"
            )
            return

        state_machine = TaskStateMachine(db_conn=conn)
        result = await state_machine.complete(
            task_id=UUID(task_id),
            current_state=current_state,
        )
        logger.info(f"Task {task_id} completed - schedule {result['schedule_action']}")
    except Exception as e:
        logger.error(
            f"Failed to complete task {task_id}: {str(e)}. State machine transition failed."
        )
        raise  # Re-raise to let workflow handle the failure
    finally:
        await conn.close()


# Notification activities (split from god activity)


@activity.defn
async def fetch_notification_context(task_id: str, execution_id: str, user_id: str) -> dict:
    """
    Fetch notification context: task, user, execution details.

    Returns all data needed for notification delivery.
    """
    conn = await get_db_connection()

    try:
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
            logger.warning(f"Task {task_id} not found")
            raise ApplicationError(f"Task {task_id} not found", non_retryable=True)

        # Get execution details
        execution = await conn.fetchrow(
            "SELECT * FROM task_executions WHERE id = $1", UUID(execution_id)
        )

        if not execution:
            logger.warning(f"Execution {execution_id} not found")
            raise ApplicationError(f"Execution {execution_id} not found", non_retryable=True)

        return {
            "task": dict(task),
            "execution": dict(execution),
            "clerk_email": task["clerk_email"],
            "verified_emails": task["verified_notification_emails"] or [],
            "notification_channels": task.get("notification_channels") or ["email"],
            "webhook_url": task.get("webhook_url") or task.get("user_webhook_url"),
            "webhook_secret": task.get("webhook_secret") or task.get("user_webhook_secret"),
        }

    finally:
        await conn.close()


@activity.defn
async def send_email_notification(
    user_id: str, task_name: str, notification_context: dict, result: dict
) -> None:
    """
    Send email notification (welcome or condition met).

    Handles email verification, spam limits, and delivery tracking.
    Raises ApplicationError for non-retryable failures (spam limits).
    Other exceptions propagate for Temporal retry handling.
    """
    conn = await get_db_connection()

    try:
        task = notification_context["task"]
        task_id = task["id"]
        execution_id = result.get("execution_id")
        clerk_email = notification_context["clerk_email"]
        verified_emails = notification_context["verified_emails"]
        is_first_execution = result.get("is_first_execution", False)

        # FIRST EXECUTION: Send welcome email
        if is_first_execution:
            logger.info(f"Sending welcome email for task {task_id}")

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
                task_id=str(task_id),
            )
            logger.info(f"Welcome email sent to {clerk_email}")
            return

        # CONDITION MET EMAIL (non-first execution)
        # Determine recipient email (Clerk email is always verified)
        recipient_email = clerk_email

        # If task has custom notification email, verify it's validated
        custom_email = task.get("notification_email")
        if custom_email and custom_email != clerk_email:
            if custom_email not in verified_emails:
                logger.warning(
                    f"Email {custom_email} not verified for user {user_id}. "
                    f"Using Clerk email instead: {clerk_email}"
                )
                recipient_email = clerk_email
            else:
                recipient_email = custom_email

        # Check spam limits (non-retryable error)
        allowed, error = await EmailVerificationService.check_spam_limits(
            conn, user_id, recipient_email
        )

        if not allowed:
            logger.warning(f"Spam limit hit for {recipient_email}: {error}")
            # Don't retry spam limit violations
            raise ApplicationError(
                f"Spam limit exceeded: {error}",
                non_retryable=True,
            )

        # Send email via Novu
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
            task_id=str(task_id),
            execution_id=execution_id,
        )

        # Determine status and error message
        email_status = "success"
        email_error = None

        if novu_result["success"]:
            logger.info(f"Email sent to {recipient_email}: {novu_result.get('transaction_id')}")
        elif novu_result.get("skipped"):
            logger.info("Email notification skipped (Novu not configured)")
            email_status = "skipped"
        else:
            logger.error(f"Failed to send email: {novu_result.get('error')}")
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

    finally:
        await conn.close()


@activity.defn
async def send_webhook_notification(notification_context: dict, result: dict) -> None:
    """
    Send webhook notification.

    Handles webhook delivery, retry scheduling, and delivery tracking.
    Raises ApplicationError for non-retryable failures (missing config).
    Other exceptions propagate for Temporal retry handling.
    """
    conn = await get_db_connection()

    try:
        task = notification_context["task"]
        execution = notification_context["execution"]
        task_id = task["id"]
        execution_id = result.get("execution_id")

        webhook_url = notification_context.get("webhook_url")
        webhook_secret = notification_context.get("webhook_secret")

        if not webhook_url or not webhook_secret:
            logger.warning("Webhook enabled but no URL/secret configured")
            # Don't retry missing configuration
            raise ApplicationError(
                "Webhook URL or secret not configured",
                non_retryable=True,
            )

        # Build payload
        payload = build_webhook_payload(execution_id, task, execution, result)

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
            logger.info(f"Webhook delivered to {webhook_url}")
        else:
            # Record failed delivery attempt
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
            logger.error(f"Webhook delivery failed: {error}")
            # Let Temporal retry the activity
            raise Exception(f"Webhook delivery failed: {error}")

    finally:
        await conn.close()
