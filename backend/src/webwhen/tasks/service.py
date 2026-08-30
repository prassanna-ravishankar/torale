"""Task Service - Unified domain logic for Task management.

This service consolidates:
1. State Management (Transitions, Validations)
2. APScheduler Job Coordination (Create/Pause/Resume/Remove)
3. High-level business logic
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.date import DateTrigger
from asyncpg.exceptions import UniqueViolationError

from webwhen.core.database import Database
from webwhen.scheduler import JOB_FUNC_REF
from webwhen.scheduler.scheduler import get_scheduler
from webwhen.tasks.notifications import prepare_notifications
from webwhen.tasks.repository import TaskRepository
from webwhen.tasks.tasks import TaskCreate, TaskData, TaskState, TaskUpdate

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""


class TaskNotFoundError(LookupError):
    """Raised when a task is missing or inaccessible to an operation."""


class ForkNameConflictError(RuntimeError):
    """Raised when an automatically generated fork name remains non-unique."""


class ActiveTaskLimitError(RuntimeError):
    """Raised when creating a task would exceed the user's active-task limit."""


class TaskPersistenceError(RuntimeError):
    """Raised when task persistence unexpectedly produces no row."""


class TaskScheduleError(RuntimeError):
    """Raised when scheduler coordination fails during task creation."""


class TaskTransitionError(RuntimeError):
    """Raised when scheduler coordination fails during a task update."""


@dataclass(frozen=True)
class TaskUpdateResult:
    """Updated row plus whether it includes latest-execution join aliases."""

    row: dict
    includes_execution: bool


class TaskService:
    """Unified service for Task domain operations.

    Manages state transitions, database updates, and APScheduler job synchronization.
    """

    def __init__(self, db: Database):
        self.db = db
        self.repository = TaskRepository(db)

    async def create(
        self,
        task: TaskCreate,
        user_id: UUID,
        max_active_tasks: int,
        next_run: datetime,
    ) -> dict:
        """Validate, persist, and schedule a newly created task."""
        if task.state == TaskState.ACTIVE:
            active_count = await self.repository.count_active_by_user(user_id)
            if active_count >= max_active_tasks:
                raise ActiveTaskLimitError(
                    f"Maximum of {max_active_tasks} active tasks reached. "
                    "Complete or pause existing tasks first."
                )

        notifications, storage = await prepare_notifications(task.notifications)
        data: TaskData = {
            "user_id": user_id,
            "name": task.name,
            "state": task.state.value,
            "next_run": next_run,
            "search_query": task.search_query,
            "condition_description": task.condition_description or task.search_query,
            "notifications": notifications,
            "notification_channels": storage.notification_channels,
            "notification_email": storage.notification_email,
            "webhook_url": storage.webhook_url,
            "webhook_secret": storage.webhook_secret,
            "context": task.context,
            "attached_connector_slugs": task.attached_connector_slugs,
        }
        row = await self.repository.create_task(data)
        if not row:
            raise TaskPersistenceError("Failed to create task")

        if task.state == TaskState.ACTIVE:
            try:
                await self.create_schedule_for_new_task(
                    task_id=row["id"],
                    task_name=task.name,
                    user_id=user_id,
                    next_run=next_run,
                )
                logger.info("Successfully created schedule for task %s", row["id"])
            except Exception as exc:
                logger.error("Failed to create schedule for task %s: %s", row["id"], exc)
                await self.repository.delete_by_id(row["id"])
                raise TaskScheduleError(f"Failed to create schedule: {exc}") from exc
        return dict(row)

    async def update(
        self, task_id: UUID, user_id: UUID, task_update: TaskUpdate
    ) -> TaskUpdateResult:
        """Persist a task update and coordinate state changes with the scheduler."""
        existing = await self.repository.find_owned(task_id, user_id)
        if not existing:
            raise TaskNotFoundError("Task not found")

        update_data = task_update.model_dump(exclude_unset=True)
        if not update_data:
            return TaskUpdateResult(row=dict(existing), includes_execution=False)

        if "notifications" in update_data:
            notifications, storage = await prepare_notifications(
                update_data["notifications"], old_webhook_url=existing.get("webhook_url")
            )
            update_data.update(
                notifications=notifications,
                notification_channels=storage.notification_channels,
                notification_email=storage.notification_email,
                webhook_url=storage.webhook_url,
            )
            if storage.webhook_secret is not None:
                update_data["webhook_secret"] = storage.webhook_secret

        state_value = update_data.pop("state", None)
        changed_fields: TaskData = update_data
        row = await self.repository.update_owned_fields(task_id, user_id, changed_fields)
        if not row:
            raise TaskPersistenceError("Failed to update task")

        if state_value is not None and state_value != existing["state"]:
            current_state = TaskState(existing["state"])
            new_state = TaskState(state_value)
            try:
                await self.transition(
                    task_id=task_id,
                    from_state=current_state,
                    to_state=new_state,
                    user_id=user_id,
                    task_name=row["name"],
                    next_run=datetime.now(UTC) + timedelta(minutes=1),
                )
                logger.info(
                    "Task %s state transition: %s -> %s",
                    task_id,
                    current_state.value,
                    new_state.value,
                )
            except Exception as exc:
                rollback: TaskData = {"state": existing["state"]}
                rollback.update({field: existing[field] for field in changed_fields})
                await self.repository.restore_fields(task_id, rollback)
                if isinstance(exc, InvalidTransitionError):
                    raise
                raise TaskTransitionError(
                    f"Failed to change task state: {exc}. Task update rolled back."
                ) from exc

        fresh = await self.repository.find_by_id_with_execution(task_id)
        if not fresh:
            raise TaskNotFoundError("Task not found")
        return TaskUpdateResult(row=dict(fresh), includes_execution=True)

    async def fork(self, task_id: UUID, user_id: UUID, requested_name: str | None) -> dict:
        """Copy an accessible task, atomically tracking public subscriptions."""
        source_row = await self.db.fetch_one("SELECT * FROM tasks WHERE id = $1", task_id)
        if not source_row:
            raise TaskNotFoundError("Task not found")
        source = dict(source_row)
        is_owner = source["user_id"] == user_id
        if not is_owner and not source["is_public"]:
            raise TaskNotFoundError("Task not found")

        if is_owner:
            notification_values = (
                source["notifications"],
                source["notification_channels"],
                source["notification_email"],
                source["webhook_url"],
                source["webhook_secret"],
            )
        else:
            notification_values = (json.dumps([]), [], None, None, None)

        base_name = requested_name or f"{source['name']} (Copy)"
        for attempt in range(3):
            fork_name = (
                base_name
                if requested_name or attempt == 0
                else f"{source['name']} (Copy {attempt + 1})"
            )
            try:
                async with self.db.acquire() as conn:
                    async with conn.transaction():
                        if not is_owner:
                            await conn.execute(
                                "UPDATE tasks SET subscriber_count = subscriber_count + 1 WHERE id = $1",
                                task_id,
                            )
                        row = await conn.fetchrow(
                            """
                            INSERT INTO tasks (
                                user_id, name, state, search_query, condition_description,
                                notifications, notification_channels, notification_email,
                                webhook_url, webhook_secret, forked_from_task_id, is_public
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            RETURNING *
                            """,
                            user_id,
                            fork_name,
                            TaskState.PAUSED.value,
                            source["search_query"],
                            source["condition_description"],
                            *notification_values,
                            task_id,
                            False,
                        )
                if row:
                    return dict(row)
                raise RuntimeError("Failed to fork task")
            except UniqueViolationError as exc:
                if attempt == 2:
                    raise ForkNameConflictError(
                        "Failed to generate unique task name after multiple attempts. "
                        "Please provide a custom name."
                    ) from exc
                logger.warning(
                    "Task name collision on attempt %s, retrying with incremented name",
                    attempt + 1,
                )

        raise RuntimeError("Failed to fork task")

    async def transition(
        self,
        task_id: UUID,
        from_state: TaskState,
        to_state: TaskState,
        user_id: UUID | None = None,
        task_name: str | None = None,
        next_run: datetime | None = None,
    ) -> dict:
        """Execute a state transition with validation and scheduler side effects."""
        if not self._is_valid_transition(from_state, to_state):
            raise InvalidTransitionError(
                f"Cannot transition from {from_state.value} to {to_state.value}"
            )

        if from_state == to_state:
            logger.info(
                f"Task {task_id} is already in state {to_state.value}. No transition needed."
            )
            return {"success": True, "schedule_action": "none", "error": None}

        update_result = await self._update_database_state(task_id, to_state, from_state)
        if update_result is False:
            raise InvalidTransitionError(
                f"Task {task_id} state changed concurrently. Expected {from_state.value} but was different."
            )
        elif update_result is None:
            raise RuntimeError(f"Could not parse DB response for task {task_id} state update.")

        try:
            if to_state == TaskState.ACTIVE:
                result = await self._add_or_resume_job(
                    task_id,
                    task_name=task_name,
                    user_id=user_id,
                    next_run=next_run,
                )
            elif to_state == TaskState.PAUSED:
                result = await self._pause_job(task_id)
            elif to_state == TaskState.COMPLETED:
                result = await self._remove_job(task_id)
            else:
                result = {"success": True, "schedule_action": "none", "error": None}

            logger.info(f"Task {task_id} transitioned: {from_state.value} -> {to_state.value}")
            return result

        except Exception as e:
            rollback_success = False
            try:
                await self._update_database_state(task_id, from_state)
                rollback_success = True
            except Exception as rollback_err:
                logger.critical(
                    f"CRITICAL: Rollback failed for task {task_id}, database state inconsistent",
                    extra={
                        "task_id": str(task_id),
                        "attempted_transition": f"{from_state.value} -> {to_state.value}",
                        "rollback_error": str(rollback_err),
                    },
                    exc_info=True,
                )

            if not rollback_success:
                raise RuntimeError(
                    f"State transition failed and rollback failed. Task {task_id} may be in inconsistent state. "
                    f"Manual intervention required. Original error: {e}"
                ) from e

            logger.error(
                f"State transition failed for task {task_id}, successfully rolled back: {e}"
            )
            raise

    async def activate(
        self,
        task_id: UUID,
        current_state: TaskState,
        user_id: UUID,
        task_name: str,
        next_run: datetime | None = None,
    ) -> dict:
        """Activate a task (transition to ACTIVE state)."""
        if next_run is None:
            next_run = datetime.now(UTC) + timedelta(minutes=1)
        return await self.transition(
            task_id,
            current_state,
            TaskState.ACTIVE,
            user_id=user_id,
            task_name=task_name,
            next_run=next_run,
        )

    async def pause(self, task_id: UUID, current_state: TaskState) -> dict:
        """Pause a task (transition to PAUSED state)."""
        return await self.transition(task_id, current_state, TaskState.PAUSED)

    async def complete(self, task_id: UUID, current_state: TaskState) -> dict:
        """Complete a task (transition to COMPLETED state)."""
        return await self.transition(task_id, current_state, TaskState.COMPLETED)

    async def create_schedule_for_new_task(
        self,
        task_id: UUID,
        task_name: str,
        user_id: UUID,
        next_run: datetime | None = None,
    ) -> dict:
        """Create an APScheduler job for a newly created task.

        Unlike transition(), this does NOT update the DB state because
        the task is already being inserted as ACTIVE.
        """
        if next_run is None:
            next_run = datetime.now(UTC) + timedelta(minutes=1)
        return await self._add_or_resume_job(
            task_id,
            task_name=task_name,
            user_id=user_id,
            next_run=next_run,
        )

    # Internal Helpers

    def _is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        if from_state == to_state:
            return True

        valid_transitions = {
            (TaskState.PAUSED, TaskState.ACTIVE),
            (TaskState.ACTIVE, TaskState.PAUSED),
            (TaskState.ACTIVE, TaskState.COMPLETED),
            (TaskState.COMPLETED, TaskState.ACTIVE),
        }
        return (from_state, to_state) in valid_transitions

    async def _update_database_state(
        self, task_id: UUID, state: TaskState, expected_current_state: TaskState | None = None
    ) -> bool | None:
        if expected_current_state is not None:
            result = await self.db.execute(
                """
                UPDATE tasks
                SET state = $1, state_changed_at = NOW(), updated_at = NOW()
                WHERE id = $2 AND state = $3
                """,
                state.value,
                task_id,
                expected_current_state.value,
            )
            try:
                return int(result.split()[-1]) > 0
            except (ValueError, IndexError, AttributeError):
                logger.error(f"Could not parse affected rows from DB result: '{result}'")
                return None
        else:
            await self.db.execute(
                "UPDATE tasks SET state = $1, state_changed_at = NOW(), updated_at = NOW() WHERE id = $2",
                state.value,
                task_id,
            )
            return True

    async def _add_or_resume_job(
        self,
        task_id: UUID,
        task_name: str | None = None,
        user_id: UUID | None = None,
        next_run: datetime | None = None,
    ) -> dict:
        """Add a new job or resume an existing paused one."""
        if not all([task_name, user_id, next_run]):
            raise ValueError("Cannot activate task: missing task_name, user_id, or next_run")

        scheduler = get_scheduler()
        job_id = f"task-{task_id}"
        existing = await asyncio.to_thread(scheduler.get_job, job_id)

        if existing is not None:
            # Job exists, resume it and update trigger
            await asyncio.to_thread(scheduler.resume_job, job_id)
            await asyncio.to_thread(
                scheduler.reschedule_job, job_id, trigger=DateTrigger(run_date=next_run)
            )
            logger.info(f"Resumed job {job_id}")
        else:
            # Create new job
            await asyncio.to_thread(
                scheduler.add_job,
                JOB_FUNC_REF,
                trigger=DateTrigger(run_date=next_run),
                id=job_id,
                args=[str(task_id), str(user_id), task_name],
                replace_existing=True,
            )
            logger.info(f"Created job {job_id}")

        # Persist next_run to DB
        await self.db.execute(
            "UPDATE tasks SET next_run = $1 WHERE id = $2",
            next_run,
            task_id,
        )

        return {"success": True, "schedule_action": "created", "error": None}

    async def _pause_job(self, task_id: UUID) -> dict:
        scheduler = get_scheduler()
        job_id = f"task-{task_id}"
        existing = await asyncio.to_thread(scheduler.get_job, job_id)

        if existing is None:
            logger.info(f"Job {job_id} not found when pausing - already deleted or never existed")
            return {"success": True, "schedule_action": "not_found_ok", "error": None}

        await asyncio.to_thread(scheduler.pause_job, job_id)
        logger.info(f"Paused job {job_id}")
        return {"success": True, "schedule_action": "paused", "error": None}

    async def _remove_job(self, task_id: UUID) -> dict:
        scheduler = get_scheduler()
        job_id = f"task-{task_id}"

        try:
            await asyncio.to_thread(scheduler.remove_job, job_id)
            logger.info(f"Removed job {job_id}")
            return {"success": True, "schedule_action": "deleted", "error": None}
        except JobLookupError:
            logger.info(f"Job {job_id} not found when removing - already deleted or never existed")
            return {"success": True, "schedule_action": "not_found_ok", "error": None}
