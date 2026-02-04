"""Public task discovery and vanity URL routing."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

from torale.access import OptionalUser
from torale.api.rate_limiter import limiter
from torale.api.routers.tasks import get_task
from torale.api.utils.task_parsers import parse_task_with_execution
from torale.core.database import Database, get_db
from torale.tasks import Task

router = APIRouter(prefix="/public", tags=["public"])


class PublicTasksResponse(BaseModel):
    """Response for public tasks listing."""

    tasks: list[Task]
    total: int
    offset: int
    limit: int


@router.get("/tasks", response_model=PublicTasksResponse)
@limiter.limit("10/minute")
async def list_public_tasks(
    request: Request,
    user: OptionalUser,
    offset: int = Query(0, ge=0, description="Number of tasks to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of tasks to return"),
    sort_by: str = Query("recent", enum=["recent", "popular"], description="Sort order"),
    db: Database = Depends(get_db),
):
    """
    Discover public tasks (NO AUTH REQUIRED).

    Sort options:
    - recent: Most recently created tasks
    - popular: Most viewed tasks
    """
    # Get total count
    count_query = """
        SELECT COUNT(*) as total
        FROM tasks
        WHERE is_public = true
    """
    count_row = await db.fetch_one(count_query)
    total = count_row["total"] if count_row else 0

    # Build query with dynamic ORDER BY clause (validated by FastAPI enum)
    # Use dictionary mapping to prevent any possibility of SQL injection
    order_clauses = {
        "popular": "ORDER BY t.view_count DESC, t.created_at DESC",
        "recent": "ORDER BY t.created_at DESC",
    }
    order_clause = order_clauses[sort_by]

    tasks_query = f"""
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
        WHERE t.is_public = true
        {order_clause}
        LIMIT $1 OFFSET $2
    """

    rows = await db.fetch_all(tasks_query, limit, offset)

    # Parse tasks using shared utility
    tasks = [parse_task_with_execution(row) for row in rows]

    # Scrub sensitive fields for public viewers (non-owners)
    scrubbed_tasks = []
    for task in tasks:
        is_owner = user is not None and task.user_id == user.id
        if not is_owner:
            task = task.model_copy(
                update={"notification_email": None, "webhook_url": None, "notifications": []}
            )
        scrubbed_tasks.append(task)

    return PublicTasksResponse(
        tasks=scrubbed_tasks,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/tasks/{username}/{slug}", response_model=Task)
@limiter.limit("20/minute")
async def get_public_task_by_vanity_url(
    request: Request,
    username: str,
    slug: str,
    user: OptionalUser,
    db: Database = Depends(get_db),
):
    """
    Get a task by vanity URL: username/slug (NO AUTH REQUIRED).

    This endpoint allows accessing tasks via pretty URLs like:
    /public/tasks/alice/iphone-release-tracker
    """
    # Find user by username
    user_query = "SELECT id FROM users WHERE username = $1"
    user_row = await db.fetch_one(user_query, username.lower())

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Find task by slug and user_id
    task_query = """
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
        WHERE t.user_id = $1 AND t.slug = $2
    """

    row = await db.fetch_one(task_query, user_row["id"], slug.lower())

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permissions: owner has full access, others only if public
    is_owner = user is not None and row["user_id"] == user.id
    is_public = row["is_public"]

    if not is_public and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # TODO: Implement async view counting
    # Synchronous UPDATE on every read causes write amplification and contention
    # Move to Redis counter + async sync, or use dedicated analytics table
    # if is_public and not is_owner:
    #     await db.execute(
    #         "UPDATE tasks SET view_count = view_count + 1 WHERE id = $1",
    #         row["id"],
    #     )

    task = parse_task_with_execution(row)

    # Scrub sensitive fields for public viewers
    if is_public and not is_owner:
        task = task.model_copy(
            update={"notification_email": None, "webhook_url": None, "notifications": []}
        )

    return task


@router.get("/tasks/id/{task_id}", response_model=Task)
@limiter.limit("20/minute")
async def get_public_task_by_id(
    request: Request,
    task_id: UUID,
    user: OptionalUser,
    db: Database = Depends(get_db),
):
    """
    Get a public task by UUID (NO AUTH REQUIRED).

    This is a fallback for sharing direct task IDs instead of vanity URLs.
    """
    # This is identical to GET /api/v1/tasks/{task_id} but under /public prefix
    # Delegate to the existing endpoint logic (imported at top of file)
    return await get_task(task_id, user, db)
