"""Manual task execution orchestration, independent of HTTP routing."""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from starlette.background import BackgroundTasks

from webwhen.core.database import Database
from webwhen.scheduler.job import execute_task_job_manual
from webwhen.scheduler.scheduler import get_scheduler
from webwhen.tasks.tasks import TaskStatus

logger = logging.getLogger(__name__)


class ExecutionAlreadyRunningError(RuntimeError):
    """Raised when a non-forced execution would overlap an existing run."""


class ExecutionCreationError(RuntimeError):
    """Raised when an execution record cannot be created."""


async def safe_execute_task_job_manual(**kwargs) -> None:
    """Run a background execution while retaining failures in application logs."""
    try:
        await execute_task_job_manual(**kwargs)
    except Exception as exc:
        logger.error(
            "Background task execution failed for task %s, execution %s: %s",
            kwargs["task_id"],
            kwargs["execution_id"],
            exc,
            exc_info=True,
        )


async def start_task_execution(
    task_id: str,
    task_name: str,
    user_id: str,
    db: Database,
    background_tasks: BackgroundTasks,
    suppress_notifications: bool = False,
    force: bool = False,
    *,
    scheduler_factory: Callable | None = None,
) -> dict:
    """Create an execution record and enqueue agent execution."""
    running = await db.fetch_one(
        "SELECT id, status, started_at FROM task_executions WHERE task_id = $1 AND status IN ($2, $3)",
        UUID(task_id),
        TaskStatus.RUNNING.value,
        TaskStatus.PENDING.value,
    )
    if running and not force:
        raise ExecutionAlreadyRunningError("Task is already running or pending")

    if running:
        await db.execute(
            """
            UPDATE task_executions
            SET status = $1, error_message = $2, internal_error = $3, completed_at = $4
            WHERE id = $5
            """,
            TaskStatus.CANCELLED.value,
            "Execution cancelled by manual force run",
            "Force override triggered from admin/manual execution",
            datetime.now(UTC),
            running["id"],
        )
        logger.warning(
            "Force-cancelling stuck execution %s for task %s (was %s since %s)",
            running["id"],
            task_id,
            running["status"],
            running["started_at"],
        )

    scheduler = (scheduler_factory or get_scheduler)()
    job_id = f"task-{task_id}"
    existing_job = await asyncio.to_thread(scheduler.get_job, job_id)
    if existing_job:
        await asyncio.to_thread(scheduler.remove_job, job_id)
        logger.info("Cancelled pending retry job for task %s", task_id)

    previous = await db.fetch_one(
        """SELECT retry_count FROM task_executions
           WHERE task_id = $1 ORDER BY started_at DESC LIMIT 1""",
        UUID(task_id),
    )
    retry_count = previous["retry_count"] if previous else 0
    row = await db.fetch_one(
        """
        INSERT INTO task_executions (task_id, status)
        VALUES ($1, $2)
        RETURNING id, task_id, status, started_at, completed_at, result, error_message, created_at
        """,
        UUID(task_id),
        TaskStatus.PENDING.value,
    )
    if not row:
        raise ExecutionCreationError("Failed to create execution record")

    background_tasks.add_task(
        safe_execute_task_job_manual,
        task_id=task_id,
        execution_id=str(row["id"]),
        user_id=user_id,
        task_name=task_name,
        suppress_notifications=suppress_notifications,
        retry_count=retry_count,
    )
    logger.info(
        "Started execution %s for task %s (retry_count=%s)", row["id"], task_id, retry_count
    )
    return dict(row)
