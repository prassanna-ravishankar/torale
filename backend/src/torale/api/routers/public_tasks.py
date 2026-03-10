"""Public task discovery and RSS feeds."""

import json
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel

from torale.access import OptionalUser
from torale.api.rate_limiter import limiter
from torale.api.routers.tasks import get_task
from torale.api.utils.task_parsers import parse_task_with_execution
from torale.core.config import settings
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


# Separate router for root-level RSS feed (mounted without /api/v1 prefix)
rss_router = APIRouter(tags=["public"])


@rss_router.get("/t/{task_id}/rss")
@limiter.limit("10/minute")
async def get_task_rss_feed(
    request: Request,
    task_id: UUID,
    db: Database = Depends(get_db),
):
    """
    RSS 2.0 feed for a public task's execution results (NO AUTH REQUIRED).

    Subscribe to this feed to get notified of new monitoring results.
    """
    # Look up task and verify it's public
    task_query = "SELECT id, name, condition_description, is_public FROM tasks WHERE id = $1"
    task_row = await db.fetch_one(task_query, task_id)

    if not task_row or not task_row["is_public"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Fetch last 50 completed executions
    executions_query = """
        SELECT id, completed_at, result, condition_met, grounding_sources
        FROM task_executions
        WHERE task_id = $1 AND status = 'completed' AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 50
    """
    executions = await db.fetch_all(executions_query, task_id)

    base_url = settings.frontend_url or "https://torale.ai"
    task_link = f"{base_url}/tasks/{task_id}"
    feed_url = f"{base_url}/t/{task_id}/rss"

    # Register atom namespace to avoid ns0 prefix
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

    # Build RSS 2.0 feed
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = f"{task_row['name']} - Torale Monitor"
    ET.SubElement(channel, "link").text = task_link
    ET.SubElement(
        channel, "description"
    ).text = f"Monitoring results for: {task_row['condition_description']}"
    ET.SubElement(channel, "language").text = "en-us"

    # Atom self-link for autodiscovery
    atom_link = ET.SubElement(
        channel, "{http://www.w3.org/2005/Atom}link", rel="self", type="application/rss+xml"
    )
    atom_link.set("href", feed_url)

    for execution in executions:
        result = execution["result"] or {}
        if isinstance(result, str):
            result = json.loads(result)

        grounding_sources = execution["grounding_sources"] or []
        if isinstance(grounding_sources, str):
            grounding_sources = json.loads(grounding_sources)

        # Build title
        evidence = result.get("evidence", "")
        notification = result.get("notification", "")
        if notification:
            title_text = notification
        elif evidence:
            title_text = evidence[:100] + ("..." if len(evidence) > 100 else "")
        else:
            title_text = f"Execution {execution['completed_at'].isoformat()}"

        # Build description from evidence + sources
        description_parts = []
        if evidence:
            description_parts.append(evidence)
        if grounding_sources:
            description_parts.append("\n\nSources:")
            for source in grounding_sources:
                url = source.get("url", "")
                source_title = source.get("title", url)
                if url:
                    description_parts.append(f'- <a href="{url}">{source_title}</a>')

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title_text
        ET.SubElement(item, "link").text = task_link
        ET.SubElement(item, "guid", isPermaLink="false").text = str(execution["id"])
        ET.SubElement(item, "pubDate").text = format_datetime(execution["completed_at"])
        ET.SubElement(item, "description").text = "\n".join(description_parts)

        if execution["condition_met"]:
            ET.SubElement(item, "category").text = "Condition Met"

    xml_output = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return Response(content=xml_output, media_type="application/rss+xml")
