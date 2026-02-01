"""Task execution orchestrator.

Coordinates agent calls, DB persistence, notifications, and state transitions.
Imports from activities (data access) and service (state machine) -- no circular deps.
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from torale.core.database import db
from torale.scheduler.activities import (
    create_execution_record,
    fetch_notification_context,
    persist_execution_result,
    send_email_notification,
    send_webhook_notification,
)
from torale.scheduler.agent import call_agent
from torale.scheduler.scheduler import get_scheduler
from torale.tasks import TaskState
from torale.tasks.service import TaskService

logger = logging.getLogger(__name__)


async def _merge_execution_result(execution_id: str, data: dict) -> None:
    """Merge additional keys into an execution's result JSONB column."""
    try:
        await db.execute(
            "UPDATE task_executions SET result = COALESCE(result, '{}'::jsonb) || $1::jsonb WHERE id = $2",
            json.dumps(data),
            uuid.UUID(execution_id),
        )
    except Exception as e:
        logger.error(f"Failed to merge execution result for {execution_id}: {e}", exc_info=True)


async def _execute(
    task_id: str,
    execution_id: str | None,
    user_id: str,
    task_name: str,
    suppress_notifications: bool = False,
) -> None:
    """Core execution logic shared by scheduled and manual runs."""
    if not execution_id:
        execution_id = await create_execution_record(task_id)

    try:
        await db.execute(
            "UPDATE task_executions SET status = 'running' WHERE id = $1",
            uuid.UUID(execution_id),
        )

        task = await db.fetch_one(
            """SELECT search_query, condition_description, name, notify_behavior,
                      notification_channels, last_known_state
               FROM tasks WHERE id = $1""",
            uuid.UUID(task_id),
        )

        if not task:
            raise RuntimeError(f"Task {task_id} not found")

        # Build agent prompt
        last_state = task["last_known_state"]
        if last_state is not None and not isinstance(last_state, str):
            last_state = json.dumps(last_state)

        prompt_parts = [
            f"Monitor: {task['search_query']}",
            f"Condition: {task['condition_description']}",
        ]
        if last_state:
            prompt_parts.append(f"Previous evidence: {last_state}")

        # Call agent
        agent_response = await call_agent("\n".join(prompt_parts))

        if not isinstance(agent_response, dict):
            raise RuntimeError(f"Agent returned non-dict response: {type(agent_response)}")

        # Map agent response to execution result
        notification = agent_response.get("notification")
        condition_met = notification is not None
        evidence = agent_response.get("evidence", "")
        sources = agent_response.get("sources", [])
        if not isinstance(sources, list):
            logger.warning(f"Agent returned non-list sources: {type(sources)}")
            sources = []
        confidence = agent_response.get("confidence", "medium")
        next_run = agent_response.get("next_run")

        change_summary = notification if condition_met else evidence
        grounding_sources = [{"url": u} if isinstance(u, str) else u for u in sources]

        await persist_execution_result(
            task_id=task_id,
            execution_id=execution_id,
            agent_result={
                "evidence": evidence,
                "notification": notification,
                "confidence": confidence,
                "next_run": next_run,
                "condition_met": condition_met,
                "change_summary": change_summary,
                "grounding_sources": grounding_sources,
            },
        )

        # Send notifications if condition met
        notification_failed = False
        if condition_met and not suppress_notifications:
            try:
                notification_context = await fetch_notification_context(
                    task_id, execution_id, user_id
                )

                channels = notification_context.get("notification_channels", ["email"])

                enriched_result = {
                    "execution_id": execution_id,
                    "summary": change_summary,
                    "sources": grounding_sources,
                    "metadata": {"changed": True, "change_explanation": change_summary},
                    "is_first_execution": False,
                }

                if "email" in channels:
                    email_delivered = await send_email_notification(
                        user_id, task_name, notification_context, enriched_result
                    )
                    if not email_delivered:
                        notification_failed = True

                if "webhook" in channels:
                    await send_webhook_notification(notification_context, enriched_result)
            except Exception as e:
                notification_failed = True
                logger.error(f"Notification failed for task {task_id}: {e}", exc_info=True)

        if notification_failed:
            await _merge_execution_result(execution_id, {"notification_failed": True})

        # Auto-complete if notify_behavior is "once" and condition met
        if condition_met and task["notify_behavior"] == "once":
            if notification_failed:
                logger.error(
                    f"Skipping auto-complete for once-task {task_id} — notification delivery failed"
                )
            else:
                try:
                    task_service = TaskService(db=db)
                    await task_service.complete(
                        task_id=uuid.UUID(task_id), current_state=TaskState.ACTIVE
                    )
                    logger.info(f"Task {task_id} auto-completed (notify_behavior=once)")
                except Exception as e:
                    logger.error(f"Auto-complete failed for task {task_id}: {e}", exc_info=True)
                    await _merge_execution_result(execution_id, {"auto_complete_failed": True})

        # Dynamic reschedule if agent returns next_run
        if next_run:
            try:
                dt = datetime.fromisoformat(next_run)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                if dt <= datetime.now(UTC):
                    logger.warning(f"Agent returned past next_run {next_run}, ignoring")
                else:
                    scheduler = get_scheduler()
                    job_id = f"task-{task_id}"
                    scheduler.modify_job(job_id, next_run_time=dt)
                    logger.info(f"Rescheduled task {task_id} to {next_run}")
            except Exception as e:
                logger.error(
                    f"Failed to reschedule task {task_id} to {next_run}: {e}", exc_info=True
                )
                await _merge_execution_result(execution_id, {"reschedule_failed": True})

    except Exception as e:
        logger.error(f"Task execution failed for {task_id}: {e}", exc_info=True)
        if execution_id:
            try:
                await db.execute(
                    "UPDATE task_executions SET status = 'failed', error_message = $1, completed_at = $2 WHERE id = $3",
                    str(e),
                    datetime.now(UTC),
                    uuid.UUID(execution_id),
                )
            except Exception as db_err:
                logger.error(
                    f"Failed to mark execution {execution_id} as failed: {db_err}",
                    exc_info=True,
                )
        raise


async def execute_task_job(task_id: str, user_id: str, task_name: str) -> None:
    """Entry point for APScheduler cron jobs."""
    await _execute(task_id=task_id, execution_id=None, user_id=user_id, task_name=task_name)


async def execute_task_job_manual(
    task_id: str,
    execution_id: str,
    user_id: str,
    task_name: str,
    suppress_notifications: bool = False,
) -> None:
    """Entry point for manual task execution."""
    await _execute(
        task_id=task_id,
        execution_id=execution_id,
        user_id=user_id,
        task_name=task_name,
        suppress_notifications=suppress_notifications,
    )
