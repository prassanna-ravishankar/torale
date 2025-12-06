import json
import logging
import secrets
from uuid import UUID

import grpc
from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from temporalio.client import Client
from temporalio.service import RPCError

from torale.api.auth import CurrentUserOrTestUser, OptionalUser
from torale.api.dependencies import get_genai_client
from torale.api.utils.task_parsers import (
    parse_execution_row,
    parse_task_row,
    parse_task_with_execution,
)
from torale.core.config import settings
from torale.core.database import Database, get_db
from torale.core.models import (
    InferredCondition,
    NotifyBehavior,
    Task,
    TaskCreate,
    TaskExecution,
    TaskExecutionRequest,
    TaskState,
    TaskUpdate,
)
from torale.core.task_state import TaskStateManager
from torale.core.task_state_machine import InvalidTransitionError, TaskStateMachine
from torale.notifications import NotificationValidationError, validate_notification
from torale.utils.slug import generate_unique_slug
from torale.workers.workflows import TaskExecutionWorkflow

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


@router.post("/", response_model=Task)
async def create_task(task: TaskCreate, user: CurrentUser, db: Database = Depends(get_db)):
    # Validate notifications and extract fields for database
    validated_notifications, extracted = await _validate_and_extract_notifications(
        task.notifications
    )

    # Create task in database
    query = """
        INSERT INTO tasks (
            user_id, name, schedule, executor_type, config, state,
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
        task.state.value,
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

    # Create Temporal schedule for automatic execution if task is active
    if task.state == TaskState.ACTIVE:
        try:
            state_manager = TaskStateManager(db_conn=db)
            # For new tasks, create the schedule directly (not a transition)
            await state_manager.set_task_active_state(
                task_id=UUID(task_id),
                is_active=True,
                task_name=task.name,
                user_id=user.id,
                schedule=task.schedule,
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
    if task.run_immediately:
        try:
            await _start_task_execution(
                task_id=task_id,
                task_name=task.name,
                user_id=str(user.id),
                db=db,
                suppress_notifications=False,  # First run should notify
            )
        except Exception as e:
            # Log error but don't fail task creation
            logger.error(f"Failed to start immediate execution for task {task_id}: {str(e)}")

    return Task(**parse_task_row(row))


@router.get("/", response_model=list[Task])
async def list_tasks(
    user: CurrentUser, state: TaskState | None = None, db: Database = Depends(get_db)
):
    # Embed latest execution via LEFT JOIN for efficient status calculation
    base_query = """
        SELECT t.*,
               e.id as exec_id,
               e.condition_met as exec_condition_met,
               e.started_at as exec_started_at,
               e.completed_at as exec_completed_at,
               e.status as exec_status,
               e.result as exec_result,
               e.change_summary as exec_change_summary,
               e.grounding_sources as exec_grounding_sources
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.user_id = $1
    """

    if state is not None:
        query = base_query + " AND t.state = $2 ORDER BY t.created_at DESC"
        rows = await db.fetch_all(query, user.id, state.value)
    else:
        query = base_query + " ORDER BY t.created_at DESC"
        rows = await db.fetch_all(query, user.id)

    return [parse_task_with_execution(row) for row in rows]


class PreviewSearchRequest(BaseModel):
    search_query: str = Field(..., description="The search query to test")
    condition_description: str | None = Field(None, description="Optional condition to evaluate")
    model: str = Field("gemini-2.0-flash-exp", description="Model to use for search")


class SuggestTaskRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description of the task")
    current_task: dict | None = Field(None, description="Current task configuration for context")
    model: str = Field("gemini-2.0-flash-exp", description="Model to use for suggestion")


class SuggestedTask(BaseModel):
    name: str = Field(description="Short, memorable name for the task (e.g., 'PS5 Stock Monitor')")
    search_query: str = Field(description="Google search query to monitor")
    condition_description: str = Field(
        description="Clear, 1-sentence description of what triggers a notification"
    )
    schedule: str = Field(description="Cron expression (e.g., '0 9 * * *' for daily at 9am)")
    notify_behavior: NotifyBehavior = Field(
        description="When to notify: 'always' (every run), 'once' (first time only), 'track_state' (on change)"
    )


@router.post("/suggest", response_model=SuggestedTask)
async def suggest_task(
    request: SuggestTaskRequest,
    user: CurrentUser,
    genai_client=Depends(get_genai_client),
):
    """
    Suggest task configuration from natural language description.
    """
    from google.genai import types

    # Use structured format with distinct roles to prevent prompt injection
    # System instructions are in the first user message, user input is separate
    if request.current_task:
        system_instruction = """You are an expert at configuring web monitoring tasks.

Based on the user's request, UPDATE the current task configuration.
- If the user says "add river facing", append it to the search query (e.g. "apartments in NY" -> "apartments in NY river facing").
- Keep existing context unless explicitly asked to change it.
- Return the FULL updated configuration.

JSON Response:"""

        contents = [
            {"role": "user", "parts": [{"text": system_instruction}]},
            {
                "role": "model",
                "parts": [
                    {
                        "text": "Understood. I will return a JSON object with the required fields based on your update request."
                    }
                ],
            },
            {
                "role": "user",
                "parts": [
                    {
                        "text": f'Current Task Configuration:\n{json.dumps(request.current_task, indent=2)}\n\nUser Request: "{request.prompt}"'
                    }
                ],
            },
        ]
    else:
        system_instruction = """You are an expert at configuring web monitoring tasks.

Based on the user's description, generate the optimal configuration for a monitoring task.

IMPORTANT for notify_behavior:
- If the user wants DAILY/WEEKLY/MONTHLY digests or summaries → use 'always' (notify every time)
- If the user wants recurring alerts (stock, price, availability) → use 'always'
- If the user wants ONE-TIME announcements (launch dates, event dates) → use 'once'

JSON Response:"""

        contents = [
            {"role": "user", "parts": [{"text": system_instruction}]},
            {
                "role": "model",
                "parts": [
                    {"text": "Understood. I will return a JSON object with the required fields."}
                ],
            },
            {"role": "user", "parts": [{"text": f'User Description: "{request.prompt}"'}]},
        ]

    try:
        response = await genai_client.aio.models.generate_content(
            model=request.model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SuggestedTask,
            ),
        )

        # Log the AI response for debugging
        suggestion = json.loads(response.text)
        logger.info(f"Task suggestion for '{request.prompt}': {json.dumps(suggestion, indent=2)}")

        return suggestion

    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse LLM JSON response for task suggestion: {response.text}", exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI suggestion. The format was invalid.",
        ) from e
    except Exception as e:
        logger.error(f"Failed to suggest task: {str(e)}", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate task suggestion. Please try again.",
        ) from e


@router.post("/preview")
async def preview_search(
    request: PreviewSearchRequest,
    user: CurrentUser,
    genai_client=Depends(get_genai_client),
):
    """
    Preview a search query without creating a task.

    This endpoint allows users to test their search query and see results before
    committing to creating a monitoring task. It executes the grounded search
    executor but doesn't save anything to the database.

    Args:
        search_query: The search query to test
        condition_description: Optional condition to evaluate (if not provided, LLM will infer)
        model: Model to use for search (default: gemini-2.0-flash-exp)

    Returns:
        {
            "answer": "The search result answer",
            "condition_met": bool,
            "inferred_condition": "LLM-inferred condition" (if condition_description not provided),
            "grounding_sources": [{url, title}, ...],
            "current_state": {...}
        }
    """
    from torale.executors.grounded_search import GroundedSearchExecutor

    try:
        executor = GroundedSearchExecutor()

        # If no condition provided, have LLM infer it from the query
        condition_description = request.condition_description
        inferred = not condition_description
        if not condition_description:
            try:
                condition_description = await _infer_condition_from_query(
                    request.search_query, request.model, genai_client
                )
            except Exception as e:
                logger.error(f"Failed to infer condition from query: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to automatically determine what to look for in the search. Please provide a specific condition description.",
                ) from e

        # Execute the search
        config = {
            "search_query": request.search_query,
            "condition_description": condition_description,
            "model": request.model,
        }

        result = await executor.execute(config)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Search execution failed"),
            )

        # Return results with inferred condition if applicable
        response = {
            "answer": result["answer"],
            "condition_met": result["condition_met"],
            "grounding_sources": result["grounding_sources"],
            "current_state": result["current_state"],
        }

        if inferred:
            response["inferred_condition"] = condition_description

        return response

    except HTTPException:
        # Re-raise HTTP exceptions from nested calls
        raise
    except ValueError as e:
        # Handle configuration/validation errors
        logger.error(f"Preview search validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search configuration: {str(e)}",
        ) from e
    except Exception as e:
        # Catch unexpected errors and log full traceback
        logger.exception(f"Unexpected error during preview search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during search preview. Please try again.",
        ) from e


async def _start_task_execution(
    task_id: str,
    task_name: str,
    user_id: str,
    db: Database,
    suppress_notifications: bool = False,
) -> dict:
    """
    Helper function to create execution record and start Temporal workflow.

    This centralizes the logic for starting task executions, used by both
    the create_task endpoint (when run_immediately=True) and the execute_task endpoint.

    Args:
        task_id: UUID of the task to execute
        task_name: Name of the task
        user_id: UUID of the user
        db: Database connection
        suppress_notifications: Whether to suppress notifications (preview mode)

    Returns:
        dict with execution record data

    Raises:
        HTTPException if execution creation or workflow start fails
    """
    # Create execution record
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

    # Start Temporal workflow
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            TaskExecutionWorkflow.run,
            TaskExecutionRequest(
                task_id=task_id,
                execution_id=str(execution_row["id"]),
                user_id=user_id,
                task_name=task_name,
                suppress_notifications=suppress_notifications,
            ),
            id=f"task-{task_id}-{execution_row['id']}",
            task_queue=settings.temporal_task_queue,
        )
        logger.info(f"Started execution {execution_row['id']} for task {task_id}")
    except Exception as e:
        # If workflow fails to start, update execution status
        await db.execute(
            "UPDATE task_executions SET status = $1, error_message = $2 WHERE id = $3",
            "failed",
            f"Failed to start workflow: {str(e)}",
            execution_row["id"],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start execution workflow: {str(e)}",
        ) from e

    return dict(execution_row)


async def _infer_condition_from_query(
    search_query: str,
    model: str,
    genai_client,
) -> str:
    """
    Use LLM to infer what the monitoring condition should be based on the search query.

    For example:
    - "When is iPhone 16 coming out?" → "A specific release date has been announced"
    - "Is GPT-5 available yet?" → "GPT-5 is officially available or released"

    Args:
        search_query: The user's search query
        model: Gemini model to use
        genai_client: Genai client instance (passed from parent endpoint)
    """
    from google.genai import types

    inference_prompt = f"""Based on this search query, infer what condition the user wants to monitor for.

Search Query: {search_query}

What condition or change would indicate this information is available or has been announced?

Examples:
- Query: "When is the next iPhone release?" → "A specific release date or month has been officially announced"
- Query: "Is GPT-5 available?" → "GPT-5 is officially released and available"
- Query: "What's the price of PS5?" → "A clear price is listed"
"""

    response = await genai_client.aio.models.generate_content(
        model=model,
        contents=inference_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InferredCondition,
        ),
    )

    result = json.loads(response.text)
    return result["condition"]


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: UUID, user: OptionalUser, db: Database = Depends(get_db)):
    """
    Get a task by ID. Supports both authenticated and unauthenticated access.

    - If user is authenticated and owns the task: full task details
    - If task is public: read-only access for anyone
    - Otherwise: 404
    """
    # Embed latest execution via LEFT JOIN
    query = """
        SELECT t.*,
               e.id as exec_id,
               e.condition_met as exec_condition_met,
               e.started_at as exec_started_at,
               e.completed_at as exec_completed_at,
               e.status as exec_status,
               e.result as exec_result,
               e.change_summary as exec_change_summary,
               e.grounding_sources as exec_grounding_sources
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.id = $1
    """

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

    # TODO: Implement async view counting (see public_tasks.py)
    # if is_public and not is_owner:
    #     await db.execute(
    #         "UPDATE tasks SET view_count = view_count + 1 WHERE id = $1",
    #         task_id,
    #     )

    return parse_task_with_execution(row)


class VisibilityUpdateRequest(BaseModel):
    """Request to toggle task visibility."""

    is_public: bool = Field(..., description="Whether the task should be public")


class VisibilityUpdateResponse(BaseModel):
    """Response after updating visibility."""

    is_public: bool
    slug: str | None = None
    username_required: bool = Field(
        False, description="True if user needs to set username before making task public"
    )


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
    # Get the source task
    source_query = """
        SELECT t.*
        FROM tasks t
        WHERE t.id = $1
    """

    source = await db.fetch_one(source_query, task_id)

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check if task is public or user owns it
    is_owner = source["user_id"] == user.id
    is_public = source["is_public"]

    if not is_public and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Allow owners to fork (duplicate) their own tasks
    # Frontend can show "Duplicate" for owners, "Fork" for others

    # Determine name for forked task
    fork_name = request.name if request.name else f"{source['name']} (Copy)"

    # Scrub sensitive fields when forking another user's task
    # Owner duplicating their own task can keep their settings
    if is_owner:
        # Keep all notification settings when duplicating own task
        notifications = source["notifications"]
        notification_email = source["notification_email"]
        webhook_url = source["webhook_url"]
        webhook_secret = source["webhook_secret"]
        notification_channels = source["notification_channels"]
    else:
        # Scrub sensitive fields when forking someone else's task
        notifications = "[]"  # Reset notifications list
        notification_email = None
        webhook_url = None
        webhook_secret = None
        notification_channels = []

    # Wrap fork operations in transaction for atomicity
    # If either the subscriber count increment or task creation fails, both are rolled back
    async with db.acquire() as conn:
        async with conn.transaction():
            # Increment subscriber count on original task
            await conn.execute(
                "UPDATE tasks SET subscriber_count = subscriber_count + 1 WHERE id = $1",
                task_id,
            )

            # Create forked task (in PAUSED state, not public)
            fork_query = """
                INSERT INTO tasks (
                    user_id, name, schedule, executor_type, config, state,
                    search_query, condition_description, notify_behavior, notifications,
                    notification_channels, notification_email, webhook_url, webhook_secret,
                    forked_from_task_id, is_public
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                RETURNING *
            """

            forked_row = await conn.fetchrow(
                fork_query,
                user.id,
                fork_name,
                source["schedule"],
                source["executor_type"],
                source["config"],
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

    # Handle state transitions if state changed
    if "state" in update_data and update_data["state"] != existing["state"]:
        state_machine = TaskStateMachine(db_conn=db)
        current_state = TaskState(existing["state"])
        new_state = TaskState(update_data["state"])

        try:
            await state_machine.transition(
                task_id=task_id,
                from_state=current_state,
                to_state=new_state,
                user_id=user.id,
                task_name=row["name"],
                schedule=row["schedule"],
            )

            logger.info(
                f"Task {task_id} state transition: {current_state.value} → {new_state.value}"
            )

        except InvalidTransitionError as e:
            # Invalid transition - rollback database
            logger.error(f"Invalid state transition for task {task_id}: {str(e)}. Rolling back.")
            await db.execute(
                "UPDATE tasks SET state = $1 WHERE id = $2",
                existing["state"],
                task_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid state transition: {str(e)}",
            ) from e
        except Exception as e:
            # Temporal operation failed - rollback database
            logger.error(f"Failed to transition task {task_id} state: {str(e)}. Rolling back.")
            await db.execute(
                "UPDATE tasks SET state = $1 WHERE id = $2",
                existing["state"],
                task_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change task state: {str(e)}. Task update rolled back.",
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
async def execute_task(
    task_id: UUID,
    user: CurrentUser,
    db: Database = Depends(get_db),
    suppress_notifications: bool = False,
):
    """
    Execute a task manually.

    Args:
        task_id: ID of the task to execute
        suppress_notifications: If True, don't send notifications (preview mode)

    This is used both for "Run Now" (preview) and scheduled executions.
    """
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
    row = await _start_task_execution(
        task_id=str(task_id),
        task_name=task["name"],
        user_id=str(user.id),
        db=db,
        suppress_notifications=suppress_notifications,
    )

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
