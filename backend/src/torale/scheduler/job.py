"""Task execution orchestrator.

Coordinates agent calls, DB persistence, notifications, and state transitions.
Imports from activities (data access) and service (state machine) -- no circular deps.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, datetime

import httpx

from torale.core.config import settings
from torale.core.database import db
from torale.scheduler.scheduler import get_scheduler
from torale.tasks import TaskState
from torale.tasks.service import TaskService
from torale.workers.activities import (
    create_execution_record,
    fetch_notification_context,
    persist_execution_result,
    send_email_notification,
    send_webhook_notification,
)

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
POLL_BACKOFF = [0.5, 1, 2, 4, 8, 16, 32]  # exponential backoff steps


async def _call_agent(prompt: str) -> dict:
    """Send task to torale-agent via A2A JSON-RPC and poll for result."""
    message_id = f"msg-{uuid.uuid4().hex[:12]}"

    async with httpx.AsyncClient(timeout=AGENT_TIMEOUT) as client:
        send_payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                }
            },
        }

        resp = await client.post(settings.agent_url, json=send_payload)
        resp.raise_for_status()
        send_result = resp.json()

        task_id = send_result.get("result", {}).get("id")
        if not task_id:
            raise RuntimeError(f"Agent did not return task_id: {send_result}")

        deadline = time.monotonic() + AGENT_TIMEOUT
        backoff_idx = 0
        while time.monotonic() < deadline:
            delay = POLL_BACKOFF[min(backoff_idx, len(POLL_BACKOFF) - 1)]
            await asyncio.sleep(delay)
            backoff_idx += 1

            poll_payload = {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tasks/get",
                "params": {"id": task_id},
            }

            poll_resp = await client.post(settings.agent_url, json=poll_payload)
            poll_resp.raise_for_status()
            poll_result = poll_resp.json()

            task_status = poll_result.get("result", {}).get("status", {})
            state = task_status.get("state") if isinstance(task_status, dict) else task_status

            if state == "completed":
                return _parse_agent_response(poll_result)
            elif state == "failed":
                error = poll_result.get("result", {}).get("error", "Unknown agent error")
                raise RuntimeError(f"Agent task failed: {error}")

        raise TimeoutError(f"Agent did not complete within {AGENT_TIMEOUT}s")


def _parse_agent_response(poll_result: dict) -> dict:
    """Parse A2A response into monitoring result shape."""
    result = poll_result.get("result", {})

    text_content = ""
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                text_content += part.get("text", "")

    try:
        parsed = json.loads(text_content)
    except (json.JSONDecodeError, TypeError) as e:
        raise RuntimeError(f"Agent returned non-JSON response: {text_content[:200]}") from e

    return parsed


async def _complete_task(task_id: str) -> None:
    """Mark task as completed via TaskService."""
    row = await db.fetch_one("SELECT state FROM tasks WHERE id = $1", uuid.UUID(task_id))
    if not row:
        raise RuntimeError(f"Task {task_id} not found")

    current_state = TaskState(row["state"])
    if current_state != TaskState.ACTIVE:
        logger.info(f"Task {task_id} is {current_state.value}, skipping completion")
        return

    task_service = TaskService(db=db)
    result = await task_service.complete(
        task_id=uuid.UUID(task_id),
        current_state=current_state,
    )
    logger.info(f"Task {task_id} completed - schedule {result['schedule_action']}")


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
        agent_response = await _call_agent("\n".join(prompt_parts))

        # Map agent response to execution result
        notification = agent_response.get("notification")
        condition_met = notification is not None
        evidence = agent_response.get("evidence", "")
        sources = agent_response.get("sources", [])
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
                "sources": sources,
                "next_run": next_run,
                "condition_met": condition_met,
                "change_summary": change_summary,
                "grounding_sources": grounding_sources,
            },
        )

        # Send notifications if condition met
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
                    await send_email_notification(
                        user_id, task_name, notification_context, enriched_result
                    )

                if "webhook" in channels:
                    await send_webhook_notification(notification_context, enriched_result)
            except Exception as e:
                logger.error(f"Notification failed for task {task_id}: {e}", exc_info=True)

        # Auto-complete if notify_behavior is "once" and condition met
        if condition_met and task["notify_behavior"] == "once":
            await _complete_task(task_id)

        # Dynamic reschedule if agent returns next_run
        if next_run:
            try:
                scheduler = get_scheduler()
                job_id = f"task-{task_id}"
                scheduler.modify_job(job_id, next_run_time=datetime.fromisoformat(next_run))
                logger.info(f"Rescheduled task {task_id} to {next_run}")
            except Exception as e:
                logger.warning(f"Failed to reschedule task {task_id}: {e}")

    except Exception as e:
        logger.error(f"Task execution failed for {task_id}: {e}")
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


_scheduled_tasks: set[asyncio.Task] = set()


def _handle_scheduled_task_result(task: asyncio.Task) -> None:
    """Log unhandled exceptions from scheduled task executions."""
    _scheduled_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(f"Scheduled task execution failed: {exc}", exc_info=exc)


def execute_task_job(task_id: str, user_id: str, task_name: str) -> None:
    """Entry point for APScheduler cron jobs."""
    bg_task = asyncio.get_running_loop().create_task(
        _execute(task_id=task_id, execution_id=None, user_id=user_id, task_name=task_name)
    )
    _scheduled_tasks.add(bg_task)
    bg_task.add_done_callback(_handle_scheduled_task_result)


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
