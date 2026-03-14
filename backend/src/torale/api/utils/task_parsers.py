"""Shared utilities for parsing task and execution rows from the database."""

import json

from torale.tasks import FeedExecution, Task, TaskStatus


def parse_task_row(row) -> dict:
    """Parse a task row from the database, converting JSON strings to dicts"""
    task_dict = dict(row)
    # Parse last_known_state if it's a string
    if isinstance(task_dict.get("last_known_state"), str):
        raw_state = task_dict.get("last_known_state", "").strip()
        if not raw_state:
            task_dict["last_known_state"] = None
        else:
            try:
                task_dict["last_known_state"] = json.loads(raw_state)
            except json.JSONDecodeError:
                task_dict["last_known_state"] = {"evidence": raw_state}
    # Parse notifications if it's a string
    if isinstance(task_dict.get("notifications"), str):
        task_dict["notifications"] = (
            json.loads(task_dict["notifications"]) if task_dict["notifications"] else []
        )
    return task_dict


def _enrich_result_for_frontend(result: dict) -> None:
    """Add frontend-compatible keys to agent result dict if missing."""
    if "metadata" not in result:
        result["metadata"] = {
            "changed": result.get("notification") is not None,
            "current_state": None,
        }


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
    # Enrich result with frontend-compatible shape
    if isinstance(exec_dict.get("result"), dict):
        _enrich_result_for_frontend(exec_dict["result"])
    return exec_dict


def parse_feed_execution_row(row) -> FeedExecution:
    """Parse a task_execution row with joined task metadata."""
    exec_dict = parse_execution_row(row)

    # Remove task-prefixed fields from exec_dict if present to avoid duplicate keyword arguments
    # when unpacking into FeedExecution
    for key in ["task_name", "task_search_query", "task_is_public", "task_user_id"]:
        exec_dict.pop(key, None)

    return FeedExecution(
        **exec_dict,
        task_name=row["task_name"],
        task_search_query=row.get("task_search_query"),
        task_is_public=row.get("task_is_public", False),
        task_user_id=row["task_user_id"],
    )


async def fetch_feed_executions(
    db, *, where_clause: str, params: list, limit: int
) -> list[FeedExecution]:
    """Shared feed query: fetch recent successful executions with task metadata.

    Args:
        db: Database connection.
        where_clause: SQL WHERE fragment for task filtering (e.g. "t.is_public = true").
        params: Bind parameters for the where_clause.
        limit: Max rows to return.
    """
    param_offset = len(params)
    query = f"""
        SELECT e.id, e.task_id, e.status, e.result, e.notification,
               e.grounding_sources, e.error_message,
               e.started_at, e.completed_at, e.created_at,
               t.name as task_name,
               t.search_query as task_search_query,
               t.is_public as task_is_public,
               t.user_id as task_user_id
        FROM task_executions e
        JOIN tasks t ON e.task_id = t.id
        WHERE {where_clause}
          AND e.status = ${param_offset + 1}
          AND e.notification IS NOT NULL
        ORDER BY e.started_at DESC
        LIMIT ${param_offset + 2}
    """
    rows = await db.fetch_all(query, *params, TaskStatus.SUCCESS.value, limit)
    return [parse_feed_execution_row(row) for row in rows]


def parse_task_with_execution(row) -> Task:
    """
    Parse a task row with embedded execution data from LEFT JOIN query.

    This helper extracts duplicate logic from list_tasks and get_task endpoints.
    Expects row from query that joins tasks with task_executions, using aliases:
    - exec_id, exec_notification, exec_started_at, etc.

    Args:
        row: Database row with task fields and optional execution fields (prefixed with exec_)

    Returns:
        Task object with embedded last_execution if execution data exists
    """
    task_dict = parse_task_row(row)

    # Embed execution if exists
    if row["exec_id"]:
        # Parse JSONB fields - asyncpg may return them as dicts or strings depending on context
        exec_result = row["exec_result"]
        if isinstance(exec_result, str):
            exec_result = json.loads(exec_result) if exec_result else None

        exec_sources = row["exec_grounding_sources"]
        if isinstance(exec_sources, str):
            exec_sources = json.loads(exec_sources) if exec_sources else None

        if isinstance(exec_result, dict):
            _enrich_result_for_frontend(exec_result)

        task_dict["last_execution"] = {
            "id": row["exec_id"],
            "task_id": task_dict["id"],
            "notification": row["exec_notification"],
            "started_at": row["exec_started_at"],
            "completed_at": row["exec_completed_at"],
            "status": row["exec_status"],
            "result": exec_result,
            "grounding_sources": exec_sources,
        }

    return Task(**task_dict)
