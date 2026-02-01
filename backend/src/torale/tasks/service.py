"""Task Service - Unified domain logic for Task management.

This service consolidates:
1. State Management (Transitions, Validations)
2. APScheduler Job Coordination (Create/Pause/Resume/Remove)
3. High-level business logic
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.jobstores.base import JobLookupError
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from torale.core.database import Database
from torale.scheduler import JOB_FUNC_REF
from torale.scheduler.scheduler import get_scheduler
from torale.tasks.tasks import TaskState

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""


class TaskService:
    """Unified service for Task domain operations.

    Manages state transitions, database updates, and APScheduler job synchronization.
    """

    def __init__(self, db: Database):
        self.db = db

    async def transition(
        self,
        task_id: UUID,
        from_state: TaskState,
        to_state: TaskState,
        user_id: UUID | None = None,
        task_name: str | None = None,
        schedule: str | None = None,
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
                    schedule=schedule,
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
            try:
                await self._update_database_state(task_id, from_state)
            except Exception as rollback_err:
                logger.error(f"Rollback failed for task {task_id}: {rollback_err}", exc_info=True)
            logger.error(f"State transition failed for task {task_id}, rolled back: {e}")
            raise

    async def activate(
        self,
        task_id: UUID,
        current_state: TaskState,
        user_id: UUID,
        task_name: str,
        schedule: str,
    ) -> dict:
        """Activate a task (transition to ACTIVE state)."""
        return await self.transition(
            task_id,
            current_state,
            TaskState.ACTIVE,
            user_id=user_id,
            task_name=task_name,
            schedule=schedule,
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
        schedule: str,
    ) -> dict:
        """Create an APScheduler job for a newly created task.

        Unlike transition(), this does NOT update the DB state because
        the task is already being inserted as ACTIVE.
        """
        return await self._add_or_resume_job(
            task_id,
            task_name=task_name,
            user_id=user_id,
            schedule=schedule,
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
        schedule: str | None = None,
    ) -> dict:
        """Add a new job or resume an existing paused one."""
        if not all([task_name, user_id, schedule]):
            raise ValueError("Cannot activate task: missing task_name, user_id, or schedule")

        scheduler = get_scheduler()
        job_id = f"task-{task_id}"
        existing = await asyncio.to_thread(scheduler.get_job, job_id)
        next_run = self._compute_next_run(schedule)

        if existing is not None:
            # Job exists, resume it and update trigger
            await asyncio.to_thread(scheduler.resume_job, job_id)
            await asyncio.to_thread(
                scheduler.reschedule_job, job_id, trigger=DateTrigger(run_date=next_run)
            )
            logger.info(f"Resumed job {job_id}")
            return {"success": True, "schedule_action": "resumed", "error": None}

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
        return {"success": True, "schedule_action": "created", "error": None}

    def _compute_next_run(self, schedule: str | None) -> datetime:
        now = datetime.now(UTC)
        if schedule:
            try:
                trigger = CronTrigger.from_crontab(schedule, timezone=UTC)
                next_time = trigger.get_next_fire_time(None, now)
                if next_time and next_time > now:
                    return next_time
            except Exception as e:
                logger.warning(f"Failed to parse schedule '{schedule}': {e}")
        return now + timedelta(hours=24)

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
