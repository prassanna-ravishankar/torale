"""Admin console API endpoints for platform management."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.access import ClerkUser, clerk_client, require_admin
from torale.api.routers.tasks import start_task_execution
from torale.core.config import settings
from torale.core.database import Database, get_db
from torale.core.database_alchemy import get_async_session
from torale.scheduler.scheduler import get_scheduler
from torale.tasks import TaskState
from torale.tasks.service import TaskService

router = APIRouter(prefix="/admin", tags=["admin"], include_in_schema=False)

logger = logging.getLogger(__name__)


# Request models for role management
class UpdateUserRoleRequest(BaseModel):
    """Request model for updating a single user's role."""

    role: Literal["admin", "developer"] | None = Field(
        ...,
        description="User role: 'admin', 'developer', or null to remove role",
    )


class BulkUpdateUserRolesRequest(BaseModel):
    """Request model for bulk updating user roles."""

    user_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Array of user IDs to update (max 100)",
    )
    role: Literal["admin", "developer"] | None = Field(
        ...,
        description="User role: 'admin', 'developer', or null to remove role",
    )


def parse_json_field(value: Any) -> Any:
    """Parse JSON field if it's a string, otherwise return as-is."""
    if isinstance(value, str):
        try:
            return json.loads(value) if value else None
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON field: {value!r:.200}")
            return value
    return value


@router.get("/stats")
async def get_platform_stats(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get platform-wide statistics for admin dashboard.

    Returns:
    - User capacity (total/used/available)
    - Task statistics (total/triggered/trigger_rate)
    - 24-hour execution metrics (total/failed/success_rate)
    - Popular queries (top 10 most common search queries)
    """
    # User capacity
    user_result = await session.execute(
        text("""
        SELECT COUNT(*) as total_users
        FROM users
        WHERE is_active = true
        """)
    )
    user_row = user_result.first()
    total_users = user_row[0] if user_row else 0

    # Get max users from settings (default 100)
    max_users = getattr(settings, "max_users", 100)

    # Task statistics
    task_result = await session.execute(
        text("""
        SELECT
            COUNT(*) as total_tasks,
            SUM(CASE WHEN e.notification IS NOT NULL THEN 1 ELSE 0 END) as triggered_tasks
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.state = 'active'
        """)
    )
    task_row = task_result.first()
    total_tasks = task_row[0] if task_row else 0
    triggered_tasks = task_row[1] if task_row and task_row[1] else 0
    trigger_rate = (triggered_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # 24-hour execution metrics
    twenty_four_hours_ago = datetime.now(UTC) - timedelta(hours=24)
    exec_result = await session.execute(
        text("""
        SELECT
            COUNT(*) as total_executions,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_executions
        FROM task_executions
        WHERE created_at >= :since
        """),
        {"since": twenty_four_hours_ago},
    )
    exec_row = exec_result.first()
    total_executions = exec_row[0] if exec_row else 0
    failed_executions = exec_row[1] if exec_row and exec_row[1] else 0
    success_rate = (
        (total_executions - failed_executions) / total_executions * 100
        if total_executions > 0
        else 100
    )

    # Popular queries (top 10)
    popular_result = await session.execute(
        text("""
        SELECT
            t.search_query,
            COUNT(*) as task_count,
            SUM(CASE WHEN e.notification IS NOT NULL THEN 1 ELSE 0 END) as triggered_count
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.search_query IS NOT NULL
        GROUP BY t.search_query
        ORDER BY task_count DESC
        LIMIT 10
        """)
    )
    popular_queries = [
        {
            "search_query": row[0],
            "count": row[1],
            "triggered_count": row[2] if row[2] else 0,
        }
        for row in popular_result
    ]

    return {
        "users": {
            "total": total_users,
            "capacity": max_users,
            "available": max_users - total_users,
        },
        "tasks": {
            "total": total_tasks,
            "triggered": triggered_tasks,
            "trigger_rate": f"{trigger_rate:.1f}%",
        },
        "executions_24h": {
            "total": total_executions,
            "failed": failed_executions,
            "success_rate": f"{success_rate:.1f}%",
        },
        "popular_queries": popular_queries,
    }


@router.get("/queries")
async def list_all_queries(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=100, le=500),
    active_only: bool = Query(default=False),
):
    """
    List all user queries with statistics.

    Query Parameters:
    - limit: Maximum number of results (default: 100, max: 500)
    - active_only: Only show active tasks (default: false)

    Returns array of tasks with:
    - User email
    - Task details (name, query, condition, next_run)
    - Execution statistics (count, trigger count, notification)
    """
    active_filter = "AND t.state = 'active'" if active_only else ""

    result = await session.execute(
        text(f"""
        SELECT
            t.id,
            t.name,
            t.search_query,
            t.condition_description,
            t.next_run,
            t.state,
            le.notification as last_notification,
            t.created_at,
            u.email as user_email,
            COUNT(te.id) as execution_count,
            SUM(CASE WHEN te.notification IS NOT NULL THEN 1 ELSE 0 END) as trigger_count,
            t.last_known_state,
            t.state_changed_at
        FROM tasks t
        JOIN users u ON u.id = t.user_id
        LEFT JOIN task_executions le ON t.last_execution_id = le.id
        LEFT JOIN task_executions te ON te.task_id = t.id
        WHERE 1=1 {active_filter}
        GROUP BY t.id, u.email, le.notification, t.last_known_state, t.state_changed_at
        ORDER BY t.created_at DESC
        LIMIT :limit
        """),
        {"limit": limit},
    )

    queries = [
        {
            "id": str(row[0]),
            "name": row[1],
            "search_query": row[2],
            "condition_description": row[3],
            "next_run": row[4].isoformat() if row[4] else None,
            "state": row[5],
            "has_notification": row[6] is not None,
            "created_at": row[7].isoformat() if row[7] else None,
            "user_email": row[8],
            "execution_count": row[9] if row[9] else 0,
            "trigger_count": row[10] if row[10] else 0,
            "last_known_state": row[11],
            "state_changed_at": row[12].isoformat() if row[12] else None,
        }
        for row in result
    ]

    return {"queries": queries, "total": len(queries)}


@router.get("/executions")
async def list_recent_executions(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, le=200),
    status_filter: str | None = Query(default=None, alias="status"),
    task_id: UUID | None = Query(default=None),
):
    """
    List task execution history across all users.

    Query Parameters:
    - limit: Maximum number of results (default: 50, max: 200)
    - status: Filter by status ('success', 'failed', 'running')
    - task_id: Filter by specific task ID

    Returns detailed execution results with:
    - Execution metadata (status, timestamps, duration)
    - Task and user information
    - Full results with Gemini answers
    - Grounding sources
    - Condition evaluation
    - Change summaries
    """
    status_clause = "AND te.status = :status_filter" if status_filter else ""
    task_clause = "AND te.task_id = :task_id" if task_id else ""

    params: dict[str, Any] = {"limit": limit}
    if status_filter:
        params["status_filter"] = status_filter
    if task_id:
        params["task_id"] = task_id

    result = await session.execute(
        text(f"""
        SELECT
            te.id,
            te.task_id,
            te.status,
            te.started_at,
            te.completed_at,
            te.result,
            te.error_message,
            te.notification,
            te.grounding_sources,
            t.search_query,
            u.email as user_email
        FROM task_executions te
        JOIN tasks t ON t.id = te.task_id
        JOIN users u ON u.id = t.user_id
        WHERE 1=1 {status_clause} {task_clause}
        ORDER BY te.started_at DESC
        LIMIT :limit
        """),
        params,
    )

    executions = [
        {
            "id": str(row[0]),
            "task_id": str(row[1]),
            "status": row[2],
            "started_at": row[3].isoformat() if row[3] else None,
            "completed_at": row[4].isoformat() if row[4] else None,
            "result": parse_json_field(row[5]),
            "error_message": row[6],
            "notification": row[7],
            "grounding_sources": parse_json_field(row[8]),
            "search_query": row[9],
            "user_email": row[10],
        }
        for row in result
    ]

    return {"executions": executions, "total": len(executions)}


@router.get("/scheduler/jobs")
async def list_scheduler_jobs(
    admin: ClerkUser = Depends(require_admin),
):
    """List all APScheduler jobs with their state."""
    scheduler = get_scheduler()
    jobs = []

    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "paused": job.next_run_time is None,
                "trigger": str(job.trigger),
            }
        )

    return {"jobs": jobs, "total": len(jobs)}


@router.get("/errors")
async def list_recent_errors(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(default=50, le=200),
):
    """
    List recent failed executions with error details.

    Query Parameters:
    - limit: Maximum number of results (default: 50, max: 200)

    Returns:
    - Failed execution details
    - Full error messages and stack traces
    - Associated user and task info
    - Timestamp of failure
    """
    result = await session.execute(
        text("""
        SELECT
            te.id,
            te.task_id,
            te.started_at,
            te.completed_at,
            te.error_message,
            t.search_query,
            t.name as task_name,
            u.email as user_email
        FROM task_executions te
        JOIN tasks t ON t.id = te.task_id
        JOIN users u ON u.id = t.user_id
        WHERE te.status = 'failed'
        ORDER BY te.started_at DESC
        LIMIT :limit
        """),
        {"limit": limit},
    )

    errors = [
        {
            "id": str(row[0]),
            "task_id": str(row[1]),
            "started_at": row[2].isoformat() if row[2] else None,
            "completed_at": row[3].isoformat() if row[3] else None,
            "error_message": row[4],
            "search_query": row[5],
            "task_name": row[6],
            "user_email": row[7],
        }
        for row in result
    ]

    return {"errors": errors, "total": len(errors)}


@router.get("/users")
async def list_users(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List all platform users with statistics and roles.

    Returns:
    - All user accounts with email and Clerk ID
    - User roles from Clerk publicMetadata
    - Signup date
    - Task count per user
    - Total execution count
    - Number of triggered conditions
    - Active/inactive status
    - Platform capacity info
    """
    result = await session.execute(
        text("""
        SELECT
            u.id,
            u.email,
            u.clerk_user_id,
            u.is_active,
            u.created_at,
            COUNT(DISTINCT t.id) as task_count,
            COUNT(te.id) as total_executions,
            SUM(CASE WHEN te.notification IS NOT NULL THEN 1 ELSE 0 END) as notifications_count
        FROM users u
        LEFT JOIN tasks t ON t.user_id = u.id
        LEFT JOIN task_executions te ON te.task_id = t.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """)
    )

    # Batch-fetch roles from Clerk to avoid N+1 query problem
    # Handle pagination to ensure we fetch all users
    role_map = {}
    clerk_warnings: list[str] = []
    if clerk_client:
        try:
            # Clerk's default limit is 10, max is 500. Use higher limit for efficiency.
            limit = 500
            offset = 0

            while True:
                clerk_users_response = await clerk_client.users.list_async(
                    limit=limit, offset=offset
                )

                if not clerk_users_response or not clerk_users_response.data:
                    break

                # Add users from this page to role_map
                for user in clerk_users_response.data:
                    role_map[user.id] = (user.public_metadata or {}).get("role")

                # Check if we've fetched all users (last page)
                if len(clerk_users_response.data) < limit:
                    break

                offset += limit

        except Exception as e:
            logger.error(f"Failed to batch-fetch users from Clerk: {e}")
            clerk_warnings.append(f"Clerk role fetch failed: {e}. Roles may be incomplete.")

    users = []
    for row in result:
        user_data = {
            "id": str(row[0]),
            "email": row[1],
            "clerk_user_id": row[2],
            "is_active": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "task_count": row[5] if row[5] else 0,
            "total_executions": row[6] if row[6] else 0,
            "notifications_count": row[7] if row[7] else 0,
            "role": role_map.get(row[2]),  # Get role from pre-fetched map
        }

        users.append(user_data)

    # Get capacity info
    active_users = sum(1 for u in users if u["is_active"])
    max_users = getattr(settings, "max_users", 100)

    response = {
        "users": users,
        "capacity": {
            "used": active_users,
            "total": max_users,
            "available": max_users - active_users,
        },
    }
    if clerk_warnings:
        response["warnings"] = clerk_warnings
    return response


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    db: Database = Depends(get_db),
):
    """
    Manually deactivate a user account.

    This sets user.is_active = false and pauses all their active tasks via state machine.
    Frees up a seat in the capacity limit.

    Path Parameters:
    - user_id: UUID of the user to deactivate

    Returns:
    - Status confirmation with count of tasks paused
    """
    # Check if user exists
    check_result = await session.execute(
        text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}
    )
    if not check_result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Fetch all active tasks for this user
    tasks_result = await session.execute(
        text("SELECT id, state FROM tasks WHERE user_id = :user_id AND state = 'active'"),
        {"user_id": user_id},
    )
    active_tasks = [(row[0], row[1]) for row in tasks_result]

    # Pause each active task via TaskService
    task_service = TaskService(db=db)
    paused_count = 0
    failed_tasks = []

    for task_id, state in active_tasks:
        try:
            current_state = TaskState(state)
            await task_service.pause(task_id=task_id, current_state=current_state)
            paused_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": str(task_id), "error": str(e)})

    # Deactivate user
    try:
        await session.execute(
            text("UPDATE users SET is_active = false, updated_at = NOW() WHERE id = :user_id"),
            {"user_id": user_id},
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        ) from e

    return {
        "status": "deactivated",
        "user_id": str(user_id),
        "tasks_paused": paused_count,
        "tasks_failed": failed_tasks if failed_tasks else None,
    }


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update a user's role in Clerk publicMetadata.

    Admins can assign roles: "admin", "developer", or null (remove role).

    Safeguards:
    - Admins cannot change their own role (prevents self-demotion)
    - Role must be one of: "admin", "developer", or null (validated by Pydantic)

    Path Parameters:
    - user_id: UUID of the user to update

    Request Body:
    - role: "admin", "developer", or null

    Returns:
    - Updated user information
    """
    # Get role from request (Pydantic validates automatically)
    role = request.role

    # Check if user exists and get their clerk_user_id
    check_result = await session.execute(
        text("SELECT clerk_user_id FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    )
    user_row = check_result.first()
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    target_clerk_user_id = user_row[0]

    # Prevent admins from changing their own role
    if admin.clerk_user_id == target_clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

    # Skip Clerk update for test users (from NoAuth mode)
    if target_clerk_user_id == "test_user_noauth":
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "Test user - role not persisted to Clerk",
        }

    # In NoAuth mode, skip Clerk update (role is not persisted)
    if settings.torale_noauth:
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "NoAuth mode - role not persisted to Clerk",
        }

    # Update role in Clerk publicMetadata
    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    try:
        # Use update_metadata (not update) — it shallow-merges, preserving existing keys.
        # Passing None for a key removes it.
        await clerk_client.users.update_metadata_async(
            user_id=target_clerk_user_id,
            public_metadata={"role": role},
        )

        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user role: {str(e)}",
        ) from e


@router.patch("/users/roles")
async def bulk_update_user_roles(
    request: BulkUpdateUserRolesRequest,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Bulk update roles for multiple users.

    Request body:
    {
        "user_ids": ["uuid1", "uuid2", ...],  # 1-100 UUIDs
        "role": "admin" | "developer" | null
    }

    Returns:
    {
        "updated": 5,
        "failed": 0,
        "errors": []
    }
    """
    # Get validated data from Pydantic model
    user_ids = request.user_ids
    role = request.role

    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    updated_count = 0
    failed_count = 0
    errors = []

    # Batch fetch all clerk_user_ids in single query to avoid N+1 problem
    result = await session.execute(
        text("SELECT id, clerk_user_id FROM users WHERE id = ANY(:user_ids)"),
        {"user_ids": user_ids},
    )
    user_map = {str(row[0]): row[1] for row in result}  # db_id -> clerk_id

    # Batch-fetch all target users from Clerk to avoid N+1 API calls
    clerk_users_map = {}
    if user_map:
        clerk_ids = list(user_map.values())
        # Filter out test users before Clerk call
        clerk_ids_to_fetch = [cid for cid in clerk_ids if cid != "test_user_noauth"]

        if clerk_ids_to_fetch and not settings.torale_noauth:
            try:
                # Single batch API call for all users (max 100)
                clerk_users_response = await clerk_client.users.list_async(
                    user_id=clerk_ids_to_fetch, limit=100
                )
                clerk_users_map = {user.id: user for user in clerk_users_response.data}
            except Exception as e:
                logger.error(f"Clerk batch fetch failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to fetch users from Clerk: {e}",
                ) from e

    # Prepare all update tasks for parallel execution
    update_tasks = []
    task_metadata = []

    for user_id in user_ids:
        try:
            # Look up clerk_user_id from pre-fetched map
            if user_id not in user_map:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found"})
                continue

            target_clerk_user_id = user_map[user_id]

            # Prevent admins from changing their own role
            if admin.clerk_user_id == target_clerk_user_id:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "Cannot change own role"})
                continue

            # Skip test users and NoAuth mode
            if target_clerk_user_id == "test_user_noauth" or settings.torale_noauth:
                updated_count += 1  # Count as success but skip Clerk update
                continue

            # Get user from pre-fetched map instead of individual API call
            clerk_user = clerk_users_map.get(target_clerk_user_id)
            if not clerk_user:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found in Clerk"})
                continue

            # Use update_metadata (not update) — it shallow-merges, preserving existing keys.
            update_coro = clerk_client.users.update_metadata_async(
                user_id=target_clerk_user_id,
                public_metadata={"role": role},
            )
            update_tasks.append(update_coro)
            task_metadata.append({"user_id": user_id})

        except Exception as e:
            # Validation errors tracked immediately
            failed_count += 1
            errors.append({"user_id": user_id, "error": str(e)})

    # Execute all Clerk updates in parallel for massive performance improvement
    if update_tasks:
        results = await asyncio.gather(*update_tasks, return_exceptions=True)

        # Process results - track successes and failures
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_count += 1
                errors.append({"user_id": task_metadata[i]["user_id"], "error": str(result)})
            else:
                updated_count += 1

    return {
        "updated": updated_count,
        "failed": failed_count,
        "errors": errors,
    }


# Waitlist endpoints
@router.get("/waitlist")
async def list_waitlist(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
    status_filter: str | None = None,
):
    """
    List all waitlist entries (admin only).

    Optionally filter by status: pending, invited, or converted.
    """
    # Build query with optional status filter
    query = """
        SELECT id, email, created_at, status, invited_at, notes
        FROM waitlist
    """
    params = {}

    if status_filter:
        query += " WHERE status = :status"
        params["status"] = status_filter

    query += " ORDER BY created_at ASC"

    result = await session.execute(text(query), params)

    entries = [
        {
            "id": str(row[0]),
            "email": row[1],
            "created_at": row[2].isoformat() if row[2] else None,
            "status": row[3],
            "invited_at": row[4].isoformat() if row[4] else None,
            "notes": row[5],
        }
        for row in result
    ]

    return entries


@router.get("/waitlist/stats")
async def get_waitlist_stats(
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get waitlist statistics (admin only).

    Returns counts by status and recent growth.
    """
    result = await session.execute(
        text("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'invited') as invited,
            COUNT(*) FILTER (WHERE status = 'converted') as converted,
            COUNT(*) as total
        FROM waitlist
        """)
    )

    row = result.first()

    return {
        "pending": row[0] or 0,
        "invited": row[1] or 0,
        "converted": row[2] or 0,
        "total": row[3] or 0,
    }


class UpdateWaitlistEntryRequest(BaseModel):
    """Request model for updating a waitlist entry."""

    status: Literal["pending", "invited", "converted"] | None = None
    notes: str | None = None


@router.patch("/waitlist/{entry_id}")
async def update_waitlist_entry(
    entry_id: UUID,
    data: UpdateWaitlistEntryRequest,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Update waitlist entry (admin only).

    Used to mark entries as invited or add notes.
    """
    # Build update query
    updates = []
    params = {"entry_id": entry_id}

    if data.status is not None:
        updates.append("status = :status")
        params["status"] = data.status
        if data.status == "invited":
            updates.append("invited_at = :invited_at")
            params["invited_at"] = datetime.now(UTC)

    if data.notes is not None:
        updates.append("notes = :notes")
        params["notes"] = data.notes

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided",
        )

    query = f"""
        UPDATE waitlist
        SET {", ".join(updates)}
        WHERE id = :entry_id
        RETURNING id, email, created_at, status, invited_at, notes
    """

    result = await session.execute(text(query), params)
    await session.commit()

    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return {
        "id": str(row[0]),
        "email": row[1],
        "created_at": row[2].isoformat() if row[2] else None,
        "status": row[3],
        "invited_at": row[4].isoformat() if row[4] else None,
        "notes": row[5],
    }


@router.delete("/waitlist/{entry_id}")
async def delete_waitlist_entry(
    entry_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Delete waitlist entry (admin only).

    Use when removing spam or invalid entries.
    """
    result = await session.execute(
        text("DELETE FROM waitlist WHERE id = :entry_id"),
        {"entry_id": entry_id},
    )
    await session.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return {"status": "deleted"}


@router.post("/tasks/{task_id}/execute")
async def admin_execute_task(
    task_id: UUID,
    background_tasks: BackgroundTasks,
    suppress_notifications: bool = Query(default=True),
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Execute a task immediately (admin only).

    Allows admins to manually trigger execution of any user's task.
    Notifications are suppressed by default for admin executions.

    Path Parameters:
    - task_id: UUID of the task to execute

    Query Parameters:
    - suppress_notifications: Whether to suppress notifications (default: true)

    Returns:
    - Execution ID and status
    """
    # Fetch task (no user_id filter - admin can access any task)
    task_query = """
        SELECT t.id, t.name, t.user_id
        FROM tasks t
        WHERE t.id = $1
    """
    task_row = await db.fetch_one(task_query, task_id)

    if not task_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Reuse existing helper for execution creation + background task scheduling
    execution_row = await start_task_execution(
        task_id=str(task_id),
        task_name=task_row["name"],
        user_id=str(task_row["user_id"]),
        db=db,
        background_tasks=background_tasks,
        suppress_notifications=suppress_notifications,
        force=True,  # Admin executions always override stuck executions
    )

    logger.info(f"Admin {admin.email} started execution {execution_row['id']} for task {task_id}")

    return {
        "id": str(execution_row["id"]),
        "task_id": str(task_id),
        "status": "pending",
        "message": f"Execution started (notifications {'suppressed' if suppress_notifications else 'enabled'})",
    }
