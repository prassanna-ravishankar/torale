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
from webwhen.tasks.notifications import TaskNotificationError
from webwhen.tasks.repository import TaskExecutionRepository, TaskRepository
from webwhen.tasks.service import (
    ActiveTaskLimitError,
    ForkNameConflictError,
    InvalidTransitionError,
    TaskNotFoundError,
    TaskPersistenceError,
    TaskScheduleError,
    TaskService,
    TaskTransitionError,
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
    try:
        row = await TaskService(db).create(
            task,
            user.id,
            settings.max_active_tasks_per_user,
            datetime.now(UTC) + timedelta(minutes=1),
        )
    except ActiveTaskLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except TaskPersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TaskNotificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TaskScheduleError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    task_id = str(row["id"])

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
    try:
        result = await TaskService(db).update(task_id, user.id, task_update)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found") from exc
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: {exc}",
        ) from exc
    except TaskPersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TaskNotificationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except TaskTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    if result.includes_execution:
        return parse_task_with_execution(result.row)
    return Task(**parse_task_row(result.row))


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
