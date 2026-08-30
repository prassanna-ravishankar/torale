"""Admin statistics and operational-observability routes."""

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from webwhen.access import ClerkUser, require_admin
from webwhen.api.routers.admin_routes.common import parse_json_field
from webwhen.core.config import settings
from webwhen.core.database import Database, get_db
from webwhen.scheduler.scheduler import get_scheduler

router = APIRouter()


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
