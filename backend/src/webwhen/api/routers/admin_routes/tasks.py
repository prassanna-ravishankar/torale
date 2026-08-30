"""Admin task-operation routes."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from webwhen.access import ClerkUser, require_admin
from webwhen.api.routers.tasks import start_task_execution
from webwhen.core.database import Database, get_db
from webwhen.tasks import TaskState
from webwhen.tasks.service import InvalidTransitionError, TaskService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tasks/{task_id}/execute")
async def admin_execute_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    suppress_notifications: bool = Query(default=False),
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Execute a task immediately (admin only).

    Allows admins to manually trigger execution of any user's task.

    Path Parameters:
    - task_id: UUID of the task to execute

    Query Parameters:
    - suppress_notifications: Whether to suppress notifications (default: false - notifications enabled)

    Returns:
    - Execution ID and status
    """
    task_row = await db.fetch_one(
        "SELECT t.id, t.name, t.user_id FROM tasks t WHERE t.id = $1",
        task_id,
    )

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    execution_row = await start_task_execution(
        task_id=str(task_id),
        task_name=task_row["name"],
        user_id=str(task_row["user_id"]),
        db=db,
        background_tasks=background_tasks,
        suppress_notifications=suppress_notifications,
        force=True,
    )

    logger.info(f"Admin {admin.email} started execution {execution_row['id']} for task {task_id}")

    return {
        "id": str(execution_row["id"]),
        "task_id": str(task_id),
        "status": "pending",
        "message": f"Execution started (notifications {'suppressed' if suppress_notifications else 'enabled'})",
    }


class AdminTaskStateUpdateRequest(BaseModel):
    """Request model for updating task state.

    Note: While 'completed' is technically supported, the admin UI only exposes
    pause/resume actions (active ↔ paused). The 'completed' state can be used
    via API for advanced operations or future features.
    """

    state: TaskState = Field(
        ...,
        description="Target state: 'active' (resume), 'paused' (pause), or 'completed' (archive)",
    )


@router.patch("/tasks/{task_id}/state")
async def admin_update_task_state(
    task_id: UUID,
    request: AdminTaskStateUpdateRequest,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Update a task's state (admin-only).

    Allows admins to transition any task through valid state changes:
    - ACTIVE ↔ PAUSED (pause/resume monitoring)
    - ACTIVE → COMPLETED (mark as done)
    - COMPLETED → ACTIVE (reactivate completed task)

    Invalid transitions (e.g., PAUSED → COMPLETED) are rejected with 400 error.

    When transitioning to ACTIVE:
    - Scheduler job is created or resumed
    - next_run is preserved from DB or defaults to 1 minute from now
    - Requires task_name, user_id (both fetched from DB)

    Returns:
    - 200: State updated successfully
    - 400: Invalid transition or missing required data
    - 404: Task not found
    - 500: Scheduler or database error (may leave task in inconsistent state)
    """
    task_row = await db.fetch_one(
        "SELECT id, name, state, user_id, next_run FROM tasks WHERE id = $1",
        task_id,
    )

    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_state = TaskState(task_row["state"])
    target_state = request.state

    next_run = None
    if target_state == TaskState.ACTIVE:
        next_run = task_row["next_run"] or datetime.now(UTC) + timedelta(minutes=1)

    try:
        task_service = TaskService(db)
        result = await task_service.transition(
            task_id=task_id,
            from_state=previous_state,
            to_state=target_state,
            user_id=task_row["user_id"],
            task_name=task_row["name"],
            next_run=next_run,
        )
    except InvalidTransitionError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition: {str(e)}",
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task data: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(
            f"Failed to transition task {task_id} from {previous_state.value} to {target_state.value}",
            exc_info=True,
            extra={
                "task_id": str(task_id),
                "from_state": previous_state.value,
                "to_state": target_state.value,
                "admin_clerk_id": admin.clerk_user_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update task state. The task may be in an inconsistent state.",
        ) from e

    logger.info(
        f"Admin user {admin.clerk_user_id} changed task {task_id} state: {previous_state.value} -> {target_state.value}",
        extra={
            "task_id": str(task_id),
            "admin_clerk_id": admin.clerk_user_id,
            "from_state": previous_state.value,
            "to_state": target_state.value,
            "schedule_action": result.get("schedule_action"),
        },
    )

    return {
        "id": str(task_id),
        "state": target_state.value,
        "previous_state": previous_state.value,
        "message": f"Task state updated to {target_state.value}",
    }


@router.delete("/tasks/{task_id}/reset")
async def reset_task_history(
    task_id: UUID,
    days: int = Query(default=1, ge=1, le=30, description="Delete executions from last N days"),
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Reset task execution history (admin only).

    Deletes all executions from the last N days and resets task state.
    This forces the agent to re-evaluate fresh on next run.

    Path Parameters:
    - task_id: UUID of the task to reset

    Query Parameters:
    - days: Delete executions from last N days (default: 1, max: 30)

    Returns:
    - Status confirmation with count of deleted executions
    """
    check_row = await db.fetch_one("SELECT id FROM tasks WHERE id = $1", task_id)
    if not check_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    cutoff = datetime.now(UTC) - timedelta(days=days)

    # Multi-statement operation needs a transaction
    async with db.acquire() as conn:
        async with conn.transaction():
            deleted_rows = await conn.fetch(
                """
                DELETE FROM task_executions
                WHERE task_id = $1 AND created_at >= $2
                RETURNING id
                """,
                task_id,
                cutoff,
            )
            deleted_count = len(deleted_rows)

            if deleted_count == 0:
                logger.warning(
                    f"Admin {admin.clerk_user_id} reset task {task_id} but found no executions in last {days} day(s)"
                )

            await conn.execute(
                """
                UPDATE tasks
                SET last_execution_id = NULL,
                    last_known_state = NULL,
                    state_changed_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                """,
                task_id,
            )

    logger.info(
        f"Admin {admin.clerk_user_id} reset task {task_id}: deleted {deleted_count} executions from last {days} day(s)"
    )

    return {
        "status": "reset",
        "task_id": str(task_id),
        "executions_deleted": deleted_count,
        "days": days,
    }
