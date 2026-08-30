import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.jobstores.base import JobLookupError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from webwhen.access import CurrentUser
from webwhen.api.rate_limiter import get_user_or_ip, limiter
from webwhen.api.utils.task_parsers import (
    fetch_feed_executions,
    parse_execution_row,
    parse_task_row,
    parse_task_with_execution,
)
from webwhen.core.config import settings
from webwhen.core.database import Database, get_db
from webwhen.core.views import increment_view
from webwhen.scheduler.scheduler import get_scheduler
from webwhen.tasks import (
    FeedExecution,
    Task,
    TaskCreate,
    TaskExecution,
    TaskState,
    TaskUpdate,
)
from webwhen.tasks.execution import (
    ExecutionAlreadyRunningError,
    ExecutionCreationError,
)
from webwhen.tasks.execution import (
    start_task_execution as _start_task_execution,
)
from webwhen.tasks.notifications import TaskNotificationError, prepare_notifications
from webwhen.tasks.repository import TaskExecutionRepository, TaskRepository
from webwhen.tasks.service import (
    ForkNameConflictError,
    InvalidTransitionError,
    TaskNotFoundError,
    TaskService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _check_task_access(db: Database, task_id: UUID, user) -> tuple[dict, bool]:
    """Verify task exists and user has access (owner or public). Returns (task row, is_owner)."""
    row = await TaskRepository(db).find_access_record(task_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    is_owner = user is not None and row["user_id"] == user.id
    if not is_owner and not row["is_public"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return dict(row), is_owner


@router.post("/", response_model=Task)
@limiter.limit("10/minute", key_func=get_user_or_ip)
async def create_task(
    request: Request,
    task: TaskCreate,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
):
    if task.state == TaskState.ACTIVE:
        active_count = await db.fetch_val(
            "SELECT COUNT(*) FROM tasks WHERE user_id = $1 AND state = 'active'",
            user.id,
        )
        if active_count >= settings.max_active_tasks_per_user:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Maximum of {settings.max_active_tasks_per_user} active tasks reached. Complete or pause existing tasks first.",
            )

    # Validate notifications and extract fields for database
    try:
        validated_notifications, extracted = await prepare_notifications(task.notifications)
    except TaskNotificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    final_condition = task.condition_description or task.search_query
    initial_next_run = datetime.now(UTC) + timedelta(minutes=1)

    # Create task in database
    query = """
        INSERT INTO tasks (
            user_id, name, state, next_run,
            search_query, condition_description, notifications,
            notification_channels, notification_email, webhook_url, webhook_secret,
            context, attached_connector_slugs
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING *
    """

    row = await db.fetch_one(
        query,
        user.id,
        task.name,
        task.state.value,
        initial_next_run,
        task.search_query,
        final_condition,
        json.dumps(validated_notifications),
        extracted.notification_channels,
        extracted.notification_email,
        extracted.webhook_url,
        extracted.webhook_secret,
        task.context,
        task.attached_connector_slugs,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create task",
        )

    task_id = str(row["id"])

    # Create APScheduler job for automatic execution if task is active
    if task.state == TaskState.ACTIVE:
        try:
            task_service = TaskService(db=db)
            # For new tasks, create the schedule directly (not a transition)
            await task_service.create_schedule_for_new_task(
                task_id=UUID(task_id),
                task_name=task.name,
                user_id=user.id,
                next_run=initial_next_run,
            )
            logger.info(f"Successfully created schedule for task {task_id}")
        except Exception as e:
            # If schedule creation fails, delete the task and raise error
            logger.error(f"Failed to create schedule for task {task_id}: {str(e)}")
            await db.execute("DELETE FROM tasks WHERE id = $1", row["id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {str(e)}",
            ) from e

    # Execute task immediately if requested
    immediate_execution_error = None
    if task.run_immediately:
        try:
            await start_task_execution(
                task_id=task_id,
                task_name=task.name,
                user_id=str(user.id),
                db=db,
                background_tasks=background_tasks,
                suppress_notifications=False,  # First run should notify
            )
        except Exception as e:
            logger.error(f"Failed to start immediate execution for task {task_id}: {e}")
            immediate_execution_error = str(e)

    return Task(**parse_task_row(row), immediate_execution_error=immediate_execution_error)


@router.get("/", response_model=list[Task])
async def list_tasks(
    user: CurrentUser, state: TaskState | None = None, db: Database = Depends(get_db)
):
    repo = TaskRepository(db)
    rows = await repo.find_by_user(user.id, state=state)
    return [parse_task_with_execution(row) for row in rows]


@router.get("/feed", response_model=list[FeedExecution])
async def get_user_feed(
    user: CurrentUser, limit: int = Query(50, ge=1, le=100), db: Database = Depends(get_db)
):
    """
    Get a feed of recent successful executions across all user's tasks.
    Only returns executions that produced a notification (condition met).
    """
    return await fetch_feed_executions(
        db, where_clause="t.user_id = $1", params=[user.id], limit=limit
    )


async def start_task_execution(
    task_id: str,
    task_name: str,
    user_id: str,
    db: Database,
    background_tasks: BackgroundTasks,
    suppress_notifications: bool = False,
    force: bool = False,
) -> dict:
    """HTTP-compatible adapter for manual execution orchestration."""
    try:
        return await _start_task_execution(
            task_id=task_id,
            task_name=task_name,
            user_id=user_id,
            db=db,
            background_tasks=background_tasks,
            suppress_notifications=suppress_notifications,
            force=force,
        )
    except ExecutionAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already running or pending. Use force=true to override.",
        ) from exc
    except ExecutionCreationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    """
    Get a task by ID for an authenticated user.

    - If user is authenticated and owns the task: full task details
    - If task is public: read-only access for authenticated non-owners
    - Otherwise: 404
    """
    repo = TaskRepository(db)
    row = await repo.find_by_id_with_execution(task_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permissions: owner has full access, others only if public
    is_owner = row["user_id"] == user.id
    is_public = row["is_public"]

    if not is_owner and not is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = parse_task_with_execution(row)

    if is_public and not is_owner:
        increment_view(task_id)
        task = task.model_copy(
            update={"notification_email": None, "webhook_url": None, "notifications": []}
        )

    return task


class VisibilityUpdateRequest(BaseModel):
    """Request to toggle task visibility."""

    is_public: bool = Field(..., description="Whether the task should be public")


class VisibilityUpdateResponse(BaseModel):
    """Response after updating visibility."""

    is_public: bool


@router.patch("/{task_id}/visibility", response_model=VisibilityUpdateResponse)
async def update_task_visibility(
    task_id: UUID,
    request: VisibilityUpdateRequest,
    user: CurrentUser,
    db: Database = Depends(get_db),
):
    """
    Toggle task visibility between public and private.
    """
    if not await TaskRepository(db).set_owned_visibility(task_id, user.id, request.is_public):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return VisibilityUpdateResponse(is_public=request.is_public)


class ForkTaskRequest(BaseModel):
    """Request to fork a public task."""

    name: str | None = Field(None, description="Optional new name for the forked task")


@router.post("/{task_id}/fork", response_model=Task)
async def fork_task(
    task_id: UUID,
    request: ForkTaskRequest,
    user: CurrentUser,
    db: Database = Depends(get_db),
):
    """
    Fork a public task. Creates a copy of the task configuration for the current user.

    - Task must be public to fork
    - Forked task starts in PAUSED state
    - Tracks original task via forked_from_task_id
    - User can optionally provide a new name
    """
    try:
        row = await TaskService(db).fork(task_id, user.id, request.name)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ForkNameConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Task(**parse_task_row(row))


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID, task_update: TaskUpdate, user: CurrentUser, db: Database = Depends(get_db)
):
    # First verify the task belongs to the user
    existing = await TaskRepository(db).find_owned(task_id, user.id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)

    if not update_data:
        return Task(**parse_task_row(existing))

    # Validate notifications if provided
    if "notifications" in update_data:
        # Get old webhook URL to check if it changed
        old_webhook_url = existing.get("webhook_url")

        # Validate and extract notification fields
        try:
            validated_notifications, extracted = await prepare_notifications(
                update_data["notifications"], old_webhook_url=old_webhook_url
            )
        except TaskNotificationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        update_data["notifications"] = validated_notifications
        update_data["notification_channels"] = extracted.notification_channels
        update_data["notification_email"] = extracted.notification_email
        update_data["webhook_url"] = extracted.webhook_url

        # Only update webhook_secret if it was generated (URL changed)
        if extracted.webhook_secret is not None:
            update_data["webhook_secret"] = extracted.webhook_secret

    # Build dynamic UPDATE query — track updated fields for rollback
    set_clauses = []
    params = []
    updated_fields = []  # Track field names for rollback on transition failure
    param_num = 1

    for field, value in update_data.items():
        # Skip state field - it's handled via TaskService below for scheduler sync
        if field == "state":
            continue

        if field == "notifications":
            set_clauses.append(f"{field} = ${param_num}")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{field} = ${param_num}")
            params.append(value)
        updated_fields.append(field)
        param_num += 1

    # If only state is being updated, set_clauses will be empty
    if set_clauses:
        params.append(task_id)
        params.append(user.id)

        query = f"""
            UPDATE tasks
            SET {", ".join(set_clauses)}
            WHERE id = ${param_num} AND user_id = ${param_num + 1}
            RETURNING *
        """

        row = await db.fetch_one(query, *params)
    else:
        # Only state (or nothing) changed, fetch the row to return
        row = existing

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update task",
        )

    # Handle state transitions if state changed
    if "state" in update_data and update_data["state"] != existing["state"]:
        current_state = TaskState(existing["state"])
        new_state = TaskState(update_data["state"])

        # Validate and execute transition using TaskService
        # This handles DB update + scheduler side effects (pause/resume/remove)
        try:
            task_service = TaskService(db=db)
            await task_service.transition(
                task_id=task_id,
                from_state=current_state,
                to_state=new_state,
                user_id=user.id,
                task_name=row["name"],
                next_run=datetime.now(UTC) + timedelta(minutes=1),
            )

            logger.info(
                f"Task {task_id} state transition: {current_state.value} → {new_state.value}"
            )

        except (InvalidTransitionError, Exception) as e:
            # Rollback ALL fields updated in Phase 1, not just state
            is_invalid = isinstance(e, InvalidTransitionError)
            logger.error(
                f"{'Invalid state transition' if is_invalid else 'Failed to transition task state'} "
                f"for task {task_id}: {str(e)}. Rolling back."
            )

            # Build dynamic rollback restoring all Phase 1 fields + state
            rollback_clauses = ["state = $1"]
            rollback_params: list = [existing["state"]]
            rp = 2
            for field in updated_fields:
                rollback_clauses.append(f"{field} = ${rp}")
                rollback_params.append(existing[field])
                rp += 1
            rollback_params.append(task_id)

            await db.execute(
                f"UPDATE tasks SET {', '.join(rollback_clauses)} WHERE id = ${rp}",
                *rollback_params,
            )

            if is_invalid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state transition: {str(e)}",
                ) from e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change task state: {str(e)}. Task update rolled back.",
            ) from e

    # Re-fetch to get the latest state (avoids returning stale data after transitions)
    repo = TaskRepository(db)
    fresh_row = await repo.find_by_id_with_execution(task_id)
    if not fresh_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return parse_task_with_execution(fresh_row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    # Delete from DB first (verifies ownership before touching scheduler)
    if not await TaskRepository(db).delete_owned(task_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Now safe to remove scheduler job — ownership verified by successful DELETE
    job_id = f"task-{task_id}"
    try:
        scheduler = get_scheduler()
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduler job {job_id}")
    except JobLookupError:
        logger.info(f"Job {job_id} not found when deleting - already removed or never existed")
    except Exception as e:
        # Task already deleted from DB; log but don't fail the request
        logger.error(f"Failed to remove scheduler job {job_id}: {e}", exc_info=True)

    return None


@router.post("/{task_id}/execute", response_model=TaskExecution)
async def execute_task(
    task_id: UUID,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
):
    """Execute a task manually (Run Now)."""
    # Verify task exists and belongs to user
    task = await TaskRepository(db).find_owned(task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Use helper to create execution and start workflow
    row = await start_task_execution(
        task_id=str(task_id),
        task_name=task["name"],
        user_id=str(user.id),
        db=db,
        background_tasks=background_tasks,
        suppress_notifications=False,
        force=True,  # User manual "Run Now" always overrides stuck executions
    )

    return TaskExecution(**parse_execution_row(row))


async def _fetch_task_executions(
    db: Database, task_id: UUID, user, limit: int, *, notifications_only: bool = False
) -> list[TaskExecution]:
    """Fetch task executions with access control. Optionally filter to notifications only."""
    _, is_owner = await _check_task_access(db, task_id, user)

    rows = await TaskExecutionRepository(db).find_recent(
        task_id, limit, notifications_only=notifications_only
    )

    executions = [TaskExecution(**parse_execution_row(row)) for row in rows]
    if not is_owner:
        for ex in executions:
            ex.error_message = None
    return executions


@router.get("/{task_id}/executions", response_model=list[TaskExecution])
async def get_task_executions(
    task_id: UUID, user: CurrentUser, limit: int = 100, db: Database = Depends(get_db)
):
    return await _fetch_task_executions(db, task_id, user, limit)


@router.get("/{task_id}/notifications", response_model=list[TaskExecution])
async def get_task_notifications(
    task_id: UUID, user: CurrentUser, limit: int = 100, db: Database = Depends(get_db)
):
    """
    Get task executions where the condition was met (notifications).
    This filters executions to only show when the monitoring condition triggered.
    """
    return await _fetch_task_executions(db, task_id, user, limit, notifications_only=True)
