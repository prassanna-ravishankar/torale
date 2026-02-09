import json
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from apscheduler.jobstores.base import JobLookupError
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from torale.access import CurrentUser, OptionalUser
from torale.api.utils.task_parsers import (
    parse_execution_row,
    parse_task_row,
    parse_task_with_execution,
)
from torale.core.database import Database, get_db
from torale.notifications import NotificationValidationError, validate_notification
from torale.scheduler.job import execute_task_job_manual
from torale.scheduler.scheduler import get_scheduler
from torale.tasks import (
    Task,
    TaskCreate,
    TaskExecution,
    TaskState,
    TaskUpdate,
)
from torale.tasks.service import InvalidTransitionError, TaskService
from torale.utils.slug import generate_unique_slug

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_TASK_WITH_EXECUTION_QUERY = """
    SELECT t.*,
           u.username as creator_username,
           e.id as exec_id,
           e.notification as exec_notification,
           e.started_at as exec_started_at,
           e.completed_at as exec_completed_at,
           e.status as exec_status,
           e.result as exec_result,
           e.grounding_sources as exec_grounding_sources
    FROM tasks t
    INNER JOIN users u ON t.user_id = u.id
    LEFT JOIN task_executions e ON t.last_execution_id = e.id
"""


async def _check_task_access(db: Database, task_id: UUID, user) -> dict:
    """Verify task exists and user has access (owner or public). Returns task row."""
    row = await db.fetch_one("SELECT * FROM tasks WHERE id = $1", task_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    is_owner = user is not None and row["user_id"] == user.id
    if not is_owner and not row["is_public"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return dict(row)


async def _validate_and_extract_notifications(
    notifications: list,
    old_webhook_url: str | None = None,
) -> tuple[list[dict], dict[str, any]]:
    """
    Validate notifications and extract fields for database storage.

    Args:
        notifications: List of notification dicts or Pydantic models
        old_webhook_url: Previous webhook URL (for updates). If provided and URL hasn't changed,
                        webhook_secret will be None to preserve existing secret.

    Returns:
        Tuple of (validated_notifications, extracted_fields) where extracted_fields contains:
        - notification_channels: list of channel types
        - notification_email: email address or None
        - webhook_url: webhook URL or None
        - webhook_secret: webhook secret or None (None means keep existing)

    Raises:
        HTTPException: If validation fails or duplicate types found
    """
    # Validate each notification
    validated_notifications = []
    for notif in notifications:
        # Convert to dict if it's a Pydantic model
        notif_dict = notif.model_dump() if hasattr(notif, "model_dump") else notif
        try:
            validated = await validate_notification(notif_dict)
            validated_notifications.append(validated)
        except NotificationValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid notification: {str(e)}"
            ) from e

    # Validate no duplicate notification types (supports 1 email + 1 webhook max)
    notification_types = [n.get("type") for n in validated_notifications]
    if len(notification_types) != len(set(notification_types)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Multiple notifications of the same type are not supported. Please provide at most one email and one webhook notification.",
        )

    # Extract notification channels and webhook config for database
    notification_channels = []
    notification_email = None
    webhook_url = None
    webhook_secret = None

    for notif in validated_notifications:
        notif_type = notif.get("type")
        if notif_type == "email":
            notification_channels.append("email")
            notification_email = notif.get("address")
        elif notif_type == "webhook":
            notification_channels.append("webhook")
            webhook_url = notif.get("url")
            # Only generate new secret if URL changed or it's a new webhook
            if old_webhook_url is None or old_webhook_url != webhook_url:
                webhook_secret = secrets.token_urlsafe(32)
            # else: webhook_secret stays None to preserve existing secret

    if not notification_channels:
        notification_channels = ["email"]

    extracted = {
        "notification_channels": notification_channels,
        "notification_email": notification_email,
        "webhook_url": webhook_url,
        "webhook_secret": webhook_secret,
    }

    return validated_notifications, extracted


@router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
    db: Database = Depends(get_db),
):
    # Validate notifications and extract fields for database
    validated_notifications, extracted = await _validate_and_extract_notifications(
        task.notifications
    )

    final_condition = task.condition_description or task.search_query
    initial_next_run = datetime.now(UTC) + timedelta(minutes=1)

    # Create task in database
    query = """
        INSERT INTO tasks (
            user_id, name, state, next_run,
            search_query, condition_description, notify_behavior, notifications,
            notification_channels, notification_email, webhook_url, webhook_secret
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
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
        task.notify_behavior,
        json.dumps(validated_notifications),
        extracted["notification_channels"],
        extracted["notification_email"],
        extracted["webhook_url"],
        extracted["webhook_secret"],
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
    base_query = _TASK_WITH_EXECUTION_QUERY + " WHERE t.user_id = $1"

    if state is not None:
        query = base_query + " AND t.state = $2 ORDER BY t.created_at DESC"
        rows = await db.fetch_all(query, user.id, state.value)
    else:
        query = base_query + " ORDER BY t.created_at DESC"
        rows = await db.fetch_all(query, user.id)

    return [parse_task_with_execution(row) for row in rows]


async def _safe_execute_task_job_manual(
    task_id: str,
    execution_id: str,
    user_id: str,
    task_name: str,
    suppress_notifications: bool = False,
    retry_count: int = 0,
) -> None:
    """Wrapper to ensure background task errors are logged.

    FastAPI's BackgroundTasks silently swallows exceptions, so we need
    explicit logging to maintain visibility into failures.
    """
    try:
        await execute_task_job_manual(
            task_id=task_id,
            execution_id=execution_id,
            user_id=user_id,
            task_name=task_name,
            suppress_notifications=suppress_notifications,
            retry_count=retry_count,
        )
    except Exception as exc:
        logger.error(
            f"Background task execution failed for task {task_id}, execution {execution_id}: {exc}",
            exc_info=True,
        )


async def start_task_execution(
    task_id: str,
    task_name: str,
    user_id: str,
    db: Database,
    background_tasks: BackgroundTasks,
    suppress_notifications: bool = False,
) -> dict:
    """Create execution record and launch agent-based execution in background."""
    from torale.scheduler.scheduler import get_scheduler

    # Check for running or pending executions to prevent concurrent execution
    running_execution = await db.fetch_one(
        "SELECT id FROM task_executions WHERE task_id = $1 AND status IN ('running', 'pending')",
        UUID(task_id),
    )

    if running_execution:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task is already running. Wait for current execution to complete.",
        )

    # Cancel any pending retry jobs before starting manual execution
    scheduler = get_scheduler()
    job_id = f"task-{task_id}"
    existing_job = scheduler.get_job(job_id)
    if existing_job:
        scheduler.remove_job(job_id)
        logger.info(f"Cancelled pending retry job for task {task_id} (manual run triggered)")

    # Inherit retry count from last execution (if it exists)
    last_execution = await db.fetch_one(
        """SELECT retry_count FROM task_executions
           WHERE task_id = $1
           ORDER BY started_at DESC LIMIT 1""",
        UUID(task_id),
    )
    retry_count = last_execution["retry_count"] if last_execution else 0

    execution_query = """
        INSERT INTO task_executions (task_id, status)
        VALUES ($1, $2)
        RETURNING id, task_id, status, started_at, completed_at, result, error_message, created_at
    """

    execution_row = await db.fetch_one(execution_query, UUID(task_id), "pending")

    if not execution_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create execution record",
        )

    background_tasks.add_task(
        _safe_execute_task_job_manual,
        task_id=task_id,
        execution_id=str(execution_row["id"]),
        user_id=user_id,
        task_name=task_name,
        suppress_notifications=suppress_notifications,
        retry_count=retry_count,
    )
    logger.info(
        f"Started execution {execution_row['id']} for task {task_id} (retry_count={retry_count})"
    )

    return dict(execution_row)


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: OptionalUser, db: Database = Depends(get_db)):
    """
    Get a task by ID. Supports both authenticated and unauthenticated access.

    - If user is authenticated and owns the task: full task details
    - If task is public: read-only access for anyone
    - Otherwise: 404
    """
    query = _TASK_WITH_EXECUTION_QUERY + " WHERE t.id = $1"
    row = await db.fetch_one(query, task_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permissions: owner has full access, others only if public
    is_owner = user is not None and row["user_id"] == user.id
    is_public = row["is_public"]

    if not is_owner and not is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    task = parse_task_with_execution(row)

    # TODO: Implement async view counting (see public_tasks.py)
    if is_public and not is_owner:
        # await db.execute(
        #     "UPDATE tasks SET view_count = view_count + 1 WHERE id = $1",
        #     task_id,
        # )
        # Scrub sensitive fields for public viewers
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
    slug: str | None = None


@router.patch("/{task_id}/visibility", response_model=VisibilityUpdateResponse)
async def update_task_visibility(
    task_id: UUID,
    request: VisibilityUpdateRequest,
    user: CurrentUser,
    db: Database = Depends(get_db),
):
    """
    Toggle task visibility between public and private.

    When making a task public:
    - User must have a username set
    - A slug will be auto-generated from the task name if not already set
    """
    # Verify task belongs to user
    task_query = """
        SELECT id, name, slug, is_public
        FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # If making public, check user has username
    if request.is_public:
        user_query = "SELECT username FROM users WHERE id = $1"
        user_row = await db.fetch_one(user_query, user.id)

        if not user_row or not user_row["username"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must set a username before making tasks public",
            )

        # Generate slug if not already set
        slug = task["slug"]
        if not slug:
            # Retry loop to handle race condition on slug uniqueness
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    slug = await generate_unique_slug(task["name"], user.id, db)
                    # Update both is_public and slug
                    await db.execute(
                        "UPDATE tasks SET is_public = $1, slug = $2 WHERE id = $3",
                        request.is_public,
                        slug,
                        task_id,
                    )
                    break  # Success, exit retry loop
                except UniqueViolationError as e:
                    # Slug collision - retry with new slug
                    if attempt < max_retries - 1:
                        logger.warning(f"Slug collision on attempt {attempt + 1}, retrying...")
                        continue
                    # Out of retries
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to generate unique slug after multiple attempts",
                    ) from e
                except Exception:
                    # Other database errors - don't retry
                    raise
        else:
            # Update only is_public
            await db.execute(
                "UPDATE tasks SET is_public = $1 WHERE id = $2",
                request.is_public,
                task_id,
            )

        return VisibilityUpdateResponse(is_public=True, slug=slug)

    # Making private - just update is_public
    await db.execute(
        "UPDATE tasks SET is_public = $1 WHERE id = $2",
        request.is_public,
        task_id,
    )

    return VisibilityUpdateResponse(is_public=False)


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
    # Verify access and get the full source task in one query
    source = await _check_task_access(db, task_id, user)

    is_owner = source["user_id"] == user.id

    # Determine base name and notification fields (scrub sensitive data for non-owners)
    base_fork_name = request.name if request.name else f"{source['name']} (Copy)"
    if is_owner:
        notifications = source["notifications"]
        notification_email = source["notification_email"]
        webhook_url = source["webhook_url"]
        webhook_secret = source["webhook_secret"]
        notification_channels = source["notification_channels"]
    else:
        notifications = json.dumps([])
        notification_email = None
        webhook_url = None
        webhook_secret = None
        notification_channels = []

    # Retry loop to handle race condition on task name uniqueness
    # Similar to slug generation logic - try up to 3 times with incremented counter
    max_retries = 3
    forked_row = None

    for attempt in range(max_retries):
        try:
            # Generate name with counter suffix if retry is needed
            if request.name:
                # User provided custom name - use it directly
                fork_name = base_fork_name
            else:
                # Auto-generated name - add counter on retry attempts
                fork_name = (
                    base_fork_name if attempt == 0 else f"{source['name']} (Copy {attempt + 1})"
                )

            # Wrap fork operations in transaction for atomicity
            # If either the subscriber count increment or task creation fails, both are rolled back
            async with db.acquire() as conn:
                async with conn.transaction():
                    # Increment subscriber count on original task only if forked by another user
                    if not is_owner:
                        await conn.execute(
                            "UPDATE tasks SET subscriber_count = subscriber_count + 1 WHERE id = $1",
                            task_id,
                        )

                    # Create forked task (in PAUSED state, not public, next_run=NULL)
                    fork_query = """
                        INSERT INTO tasks (
                            user_id, name, state,
                            search_query, condition_description, notify_behavior, notifications,
                            notification_channels, notification_email, webhook_url, webhook_secret,
                            forked_from_task_id, is_public
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        RETURNING *
                    """

                    forked_row = await conn.fetchrow(
                        fork_query,
                        user.id,
                        fork_name,
                        TaskState.PAUSED.value,
                        source["search_query"],
                        source["condition_description"],
                        source["notify_behavior"],
                        notifications,
                        notification_channels,
                        notification_email,
                        webhook_url,
                        webhook_secret,
                        task_id,
                        False,  # Forked tasks start as private
                    )

            # Success - break out of retry loop
            break

        except UniqueViolationError as e:
            # Name collision - retry with incremented counter
            if attempt < max_retries - 1:
                logger.warning(
                    f"Task name collision on attempt {attempt + 1}, retrying with incremented name..."
                )
                continue
            # Out of retries
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Failed to generate unique task name after multiple attempts. Please provide a custom name.",
            ) from e
        except Exception:
            # Other database errors - don't retry
            raise

    if not forked_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to fork task",
        )

    return Task(**parse_task_row(forked_row))


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: UUID, task_update: TaskUpdate, user: CurrentUser, db: Database = Depends(get_db)
):
    # First verify the task belongs to the user
    existing_query = """
        SELECT *
        FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    existing = await db.fetch_one(existing_query, task_id, user.id)

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
        validated_notifications, extracted = await _validate_and_extract_notifications(
            update_data["notifications"], old_webhook_url=old_webhook_url
        )

        update_data["notifications"] = validated_notifications
        update_data["notification_channels"] = extracted["notification_channels"]
        update_data["notification_email"] = extracted["notification_email"]
        update_data["webhook_url"] = extracted["webhook_url"]

        # Only update webhook_secret if it was generated (URL changed)
        if extracted["webhook_secret"] is not None:
            update_data["webhook_secret"] = extracted["webhook_secret"]

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
        elif field == "notify_behavior":
            # Convert enum to string value
            set_clauses.append(f"{field} = ${param_num}")
            params.append(value.value if hasattr(value, "value") else value)
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
    fresh_row = await db.fetch_one(_TASK_WITH_EXECUTION_QUERY + " WHERE t.id = $1", task_id)
    if not fresh_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return parse_task_with_execution(fresh_row)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    # Verify task exists and belongs to user first
    verify_query = """
        SELECT id FROM tasks
        WHERE id = $1 AND user_id = $2
    """
    task = await db.fetch_one(verify_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Remove APScheduler job (if it exists)
    job_id = f"task-{task_id}"
    try:
        scheduler = get_scheduler()
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduler job {job_id}")
    except JobLookupError:
        logger.info(f"Job {job_id} not found when deleting - already removed or never existed")
    except Exception as e:
        logger.error(f"Failed to remove scheduler job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove scheduler job: {str(e)}",
        ) from e

    # Delete task from database
    query = """
        DELETE FROM tasks
        WHERE id = $1 AND user_id = $2
        RETURNING id
    """

    row = await db.fetch_one(query, task_id, user.id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

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
    task_query = """
        SELECT id, name FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

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
    )

    return TaskExecution(**parse_execution_row(row))


@router.get("/{task_id}/executions", response_model=list[TaskExecution])
async def get_task_executions(
    task_id: UUID, user: OptionalUser, limit: int = 100, db: Database = Depends(get_db)
):
    await _check_task_access(db, task_id, user)

    # Get executions (exclude internal_error and other sensitive fields)
    executions_query = """
        SELECT id, task_id, status, started_at, completed_at,
               result, error_message, notification, grounding_sources,
               created_at
        FROM task_executions
        WHERE task_id = $1
        ORDER BY started_at DESC
        LIMIT $2
    """

    rows = await db.fetch_all(executions_query, task_id, limit)

    return [TaskExecution(**parse_execution_row(row)) for row in rows]


@router.get("/{task_id}/notifications", response_model=list[TaskExecution])
async def get_task_notifications(
    task_id: UUID, user: OptionalUser, limit: int = 100, db: Database = Depends(get_db)
):
    """
    Get task executions where the condition was met (notifications).
    This filters executions to only show when the monitoring condition triggered.
    """
    await _check_task_access(db, task_id, user)

    # Get executions where notification was sent (exclude internal_error and other sensitive fields)
    notifications_query = """
        SELECT id, task_id, status, started_at, completed_at,
               result, error_message, notification, grounding_sources,
               created_at
        FROM task_executions
        WHERE task_id = $1 AND notification IS NOT NULL
        ORDER BY started_at DESC
        LIMIT $2
    """

    rows = await db.fetch_all(notifications_query, task_id, limit)

    return [TaskExecution(**parse_execution_row(row)) for row in rows]
