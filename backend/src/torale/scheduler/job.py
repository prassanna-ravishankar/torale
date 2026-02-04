"""Task execution orchestrator.

Coordinates agent calls, DB persistence, notifications, and state transitions.
Imports from activities (data access) and service (state machine) -- no circular deps.
"""

import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse

from apscheduler.triggers.date import DateTrigger

from torale.core.database import db
from torale.scheduler import JOB_FUNC_REF
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


def _normalize_confidence(value: object) -> int:
    if isinstance(value, bool):
        return 50
    if isinstance(value, (int, float)):
        try:
            return max(0, min(100, int(value)))
        except (ValueError, TypeError):
            return 50
    if isinstance(value, str):
        try:
            return max(0, min(100, int(float(value))))
        except ValueError:
            return 50
    return 50


def _parse_next_run(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _resolve_next_run(value: str | None) -> datetime:
    """Resolve a next_run string to a future datetime. Falls back to now + 24h."""
    now = datetime.now(UTC)
    dt = _parse_next_run(value)
    if dt is None or dt <= now:
        return now + timedelta(hours=24)
    return dt


async def _schedule_next_run(
    task_id: str,
    user_id: str,
    task_name: str,
    next_run_dt: datetime,
    execution_id: str | None,
) -> None:
    """Schedule an APScheduler job and persist next_run to DB."""
    try:
        scheduler = get_scheduler()
        job_id = f"task-{task_id}"
        scheduler.add_job(
            JOB_FUNC_REF,
            trigger=DateTrigger(run_date=next_run_dt),
            id=job_id,
            args=[task_id, user_id, task_name],
            replace_existing=True,
        )
        await db.execute(
            "UPDATE tasks SET next_run = $1 WHERE id = $2",
            next_run_dt,
            uuid.UUID(task_id),
        )
        logger.info(f"Scheduled task {task_id} next run at {next_run_dt.isoformat()}")
    except Exception as e:
        logger.error(f"Failed to schedule next run for task {task_id}: {e}", exc_info=True)
        if execution_id:
            await _merge_execution_result(execution_id, {"reschedule_failed": True})


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

    next_run_value: str | None = None
    execution_succeeded = False

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
            f"task_id: {task_id}",
            f"user_id: {user_id}",
            f"Task: {task['search_query']}",
        ]

        # Only include condition if it adds new info
        cond = task["condition_description"]
        if cond and cond.strip() != task["search_query"].strip():
            prompt_parts.append(f"Context: {cond}")

        if last_state:
            prompt_parts.append(f"Previous evidence: {last_state}")

        # Call agent
        agent_response = await call_agent("\n".join(prompt_parts))

        if not isinstance(agent_response, dict):
            raise RuntimeError(f"Agent returned non-dict response: {type(agent_response)}")

        # Map agent response to execution result
        notification = agent_response.get("notification")
        evidence = agent_response.get("evidence", "")
        topic = agent_response.get("topic")

        # Auto-name task if agent provided a topic and name is still the default
        if topic and task["name"] == "New Monitor":
            try:
                await db.execute(
                    "UPDATE tasks SET name = $1 WHERE id = $2",
                    topic,
                    uuid.UUID(task_id),
                )
                task_name = topic
                logger.info(f"Named task {task_id}: '{topic}'")
            except Exception as e:
                logger.error(f"Failed to name task {task_id}: {e}")

        sources = agent_response.get("sources", [])
        if not isinstance(sources, list):
            logger.warning(f"Agent returned non-list sources: {type(sources)}")
            sources = []
        confidence = _normalize_confidence(agent_response.get("confidence"))
        next_run_value = agent_response.get("next_run")
        next_run_dt = _parse_next_run(next_run_value)
        next_run = next_run_dt.isoformat() if next_run_dt else None

        def _source_entry(u):
            if isinstance(u, str):
                return {"url": u, "title": urlparse(u).netloc or u}
            return u

        grounding_sources = [_source_entry(u) for u in sources]

        await persist_execution_result(
            task_id=task_id,
            execution_id=execution_id,
            agent_result={
                "evidence": evidence,
                "notification": notification,
                "confidence": confidence,
                "next_run": next_run,
                "grounding_sources": grounding_sources,
            },
        )

        # Send notifications if notification text present
        notification_failed = False
        if notification and not suppress_notifications:
            try:
                notification_context = await fetch_notification_context(
                    task_id, execution_id, user_id
                )

                channels = notification_context.get("notification_channels", ["email"])

                enriched_result = {
                    "execution_id": execution_id,
                    "summary": notification or evidence,
                    "sources": grounding_sources,
                    "notification": notification,
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

        execution_succeeded = True

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
    finally:
        if execution_succeeded and next_run_value is None:
            # Agent returned next_run=null → monitoring complete
            try:
                task_service = TaskService(db=db)
                await task_service.complete(
                    task_id=uuid.UUID(task_id), current_state=TaskState.ACTIVE
                )
                await db.execute(
                    "UPDATE tasks SET next_run = NULL WHERE id = $1",
                    uuid.UUID(task_id),
                )
                logger.info(f"Task {task_id} completed (agent returned next_run=null)")
            except Exception as e:
                logger.error(f"Auto-complete failed for task {task_id}: {e}", exc_info=True)
                await _merge_execution_result(execution_id, {"auto_complete_failed": True})
        elif execution_succeeded:
            # Agent returned a next_run date → schedule next check
            resolved_dt = _resolve_next_run(next_run_value)
            await _schedule_next_run(
                task_id=task_id,
                user_id=user_id,
                task_name=task_name,
                next_run_dt=resolved_dt,
                execution_id=execution_id,
            )
        else:
            # Execution failed → retry in 1 hour, don't complete
            retry_dt = datetime.now(UTC) + timedelta(hours=1)
            await _schedule_next_run(
                task_id=task_id,
                user_id=user_id,
                task_name=task_name,
                next_run_dt=retry_dt,
                execution_id=execution_id,
            )


async def execute_task_job(task_id: str, user_id: str, task_name: str) -> None:
    """Entry point for APScheduler scheduled jobs."""
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
