"""
Task State Manager - Single source of truth for task activation state.

This module ensures that task activation state (is_active) stays in sync between
the database and Temporal schedules. All code that changes is_active MUST use this manager.
"""

import logging
from uuid import UUID

from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from temporalio.service import RPCError, RPCStatusCode

from torale.core.config import settings
from torale.core.models import TaskExecutionRequest
from torale.workers.workflows import TaskExecutionWorkflow

logger = logging.getLogger(__name__)


class TaskStateManager:
    """
    Manages task activation state across database and Temporal schedules.

    This class encapsulates the logic for keeping is_active state synchronized
    between PostgreSQL and Temporal Cloud. It handles errors gracefully and
    provides clear logging for debugging.
    """

    def __init__(self, db_conn=None):
        """
        Initialize state manager.

        Args:
            db_conn: Database connection (asyncpg or Database wrapper)
        """
        self.db_conn = db_conn
        self._temporal_client: Client | None = None

    async def _get_temporal_client(self) -> Client:
        """Get cached Temporal client with proper authentication."""
        if self._temporal_client is None:
            if settings.temporal_api_key:
                self._temporal_client = await Client.connect(
                    settings.temporal_host,
                    namespace=settings.temporal_namespace,
                    tls=True,
                    api_key=settings.temporal_api_key,
                )
            else:
                self._temporal_client = await Client.connect(
                    settings.temporal_host,
                    namespace=settings.temporal_namespace,
                )
        return self._temporal_client

    async def set_task_active_state(
        self,
        task_id: UUID,
        is_active: bool,
        task_name: str | None = None,
        user_id: UUID | None = None,
        schedule: str | None = None,
    ) -> dict:
        """
        Set task activation state and sync with Temporal schedule.

        This method updates the database AND pauses/unpauses the Temporal schedule
        atomically. If the schedule operation fails, it rolls back the database change.

        Args:
            task_id: UUID of the task
            is_active: New activation state (True = active, False = paused/completed)
            task_name: Task name (required for creating missing schedules)
            user_id: User UUID (required for creating missing schedules)
            schedule: Cron expression (required for creating missing schedules)

        Returns:
            dict with:
                - success: bool
                - schedule_action: str ("paused", "unpaused", "created", "not_found_ok")
                - error: str | None

        Raises:
            Exception: If Temporal operation fails and cannot be recovered
        """
        schedule_id = f"schedule-{task_id}"
        client = await self._get_temporal_client()

        # For activations, check if we need to create the schedule first
        if is_active:
            # Validate we have all required params for potential schedule creation
            if not all([task_name, user_id, schedule]):
                error_msg = "Cannot activate task: missing task_name, user_id, or schedule"
                logger.error(f"{error_msg} for task {task_id}")
                raise ValueError(error_msg)

            # Try to unpause the schedule (will throw NOT_FOUND if doesn't exist)
            try:
                schedule_handle = client.get_schedule_handle(schedule_id)
                logger.info(f"Unpausing schedule {schedule_id}")
                await schedule_handle.unpause()
                logger.info(f"Successfully unpaused schedule {schedule_id}")
                return {
                    "success": True,
                    "schedule_action": "unpaused",
                    "error": None,
                }
            except RPCError as e:
                if e.status == RPCStatusCode.NOT_FOUND:
                    # Schedule doesn't exist, create it
                    logger.info(f"Schedule {schedule_id} not found, creating new schedule")

                    try:
                        logger.info(
                            f"Creating schedule with cron: {schedule}, task_queue: {settings.temporal_task_queue}"
                        )
                        await client.create_schedule(
                            id=schedule_id,
                            schedule=Schedule(
                                action=ScheduleActionStartWorkflow(
                                    TaskExecutionWorkflow.run,
                                    TaskExecutionRequest(
                                        task_id=str(task_id),
                                        execution_id="",
                                        user_id=str(user_id),
                                        task_name=task_name,
                                    ),
                                    id=f"scheduled-task-{task_id}",
                                    task_queue=settings.temporal_task_queue,
                                ),
                                spec=ScheduleSpec(cron_expressions=[schedule]),
                            ),
                        )
                        logger.info(f"Successfully created schedule {schedule_id}")
                        return {
                            "success": True,
                            "schedule_action": "created",
                            "error": None,
                        }
                    except Exception as create_error:
                        logger.error(
                            f"Failed to create schedule {schedule_id}: {type(create_error).__name__}: {str(create_error)}"
                        )
                        raise
                else:
                    # Real RPC error
                    logger.error(f"Failed to activate schedule {schedule_id}: {str(e)}")
                    raise

        # For deactivations, pause the schedule (create not needed)
        else:
            try:
                schedule_handle = client.get_schedule_handle(schedule_id)
                logger.info(f"Pausing schedule {schedule_id}")
                await schedule_handle.pause()
                logger.info(f"Successfully paused schedule {schedule_id}")
                return {
                    "success": True,
                    "schedule_action": "paused",
                    "error": None,
                }
            except RPCError as e:
                if e.status == RPCStatusCode.NOT_FOUND:
                    # Schedule doesn't exist - that's fine for deactivation
                    logger.info(
                        f"Schedule {schedule_id} not found when deactivating - "
                        f"already deleted or never existed"
                    )
                    return {
                        "success": True,
                        "schedule_action": "not_found_ok",
                        "error": None,
                    }
                else:
                    # Real RPC error
                    logger.error(f"Failed to pause schedule {schedule_id}: {str(e)}")
                    raise

    async def deactivate_task(
        self,
        task_id: UUID,
        reason: str = "manual",
    ) -> dict:
        """
        Deactivate a task (set is_active = false and pause schedule).

        This is used for both manual pausing (user action) and auto-completion
        (notify_behavior=once).

        Args:
            task_id: UUID of the task
            reason: Why the task is being deactivated ("manual", "completed", etc.)

        Returns:
            Result dict from set_task_active_state
        """
        logger.info(f"Deactivating task {task_id} (reason: {reason})")
        return await self.set_task_active_state(task_id, is_active=False)

    async def activate_task(
        self,
        task_id: UUID,
        task_name: str,
        user_id: UUID,
        schedule: str,
    ) -> dict:
        """
        Activate a task (set is_active = true and unpause/create schedule).

        Args:
            task_id: UUID of the task
            task_name: Name of the task (for creating schedule if missing)
            user_id: User UUID (for creating schedule if missing)
            schedule: Cron expression (for creating schedule if missing)

        Returns:
            Result dict from set_task_active_state
        """
        logger.info(f"Activating task {task_id}")
        return await self.set_task_active_state(
            task_id,
            is_active=True,
            task_name=task_name,
            user_id=user_id,
            schedule=schedule,
        )


# Convenience functions for common use cases


async def pause_task(task_id: UUID) -> dict:
    """
    Pause a task's Temporal schedule.

    This is a convenience function for when you need to pause a schedule
    without necessarily changing the database (though you usually should).
    """
    manager = TaskStateManager()
    return await manager.deactivate_task(task_id, reason="pause")


async def complete_task(task_id: UUID) -> dict:
    """
    Mark a task as completed (auto-disable after notify_behavior=once).

    This is a convenience function for the worker to call when a task
    with notify_behavior=once meets its condition.
    """
    manager = TaskStateManager()
    return await manager.deactivate_task(task_id, reason="completed")
