"""Notification history API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends

from torale.api.auth import CurrentUser
from torale.core.database import Database, get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/sends")
async def list_notification_sends(
    user: CurrentUser,
    notification_type: str | None = None,
    task_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Database = Depends(get_db),
):
    """
    List notification send history for the user's tasks.

    Filters:
    - notification_type: Filter by 'email' or 'webhook'
    - task_id: Filter by specific task
    - limit: Max results to return (default: 50)
    - offset: Pagination offset (default: 0)

    Returns paginated notification sends with total count.
    """
    # Build query with filters
    where_clauses = ["t.user_id = $1"]
    params = [user.id]
    param_count = 1

    if notification_type:
        param_count += 1
        where_clauses.append(f"ns.notification_type = ${param_count}")
        params.append(notification_type)

    if task_id:
        param_count += 1
        where_clauses.append(f"ns.task_id = ${param_count}")
        params.append(UUID(task_id))

    where_clause = " AND ".join(where_clauses)

    # Get total count
    count_query = f"""
        SELECT COUNT(*)
        FROM notification_sends ns
        JOIN tasks t ON ns.task_id = t.id
        WHERE {where_clause}
    """
    total = await db.fetch_val(count_query, *params)

    # Get paginated results
    param_count += 1
    limit_param = f"${param_count}"
    param_count += 1
    offset_param = f"${param_count}"

    query = f"""
        SELECT
            ns.id,
            ns.user_id,
            ns.task_id,
            ns.execution_id,
            ns.recipient_email as recipient,
            ns.notification_type,
            ns.status,
            ns.error_message,
            ns.created_at
        FROM notification_sends ns
        JOIN tasks t ON ns.task_id = t.id
        WHERE {where_clause}
        ORDER BY ns.created_at DESC
        LIMIT {limit_param} OFFSET {offset_param}
    """

    sends = await db.fetch_all(query, *params, limit, offset)

    return {
        "sends": [dict(row) for row in sends],
        "total": total,
    }
