import json
import logging
import secrets
from uuid import UUID

import grpc
from fastapi import APIRouter, Depends, HTTPException, status
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec
from temporalio.service import RPCError

from torale.api.auth import CurrentUserOrTestUser
from torale.core.config import settings
from torale.core.database import Database, get_db
from torale.core.models import Task, TaskCreate, TaskExecution, TaskUpdate
from torale.notifications import NotificationValidationError, validate_notification
from torale.workers.workflows import TaskExecutionRequest, TaskExecutionWorkflow

logger = logging.getLogger(__name__)

# Use CurrentUserOrTestUser for all endpoints to support TORALE_NOAUTH testing mode
# This is safe since all operations are user-scoped anyway
CurrentUser = CurrentUserOrTestUser

router = APIRouter(prefix="/tasks", tags=["tasks"])


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

    # Validate no duplicate notification types (PR #27 schema supports 1 email + 1 webhook max)
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

    extracted = {
        "notification_channels": notification_channels,
        "notification_email": notification_email,
        "webhook_url": webhook_url,
        "webhook_secret": webhook_secret,
    }

    return validated_notifications, extracted


def parse_task_row(row) -> dict:
    """Parse a task row from the database, converting JSON strings to dicts"""
    task_dict = dict(row)
    # Parse config if it's a string
    if isinstance(task_dict.get("config"), str):
        task_dict["config"] = json.loads(task_dict["config"])
    # Parse last_known_state if it's a string
    if isinstance(task_dict.get("last_known_state"), str):
        task_dict["last_known_state"] = (
            json.loads(task_dict["last_known_state"]) if task_dict["last_known_state"] else None
        )
    # Parse notifications if it's a string
    if isinstance(task_dict.get("notifications"), str):
        task_dict["notifications"] = (
            json.loads(task_dict["notifications"]) if task_dict["notifications"] else []
        )
    return task_dict


async def get_temporal_client() -> Client:
    """Get a Temporal client with proper authentication for Temporal Cloud or local dev."""
    if settings.temporal_api_key:
        return await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
            tls=True,
            api_key=settings.temporal_api_key,
        )
    else:
        return await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )


def parse_execution_row(row) -> dict:
    """Parse an execution row from the database, converting JSON strings to dicts"""
    exec_dict = dict(row)
    # Parse result if it's a string
    if isinstance(exec_dict.get("result"), str):
        exec_dict["result"] = json.loads(exec_dict["result"]) if exec_dict["result"] else None
    # Parse grounding_sources if it's a string
    if isinstance(exec_dict.get("grounding_sources"), str):
        exec_dict["grounding_sources"] = (
            json.loads(exec_dict["grounding_sources"]) if exec_dict["grounding_sources"] else None
        )
    return exec_dict


@router.post("/", response_model=Task)
async def create_task(task: TaskCreate, user: CurrentUser, db: Database = Depends(get_db)):
    # Validate notifications and extract fields for database
    validated_notifications, extracted = await _validate_and_extract_notifications(
        task.notifications
    )

    # Create task in database, populating BOTH schema approaches for compatibility
    query = """
        INSERT INTO tasks (
            user_id, name, schedule, executor_type, config, is_active,
            search_query, condition_description, notify_behavior, notifications,
            notification_channels, notification_email, webhook_url, webhook_secret
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        RETURNING *
    """

    row = await db.fetch_one(
        query,
        user.id,
        task.name,
        task.schedule,
        task.executor_type,
        json.dumps(task.config),
        task.is_active,
        task.search_query,
        task.condition_description,
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

    # Create Temporal schedule for automatic execution
    if task.is_active:
        try:
            client = await get_temporal_client()
            schedule_id = f"schedule-{task_id}"
            logger.info(f"Creating Temporal schedule {schedule_id} for task {task_id}")
            await client.create_schedule(
                id=schedule_id,
                schedule=Schedule(
                    action=ScheduleActionStartWorkflow(
                        TaskExecutionWorkflow.run,
                        TaskExecutionRequest(
                            task_id=task_id,
                            execution_id="",  # Will be generated by workflow
                            user_id=str(user.id),
                            task_name=task.name,
                        ),
                        id=f"scheduled-task-{task_id}",
                        task_queue="torale-tasks",
                    ),
                    spec=ScheduleSpec(cron_expressions=[task.schedule]),
                ),
            )
            logger.info(f"Successfully created Temporal schedule {schedule_id}")
        except Exception as e:
            # If schedule creation fails, delete the task and raise error
            logger.error(f"Failed to create schedule {schedule_id}: {str(e)}")
            await db.execute("DELETE FROM tasks WHERE id = $1", row["id"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {str(e)}",
            ) from e

    return Task(**parse_task_row(row))


@router.get("/", response_model=list[Task])
async def list_tasks(
    user: CurrentUser, is_active: bool | None = None, db: Database = Depends(get_db)
):
    if is_active is not None:
        query = """
            SELECT *
            FROM tasks
            WHERE user_id = $1 AND is_active = $2
            ORDER BY created_at DESC
        """
        rows = await db.fetch_all(query, user.id, is_active)
    else:
        query = """
            SELECT *
            FROM tasks
            WHERE user_id = $1
            ORDER BY created_at DESC
        """
        rows = await db.fetch_all(query, user.id)

    return [Task(**parse_task_row(row)) for row in rows]


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
    query = """
        SELECT *
        FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    row = await db.fetch_one(query, task_id, user.id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return Task(**parse_task_row(row))


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

    # Build dynamic UPDATE query
    set_clauses = []
    params = []
    param_num = 1

    for field, value in update_data.items():
        if field == "config":
            set_clauses.append(f"{field} = ${param_num}")
            params.append(json.dumps(value))
        elif field == "notifications":
            set_clauses.append(f"{field} = ${param_num}")
            params.append(json.dumps(value))
        elif field == "notify_behavior":
            # Convert enum to string value
            set_clauses.append(f"{field} = ${param_num}")
            params.append(value.value if hasattr(value, "value") else value)
        else:
            set_clauses.append(f"{field} = ${param_num}")
            params.append(value)
        param_num += 1

    params.append(task_id)
    params.append(user.id)

    query = f"""
        UPDATE tasks
        SET {", ".join(set_clauses)}
        WHERE id = ${param_num} AND user_id = ${param_num + 1}
        RETURNING *
    """

    row = await db.fetch_one(query, *params)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update task",
        )

    # Handle schedule pause/unpause if is_active changed
    if "is_active" in update_data and update_data["is_active"] != existing["is_active"]:
        client = await get_temporal_client()
        schedule_id = f"schedule-{task_id}"

        try:
            schedule_handle = client.get_schedule_handle(schedule_id)

            if update_data["is_active"]:
                # Unpause the schedule
                logger.info(f"Unpausing Temporal schedule {schedule_id}")
                await schedule_handle.unpause()
                logger.info(f"Successfully unpaused schedule {schedule_id}")
            else:
                # Pause the schedule
                logger.info(f"Pausing Temporal schedule {schedule_id}")
                await schedule_handle.pause()
                logger.info(f"Successfully paused schedule {schedule_id}")
        except RPCError as e:
            if e.status == grpc.StatusCode.NOT_FOUND:
                if update_data["is_active"]:
                    # Schedule doesn't exist, create it
                    logger.info(f"Schedule {schedule_id} not found, creating new schedule")
                    try:
                        await client.create_schedule(
                            id=schedule_id,
                            schedule=Schedule(
                                action=ScheduleActionStartWorkflow(
                                    TaskExecutionWorkflow.run,
                                    TaskExecutionRequest(
                                        task_id=str(task_id),
                                        execution_id="",
                                        user_id=str(user.id),
                                        task_name=row["name"],
                                    ),
                                    id=f"scheduled-task-{task_id}",
                                    task_queue="torale-tasks",
                                ),
                                spec=ScheduleSpec(cron_expressions=[row["schedule"]]),
                            ),
                        )
                        logger.info(f"Successfully created schedule {schedule_id}")
                    except Exception as create_error:
                        # Failed to create schedule - rollback task update
                        logger.error(
                            f"Failed to create schedule {schedule_id}: {str(create_error)}"
                        )
                        await db.execute(
                            "UPDATE tasks SET is_active = $1 WHERE id = $2",
                            existing["is_active"],
                            task_id,
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to create schedule: {str(create_error)}. Task update rolled back.",
                        ) from create_error
                else:
                    # Deactivating task but schedule doesn't exist - that's fine
                    logger.info(
                        f"Schedule {schedule_id} not found when deactivating task - already deleted"
                    )
            else:
                # Real RPC error (not "not found") - rollback the task update
                logger.error(
                    f"Failed to {'unpause' if update_data['is_active'] else 'pause'} schedule {schedule_id}: {str(e)}"
                )
                await db.execute(
                    "UPDATE tasks SET is_active = $1 WHERE id = $2",
                    existing["is_active"],
                    task_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to {'unpause' if update_data['is_active'] else 'pause'} schedule: {str(e)}. Task update rolled back.",
                ) from e
        except Exception as e:
            # Other unexpected error - rollback the task update
            logger.error(
                f"Unexpected error when trying to {'unpause' if update_data['is_active'] else 'pause'} schedule {schedule_id}: {str(e)}"
            )
            await db.execute(
                "UPDATE tasks SET is_active = $1 WHERE id = $2",
                existing["is_active"],
                task_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to {'unpause' if update_data['is_active'] else 'pause'} schedule: {str(e)}. Task update rolled back.",
            ) from e

    return Task(**parse_task_row(row))


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

    # Delete Temporal schedule first (if it exists)
    schedule_deleted = False
    schedule_error = None
    schedule_id = f"schedule-{task_id}"

    try:
        client = await get_temporal_client()
        schedule_handle = client.get_schedule_handle(schedule_id)
        logger.info(f"Deleting Temporal schedule {schedule_id} for task {task_id}")
        await schedule_handle.delete()
        schedule_deleted = True
        logger.info(f"Successfully deleted schedule {schedule_id}")
    except RPCError as e:
        if e.status == grpc.StatusCode.NOT_FOUND:
            logger.info(f"Schedule {schedule_id} not found - already deleted or never existed")
            schedule_deleted = True  # Schedule doesn't exist, safe to proceed
        else:
            logger.error(f"Failed to delete schedule {schedule_id}: {str(e)}")
            schedule_error = e
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error when deleting schedule {schedule_id}: {str(e)}")
        schedule_error = e

    # Only delete from database if schedule was successfully deleted or doesn't exist
    if not schedule_deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete Temporal schedule: {str(schedule_error)}. Task not deleted to prevent orphaned schedule.",
        ) from schedule_error

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
async def execute_task(task_id: UUID, user: CurrentUser, db: Database = Depends(get_db)):
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

    # Create execution record
    execution_query = """
        INSERT INTO task_executions (task_id, status)
        VALUES ($1, $2)
        RETURNING id, task_id, status, started_at, completed_at, result, error_message, created_at
    """

    row = await db.fetch_one(execution_query, task_id, "pending")

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create execution",
        )

    # Trigger Temporal workflow for actual execution
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            TaskExecutionWorkflow.run,
            TaskExecutionRequest(
                task_id=str(task_id),
                execution_id=str(row["id"]),
                user_id=str(user.id),
                task_name=task["name"],
            ),
            id=f"task-{task_id}-{row['id']}",
            task_queue="torale-tasks",
        )
    except Exception as e:
        # If workflow fails to start, update execution status
        await db.execute(
            "UPDATE task_executions SET status = $1, error_message = $2 WHERE id = $3",
            "failed",
            f"Failed to start workflow: {str(e)}",
            row["id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start task execution: {str(e)}",
        ) from e

    return TaskExecution(**parse_execution_row(row))


@router.get("/{task_id}/executions", response_model=list[TaskExecution])
async def get_task_executions(
    task_id: UUID, user: CurrentUser, limit: int = 100, db: Database = Depends(get_db)
):
    # Verify task belongs to user
    task_query = """
        SELECT id FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get executions
    executions_query = """
        SELECT *
        FROM task_executions
        WHERE task_id = $1
        ORDER BY started_at DESC
        LIMIT $2
    """

    rows = await db.fetch_all(executions_query, task_id, limit)

    return [TaskExecution(**parse_execution_row(row)) for row in rows]


@router.get("/{task_id}/notifications", response_model=list[TaskExecution])
async def get_task_notifications(
    task_id: UUID, user: CurrentUser, limit: int = 100, db: Database = Depends(get_db)
):
    """
    Get task executions where the condition was met (notifications).
    This filters executions to only show when the monitoring condition triggered.
    """
    # Verify task belongs to user
    task_query = """
        SELECT id FROM tasks
        WHERE id = $1 AND user_id = $2
    """

    task = await db.fetch_one(task_query, task_id, user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Get executions where condition_met is true
    notifications_query = """
        SELECT *
        FROM task_executions
        WHERE task_id = $1 AND condition_met = true
        ORDER BY started_at DESC
        LIMIT $2
    """

    rows = await db.fetch_all(notifications_query, task_id, limit)

    return [TaskExecution(**parse_execution_row(row)) for row in rows]
