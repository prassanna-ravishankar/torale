"""Admin console API endpoints for platform management."""

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio.client import Client

from torale.api.clerk_auth import ClerkUser, require_admin
from torale.api.users import get_async_session
from torale.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


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


def parse_json_field(value: Any) -> Any:
    """Parse JSON field if it's a string, otherwise return as-is."""
    if isinstance(value, str):
        try:
            return json.loads(value) if value else None
        except json.JSONDecodeError:
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
            SUM(CASE WHEN condition_met = true THEN 1 ELSE 0 END) as triggered_tasks
        FROM tasks
        WHERE is_active = true
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
            search_query,
            COUNT(*) as task_count,
            SUM(CASE WHEN condition_met = true THEN 1 ELSE 0 END) as triggered_count
        FROM tasks
        WHERE search_query IS NOT NULL
        GROUP BY search_query
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
    - Task details (name, query, condition, schedule)
    - Execution statistics (count, trigger count, condition_met)
    """
    active_filter = "AND t.is_active = true" if active_only else ""

    result = await session.execute(
        text(f"""
        SELECT
            t.id,
            t.name,
            t.search_query,
            t.condition_description,
            t.schedule,
            t.is_active,
            t.condition_met,
            t.created_at,
            u.email as user_email,
            COUNT(te.id) as execution_count,
            SUM(CASE WHEN te.condition_met = true THEN 1 ELSE 0 END) as trigger_count
        FROM tasks t
        JOIN users u ON u.id = t.user_id
        LEFT JOIN task_executions te ON te.task_id = t.id
        WHERE 1=1 {active_filter}
        GROUP BY t.id, u.email
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
            "schedule": row[4],
            "is_active": row[5],
            "condition_met": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "user_email": row[8],
            "execution_count": row[9] if row[9] else 0,
            "trigger_count": row[10] if row[10] else 0,
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
            te.condition_met,
            te.change_summary,
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
            "condition_met": row[7],
            "change_summary": row[8],
            "grounding_sources": parse_json_field(row[9]),
            "search_query": row[10],
            "user_email": row[11],
        }
        for row in result
    ]

    return {"executions": executions, "total": len(executions)}


@router.get("/temporal/workflows")
async def list_temporal_workflows(
    admin: ClerkUser = Depends(require_admin),
):
    """
    List recent Temporal workflow executions.

    Returns:
    - Workflow ID and run ID
    - Workflow type (e.g., TaskExecutionWorkflow)
    - Status (RUNNING, COMPLETED, FAILED, TIMED_OUT)
    - Start/close timestamps
    - Execution duration
    - UI URL (clickable link to Temporal UI)
    """
    try:
        client = await get_temporal_client()

        # Use configured Temporal UI URL
        temporal_ui_base = settings.temporal_ui_url

        # List recent workflows (last 100)
        workflows = []
        async for workflow in client.list_workflows(
            f"ExecutionTime >= '{(datetime.now(UTC) - timedelta(hours=24)).isoformat()}'"
        ):
            # Construct UI URL: {base}/namespaces/{namespace}/workflows/{workflow_id}/{run_id}/history
            ui_url = f"{temporal_ui_base}/namespaces/{settings.temporal_namespace}/workflows/{workflow.id}/{workflow.run_id}/history"

            workflows.append(
                {
                    "workflow_id": workflow.id,
                    "run_id": workflow.run_id,
                    "workflow_type": workflow.workflow_type,
                    "status": workflow.status.name,
                    "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                    "close_time": workflow.close_time.isoformat() if workflow.close_time else None,
                    "execution_time": workflow.execution_time.isoformat()
                    if workflow.execution_time
                    else None,
                    "ui_url": ui_url,
                }
            )

            # Limit to 100 workflows
            if len(workflows) >= 100:
                break

        return {"workflows": workflows, "total": len(workflows)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Temporal workflows: {str(e)}",
        ) from e


@router.get("/temporal/schedules")
async def list_temporal_schedules(
    admin: ClerkUser = Depends(require_admin),
):
    """
    List all active Temporal schedules.

    Returns:
    - Schedule ID (matches task ID)
    - Cron spec
    - Next scheduled run time
    - Paused/running status
    - Recent action count
    """
    try:
        client = await get_temporal_client()

        schedules = []
        schedule_iterator = await client.list_schedules()
        async for schedule in schedule_iterator:
            handle = client.get_schedule_handle(schedule.id)
            desc = await handle.describe()

            # Extract cron spec
            cron_spec = None
            if desc.schedule.spec and desc.schedule.spec.cron_expressions:
                cron_spec = desc.schedule.spec.cron_expressions[0]

            # Get memo data from description (memo is an async method)
            try:
                memo_data = await desc.memo()
            except Exception:
                memo_data = {}

            schedules.append(
                {
                    "schedule_id": schedule.id,
                    "spec": cron_spec,
                    "paused": desc.schedule.state.paused,
                    "next_run": None,  # Would need to compute from cron
                    "recent_actions": len(desc.info.recent_actions)
                    if desc.info.recent_actions
                    else 0,
                    "created_at": memo_data.get("created_at") if memo_data else None,
                }
            )

        return {"schedules": schedules, "total": len(schedules)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Temporal schedules: {str(e)}",
        ) from e


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
    List all platform users with statistics.

    Returns:
    - All user accounts with email and Clerk ID
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
            SUM(CASE WHEN te.condition_met = true THEN 1 ELSE 0 END) as conditions_met_count
        FROM users u
        LEFT JOIN tasks t ON t.user_id = u.id
        LEFT JOIN task_executions te ON te.task_id = t.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
        """)
    )

    users = [
        {
            "id": str(row[0]),
            "email": row[1],
            "clerk_user_id": row[2],
            "is_active": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "task_count": row[5] if row[5] else 0,
            "total_executions": row[6] if row[6] else 0,
            "conditions_met_count": row[7] if row[7] else 0,
        }
        for row in result
    ]

    # Get capacity info
    active_users = sum(1 for u in users if u["is_active"])
    max_users = getattr(settings, "max_users", 100)

    return {
        "users": users,
        "capacity": {
            "used": active_users,
            "total": max_users,
            "available": max_users - active_users,
        },
    }


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    admin: ClerkUser = Depends(require_admin),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Manually deactivate a user account.

    This sets is_active = false and deactivates all their tasks.
    Frees up a seat in the capacity limit.

    Path Parameters:
    - user_id: UUID of the user to deactivate

    Returns:
    - Status confirmation
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

    # Deactivate user and all their tasks in a single transaction
    try:
        await session.execute(
            text("UPDATE users SET is_active = false, updated_at = NOW() WHERE id = :user_id"),
            {"user_id": user_id},
        )
        await session.execute(
            text("UPDATE tasks SET is_active = false, updated_at = NOW() WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}",
        ) from e

    return {"status": "deactivated", "user_id": str(user_id)}


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


@router.patch("/waitlist/{entry_id}")
async def update_waitlist_entry(
    entry_id: UUID,
    data: dict,
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

    if "status" in data:
        updates.append("status = :status")
        params["status"] = data["status"]
        if data["status"] == "invited":
            updates.append("invited_at = :invited_at")
            params["invited_at"] = datetime.now(UTC)

    if "notes" in data:
        updates.append("notes = :notes")
        params["notes"] = data["notes"]

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
