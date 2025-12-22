"""
Task Service - Unified domain logic for Task management.

This service consolidates:
1. State Management (Transitions, Validations)
2. Temporal Schedule Coordination (Create/Pause/Unpause)
3. High-level business logic
"""

import logging
from uuid import UUID

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleSpec,
)
from temporalio.service import RPCError, RPCStatusCode

from torale.core.config import settings
from torale.core.database import Database
from torale.tasks.tasks import TaskExecutionRequest, TaskState
from torale.workers.workflows import TaskExecutionWorkflow

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    pass


class TaskService:
    """
    Unified service for Task domain operations.

    Manages state transitions, database updates, and Temporal schedule synchronization.
    """

    def __init__(self, db: Database):
        """
        Initialize TaskService.

        Args:
            db: Database connection wrapper
        """
        self.db = db
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

    async def transition(
        self,
        task_id: UUID,
        from_state: TaskState,
        to_state: TaskState,
        user_id: UUID | None = None,
        task_name: str | None = None,
        schedule: str | None = None,
    ) -> dict:
        """
        Execute a state transition with validation and Temporal side effects.

        Args:
            task_id: UUID of the task
            from_state: Current state of the task
            to_state: Desired state of the task
            user_id: User UUID (required for creating missing schedules if activating)
            task_name: Task name (required for creating missing schedules if activating)
            schedule: Cron expression (required for creating missing schedules if activating)

        Returns:
            dict with:
                - success: bool
                - schedule_action: str ("paused", "unpaused", "created", etc.)
                - error: str | None

        Raises:
            InvalidTransitionError: If transition is not allowed
            Exception: If database or Temporal operation fails
        """
        # 1. Validate transition
        if not self._is_valid_transition(from_state, to_state):
            raise InvalidTransitionError(
                f"Cannot transition from {from_state.value} to {to_state.value}"
            )

        # Handle idempotent case to avoid unnecessary DB updates and side effects
        if from_state == to_state:
            logger.info(
                f"Task {task_id} is already in state {to_state.value}. No transition needed."
            )
            return {"success": True, "schedule_action": "none", "error": None}

        # 2. Update database FIRST (fail fast if DB error)
        # Use conditional update to prevent race conditions
        update_result = await self._update_database_state(task_id, to_state, from_state)
        if update_result is False:
            raise InvalidTransitionError(
                f"Task {task_id} state changed concurrently. Expected {from_state.value} but was different."
            )
        elif update_result is None:
            raise RuntimeError(f"Could not parse DB response for task {task_id} state update.")

        # 3. Apply Temporal side effect
        try:
            if to_state == TaskState.ACTIVE:
                result = await self._set_temporal_state(
                    task_id,
                    is_active=True,
                    task_name=task_name,
                    user_id=user_id,
                    schedule=schedule,
                )
            elif to_state == TaskState.PAUSED:
                result = await self._set_temporal_state(
                    task_id,
                    is_active=False,
                )
            elif to_state == TaskState.COMPLETED:
                # Delete schedule for completed tasks (won't run again unless re-activated)
                result = await self._delete_schedule(task_id)
            else:
                # Should not happen given _is_valid_transition, but safe default
                result = {"success": True, "schedule_action": "none", "error": None}

            logger.info(f"Task {task_id} transitioned: {from_state.value} → {to_state.value}")
            return result

        except Exception as e:
            # Rollback database if Temporal fails
            await self._update_database_state(task_id, from_state)
            logger.error(f"State transition failed for task {task_id}, rolled back: {e}")
            raise

    # Public Convenience Methods

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
        """
        Create a Temporal schedule for a newly created task.

        Unlike transition(), this does NOT update the DB state because
        the task is already being inserted as ACTIVE.
        """
        return await self._set_temporal_state(
            task_id,
            is_active=True,
            task_name=task_name,
            user_id=user_id,
            schedule=schedule,
        )

    # Internal Helpers

    def _is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if transition is valid."""
        # Allow same-state transitions (idempotent)
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
        """Update task state in database."""
        if expected_current_state is not None:
            # Conditional update - only update if current state matches expected
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
            # Parse affected rows from DB result
            try:
                return int(result.split()[-1]) > 0
            except (ValueError, IndexError, AttributeError):
                logger.warning(f"Could not parse affected rows from DB result: '{result}'")
                return None
        else:
            # Unconditional update (for rollback scenarios)
            await self.db.execute(
                "UPDATE tasks SET state = $1, state_changed_at = NOW(), updated_at = NOW() WHERE id = $2",
                state.value,
                task_id,
            )
            return True

    async def _set_temporal_state(
        self,
        task_id: UUID,
        is_active: bool,
        task_name: str | None = None,
        user_id: UUID | None = None,
        schedule: str | None = None,
    ) -> dict:
        """
        Set task activation state and sync with Temporal schedule.

        Logic adopted from TaskStateManager.
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
                                policy=SchedulePolicy(
                                    overlap=ScheduleOverlapPolicy.SKIP,
                                ),
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

        # For deactivations, pause the schedule
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
                    logger.info(
                        f"Schedule {schedule_id} not found when deactivating - already deleted or never existed"
                    )
                    return {
                        "success": True,
                        "schedule_action": "not_found_ok",
                        "error": None,
                    }
                else:
                    logger.error(f"Failed to pause schedule {schedule_id}: {str(e)}")
                    raise

    async def _delete_schedule(self, task_id: UUID) -> dict:
        """Delete a Temporal schedule permanently."""
        schedule_id = f"schedule-{task_id}"
        client = await self._get_temporal_client()

        try:
            schedule_handle = client.get_schedule_handle(schedule_id)
            logger.info(f"Deleting schedule {schedule_id}")
            await schedule_handle.delete()
            logger.info(f"Successfully deleted schedule {schedule_id}")
            return {
                "success": True,
                "schedule_action": "deleted",
                "error": None,
            }
        except RPCError as e:
            if e.status == RPCStatusCode.NOT_FOUND:
                logger.info(
                    f"Schedule {schedule_id} not found when deleting - already deleted or never existed"
                )
                return {
                    "success": True,
                    "schedule_action": "not_found_ok",
                    "error": None,
                }
            else:
                logger.error(f"Failed to delete schedule {schedule_id}: {str(e)}")
                raise
