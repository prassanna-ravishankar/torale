"""Task State Machine - Manages state transitions with Temporal side effects."""

import logging
from uuid import UUID

from torale.core.models import TaskState
from torale.core.task_state import TaskStateManager

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    pass


class TaskStateMachine:
    """
    Manages task state transitions and ensures Temporal schedules stay in sync.

    Valid transitions:
    - PAUSED → ACTIVE (user activates)
    - ACTIVE → PAUSED (user pauses)
    - ACTIVE → COMPLETED (notify_behavior=once triggers)
    - COMPLETED → ACTIVE (user re-activates)

    Invalid transitions:
    - PAUSED → COMPLETED (can't complete a paused task)
    - COMPLETED → PAUSED (completed is terminal)
    """

    def __init__(self, db_conn=None):
        """
        Initialize state machine.

        Args:
            db_conn: Database connection (asyncpg or Database wrapper)
        """
        self.db_conn = db_conn
        self._state_manager = TaskStateManager(db_conn)

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
            user_id: User UUID (required for creating missing schedules)
            task_name: Task name (required for creating missing schedules)
            schedule: Cron expression (required for creating missing schedules)

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

        # 2. Update database FIRST (fail fast if DB error)
        # Use conditional update to prevent race conditions
        success = await self._update_database_state(task_id, to_state, from_state)
        if not success:
            raise InvalidTransitionError(
                f"Task {task_id} state changed concurrently. Expected {from_state.value} but was different."
            )

        # 3. Apply Temporal side effect
        try:
            if to_state == TaskState.ACTIVE:
                result = await self._state_manager.set_task_active_state(
                    task_id,
                    is_active=True,
                    task_name=task_name,
                    user_id=user_id,
                    schedule=schedule,
                )
            elif to_state == TaskState.PAUSED:
                result = await self._state_manager.set_task_active_state(
                    task_id,
                    is_active=False,
                )
            elif to_state == TaskState.COMPLETED:
                # Delete schedule for completed tasks (won't run again unless re-activated)
                result = await self._state_manager.delete_schedule(task_id)

            logger.info(f"Task {task_id} transitioned: {from_state.value} → {to_state.value}")
            return result

        except Exception as e:
            # Rollback database if Temporal fails
            await self._update_database_state(task_id, from_state)
            logger.error(f"State transition failed for task {task_id}, rolled back: {e}")
            raise

    def _is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """
        Check if transition is valid.

        Args:
            from_state: Current state
            to_state: Desired state

        Returns:
            True if transition is valid, False otherwise
        """
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
    ) -> bool:
        """
        Update task state in database.

        Args:
            task_id: UUID of the task
            state: New state
            expected_current_state: If provided, only update if current state matches this

        Returns:
            True if update was successful, False if state didn't match expected
        """
        if expected_current_state is not None:
            # Conditional update - only update if current state matches expected
            result = await self.db_conn.execute(
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
            # asyncpg returns strings like "UPDATE N" where N is the affected rows
            try:
                return int(result.split()[-1]) > 0
            except (ValueError, IndexError):
                logger.warning(f"Could not parse affected rows from DB result: '{result}'")
                return False
        else:
            # Unconditional update (for rollback scenarios)
            await self.db_conn.execute(
                "UPDATE tasks SET state = $1, state_changed_at = NOW(), updated_at = NOW() WHERE id = $2",
                state.value,
                task_id,
            )
            return True

    # Convenience methods for common transitions

    async def activate(
        self,
        task_id: UUID,
        current_state: TaskState,
        user_id: UUID,
        task_name: str,
        schedule: str,
    ) -> dict:
        """
        Activate a task (transition to ACTIVE state).

        Args:
            task_id: UUID of the task
            current_state: Current state of the task
            user_id: User UUID
            task_name: Task name
            schedule: Cron expression

        Returns:
            Result dict from transition
        """
        return await self.transition(
            task_id,
            current_state,
            TaskState.ACTIVE,
            user_id=user_id,
            task_name=task_name,
            schedule=schedule,
        )

    async def pause(self, task_id: UUID, current_state: TaskState) -> dict:
        """
        Pause a task (transition to PAUSED state).

        Args:
            task_id: UUID of the task
            current_state: Current state of the task

        Returns:
            Result dict from transition
        """
        return await self.transition(task_id, current_state, TaskState.PAUSED)

    async def complete(self, task_id: UUID, current_state: TaskState) -> dict:
        """
        Complete a task (transition to COMPLETED state).

        This is typically called by the worker when a task with
        notify_behavior=once meets its condition.

        Args:
            task_id: UUID of the task
            current_state: Current state of the task

        Returns:
            Result dict from transition
        """
        return await self.transition(task_id, current_state, TaskState.COMPLETED)
