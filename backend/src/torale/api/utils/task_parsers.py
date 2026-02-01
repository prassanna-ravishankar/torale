"""Shared utilities for parsing task and execution rows from the database."""

import json

from torale.tasks import Task


def parse_task_row(row) -> dict:
    """Parse a task row from the database, converting JSON strings to dicts"""
    task_dict = dict(row)
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


def parse_task_with_execution(row) -> Task:
    """
    Parse a task row with embedded execution data from LEFT JOIN query.

    This helper extracts duplicate logic from list_tasks and get_task endpoints.
    Expects row from query that joins tasks with task_executions, using aliases:
    - exec_id, exec_condition_met, exec_started_at, etc.

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

        task_dict["last_execution"] = {
            "id": row["exec_id"],
            "task_id": task_dict["id"],
            "condition_met": row["exec_condition_met"],
            "started_at": row["exec_started_at"],
            "completed_at": row["exec_completed_at"],
            "status": row["exec_status"],
            "result": exec_result,
            "change_summary": row["exec_change_summary"],
            "grounding_sources": exec_sources,
        }

    return Task(**task_dict)
