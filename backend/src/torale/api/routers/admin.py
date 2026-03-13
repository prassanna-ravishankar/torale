"""Admin console API endpoints for platform management."""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from torale.access import ClerkUser, clerk_client, require_admin
from torale.api.routers.tasks import start_task_execution
from torale.core.config import settings
from torale.core.database import Database, get_db
from torale.scheduler.scheduler import get_scheduler
from torale.tasks import TaskState
from torale.tasks.service import InvalidTransitionError, TaskService

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


def _serialize_waitlist_row(row) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "status": row["status"],
        "invited_at": row["invited_at"].isoformat() if row["invited_at"] else None,
        "notes": row["notes"],
    }


@router.get("/stats")
async def get_platform_stats(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Get platform-wide statistics for admin dashboard.

    Returns:
    - User capacity (total/used/available)
    - Task statistics (total/triggered/trigger_rate)
    - 24-hour execution metrics (total/failed/success_rate)
    - Popular queries (top 10 most common search queries)
    """
    max_users = getattr(settings, "max_users", 100)
    twenty_four_hours_ago = datetime.now(UTC) - timedelta(hours=24)

    # Each db.fetch_* acquires its own pool connection — run concurrently
    user_count_coro = db.fetch_val("SELECT COUNT(*) FROM users WHERE is_active = true")
    task_coro = db.fetch_one(
        """
        SELECT
            COUNT(*) as total_tasks,
            COALESCE(SUM(CASE WHEN e.notification IS NOT NULL THEN 1 ELSE 0 END), 0) as triggered_tasks
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.state = 'active'
        """
    )
    exec_coro = db.fetch_one(
        """
        SELECT
            COUNT(*) as total_executions,
            COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as failed_executions
        FROM task_executions
        WHERE created_at >= $1
        """,
        twenty_four_hours_ago,
    )
    popular_coro = db.fetch_all(
        """
        SELECT
            t.search_query,
            COUNT(*) as task_count,
            COALESCE(SUM(CASE WHEN e.notification IS NOT NULL THEN 1 ELSE 0 END), 0) as triggered_count
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.search_query IS NOT NULL
        GROUP BY t.search_query
        ORDER BY task_count DESC
        LIMIT 10
        """
    )

    total_users, task_row, exec_row, popular_rows = await asyncio.gather(
        user_count_coro, task_coro, exec_coro, popular_coro
    )

    total_tasks = task_row["total_tasks"] if task_row else 0
    triggered_tasks = task_row["triggered_tasks"] if task_row else 0
    trigger_rate = (triggered_tasks / total_tasks * 100) if total_tasks > 0 else 0

    total_executions = exec_row["total_executions"] if exec_row else 0
    failed_executions = exec_row["failed_executions"] if exec_row else 0
    success_rate = (
        (total_executions - failed_executions) / total_executions * 100
        if total_executions > 0
        else 100
    )

    popular_queries = [
        {
            "search_query": row["search_query"],
            "count": row["task_count"],
            "triggered_count": row["triggered_count"],
        }
        for row in popular_rows
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
    db: Database = Depends(get_db),
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

    rows = await db.fetch_all(
        f"""
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
        LIMIT $1
        """,
        limit,
    )

    queries = [
        {
            "id": str(row["id"]),
            "name": row["name"],
            "search_query": row["search_query"],
            "condition_description": row["condition_description"],
            "next_run": row["next_run"].isoformat() if row["next_run"] else None,
            "state": row["state"],
            "has_notification": row["last_notification"] is not None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "user_email": row["user_email"],
            "execution_count": row["execution_count"] or 0,
            "trigger_count": row["trigger_count"] or 0,
            "last_known_state": row["last_known_state"],
            "state_changed_at": row["state_changed_at"].isoformat()
            if row["state_changed_at"]
            else None,
        }
        for row in rows
    ]

    return {"queries": queries, "total": len(queries)}


@router.get("/executions")
async def list_recent_executions(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
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
    # Build query with positional params
    conditions = ["1=1"]
    params: list[Any] = []
    param_idx = 0

    if status_filter:
        param_idx += 1
        conditions.append(f"te.status = ${param_idx}")
        params.append(status_filter)
    if task_id:
        param_idx += 1
        conditions.append(f"te.task_id = ${param_idx}")
        params.append(task_id)

    param_idx += 1
    where_clause = " AND ".join(conditions)

    rows = await db.fetch_all(
        f"""
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
        WHERE {where_clause}
        ORDER BY te.started_at DESC
        LIMIT ${param_idx}
        """,
        *params,
        limit,
    )

    executions = [
        {
            "id": str(row["id"]),
            "task_id": str(row["task_id"]),
            "status": row["status"],
            "started_at": row["started_at"].isoformat() if row["started_at"] else None,
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
            "result": parse_json_field(row["result"]),
            "error_message": row["error_message"],
            "notification": row["notification"],
            "grounding_sources": parse_json_field(row["grounding_sources"]),
            "search_query": row["search_query"],
            "user_email": row["user_email"],
        }
        for row in rows
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
    db: Database = Depends(get_db),
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
    rows = await db.fetch_all(
        """
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
        LIMIT $1
        """,
        limit,
    )

    errors = [
        {
            "id": str(row["id"]),
            "task_id": str(row["task_id"]),
            "started_at": row["started_at"].isoformat() if row["started_at"] else None,
            "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
            "error_message": row["error_message"],
            "search_query": row["search_query"],
            "task_name": row["task_name"],
            "user_email": row["user_email"],
        }
        for row in rows
    ]

    return {"errors": errors, "total": len(errors)}


@router.get("/users")
async def list_users(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
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
    rows = await db.fetch_all(
        """
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
        """
    )

    # Batch-fetch roles from Clerk to avoid N+1 query problem
    role_map = {}
    clerk_warnings: list[str] = []
    if clerk_client:
        try:
            limit = 500
            offset = 0

            while True:
                clerk_users_response = await clerk_client.users.list_async(
                    limit=limit, offset=offset
                )

                if not clerk_users_response or not clerk_users_response.data:
                    break

                for user in clerk_users_response.data:
                    role_map[user.id] = (user.public_metadata or {}).get("role")

                if len(clerk_users_response.data) < limit:
                    break

                offset += limit

        except Exception as e:
            logger.error(f"Failed to batch-fetch users from Clerk: {e}")
            clerk_warnings.append(f"Clerk role fetch failed: {e}. Roles may be incomplete.")

    users = []
    for row in rows:
        user_data = {
            "id": str(row["id"]),
            "email": row["email"],
            "clerk_user_id": row["clerk_user_id"],
            "is_active": row["is_active"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "task_count": row["task_count"] or 0,
            "total_executions": row["total_executions"] or 0,
            "notifications_count": row["notifications_count"] or 0,
            "role": role_map.get(row["clerk_user_id"]),
        }
        users.append(user_data)

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
    check_row = await db.fetch_one("SELECT id FROM users WHERE id = $1", user_id)
    if not check_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    active_tasks = await db.fetch_all(
        "SELECT id, state FROM tasks WHERE user_id = $1 AND state = 'active'",
        user_id,
    )

    task_service = TaskService(db=db)
    paused_count = 0
    failed_tasks = []

    for task_row in active_tasks:
        try:
            current_state = TaskState(task_row["state"])
            await task_service.pause(task_id=task_row["id"], current_state=current_state)
            paused_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": str(task_row["id"]), "error": str(e)})

    await db.execute(
        "UPDATE users SET is_active = false, updated_at = NOW() WHERE id = $1",
        user_id,
    )

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
    db: Database = Depends(get_db),
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
    role = request.role

    user_row = await db.fetch_one("SELECT clerk_user_id FROM users WHERE id = $1", user_id)
    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    target_clerk_user_id = user_row["clerk_user_id"]

    if admin.clerk_user_id == target_clerk_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role",
        )

    if target_clerk_user_id == "test_user_noauth":
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "Test user - role not persisted to Clerk",
        }

    if settings.torale_noauth:
        return {
            "status": "updated",
            "user_id": str(user_id),
            "role": role,
            "note": "NoAuth mode - role not persisted to Clerk",
        }

    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    try:
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
    db: Database = Depends(get_db),
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

    rows = await db.fetch_all(
        "SELECT id, clerk_user_id FROM users WHERE id = ANY($1::uuid[])",
        user_ids,
    )
    user_map = {str(row["id"]): row["clerk_user_id"] for row in rows}

    clerk_users_map = {}
    if user_map:
        clerk_ids = list(user_map.values())
        clerk_ids_to_fetch = [cid for cid in clerk_ids if cid != "test_user_noauth"]

        if clerk_ids_to_fetch and not settings.torale_noauth:
            try:
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

    update_tasks = []
    task_metadata = []

    for user_id in user_ids:
        try:
            if user_id not in user_map:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found"})
                continue

            target_clerk_user_id = user_map[user_id]

            if admin.clerk_user_id == target_clerk_user_id:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "Cannot change own role"})
                continue

            if target_clerk_user_id == "test_user_noauth" or settings.torale_noauth:
                updated_count += 1
                continue

            clerk_user = clerk_users_map.get(target_clerk_user_id)
            if not clerk_user:
                failed_count += 1
                errors.append({"user_id": user_id, "error": "User not found in Clerk"})
                continue

            update_coro = clerk_client.users.update_metadata_async(
                user_id=target_clerk_user_id,
                public_metadata={"role": role},
            )
            update_tasks.append(update_coro)
            task_metadata.append({"user_id": user_id})

        except Exception as e:
            failed_count += 1
            errors.append({"user_id": user_id, "error": str(e)})

    if update_tasks:
        results = await asyncio.gather(*update_tasks, return_exceptions=True)

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
    db: Database = Depends(get_db),
    status_filter: str | None = None,
):
    """
    List all waitlist entries (admin only).

    Optionally filter by status: pending, invited, or converted.
    """
    query = "SELECT id, email, created_at, status, invited_at, notes FROM waitlist"
    params: list[Any] = []
    if status_filter:
        query += " WHERE status = $1"
        params.append(status_filter)
    query += " ORDER BY created_at ASC"
    rows = await db.fetch_all(query, *params)

    return [_serialize_waitlist_row(row) for row in rows]


@router.get("/waitlist/stats")
async def get_waitlist_stats(
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Get waitlist statistics (admin only).

    Returns counts by status and recent growth.
    """
    row = await db.fetch_one(
        """
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'invited') as invited,
            COUNT(*) FILTER (WHERE status = 'converted') as converted,
            COUNT(*) as total
        FROM waitlist
        """
    )

    return {
        "pending": row["pending"] or 0,
        "invited": row["invited"] or 0,
        "converted": row["converted"] or 0,
        "total": row["total"] or 0,
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
    db: Database = Depends(get_db),
):
    """
    Update waitlist entry (admin only).

    Used to mark entries as invited or add notes.
    """
    updates = []
    params: list[Any] = [entry_id]  # $1 = entry_id
    param_idx = 1

    if data.status is not None:
        param_idx += 1
        updates.append(f"status = ${param_idx}")
        params.append(data.status)
        if data.status == "invited":
            param_idx += 1
            updates.append(f"invited_at = ${param_idx}")
            params.append(datetime.now(UTC))

    if data.notes is not None:
        param_idx += 1
        updates.append(f"notes = ${param_idx}")
        params.append(data.notes)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided",
        )

    row = await db.fetch_one(
        f"""
        UPDATE waitlist
        SET {", ".join(updates)}
        WHERE id = $1
        RETURNING id, email, created_at, status, invited_at, notes
        """,
        *params,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return _serialize_waitlist_row(row)


@router.delete("/waitlist/{entry_id}")
async def delete_waitlist_entry(
    entry_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    db: Database = Depends(get_db),
):
    """
    Delete waitlist entry (admin only).

    Use when removing spam or invalid entries.
    """
    row = await db.fetch_one(
        "DELETE FROM waitlist WHERE id = $1 RETURNING id",
        entry_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Waitlist entry not found",
        )

    return {"status": "deleted"}


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
