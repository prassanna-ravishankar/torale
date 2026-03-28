"""Public task discovery and RSS feeds."""

import xml.etree.ElementTree as ET
from email.utils import format_datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict

from torale.access import OptionalUser
from torale.api.rate_limiter import limiter
from torale.api.routers.tasks import get_task
from torale.api.utils.task_parsers import (
    fetch_feed_executions,
    parse_task_with_execution,
)
from torale.core.config import settings
from torale.core.database import Database, get_db
from torale.tasks import FeedExecution, Task
from torale.utils.jsonb import parse_jsonb

# Register atom namespace once at module level (avoids per-request global mutation)
ET.register_namespace("atom", "http://www.w3.org/2005/Atom")

router = APIRouter(prefix="/public", tags=["public"])


class PublicTask(Task):
    """Task model with user_id stripped for public responses."""

    model_config = ConfigDict(from_attributes=True, fields={"user_id": {"exclude": True}})


class PublicFeedExecution(FeedExecution):
    """Feed execution with task_user_id stripped for public responses."""

    model_config = ConfigDict(
        from_attributes=True, fields={"task_user_id": {"exclude": True}}
    )


class PublicTasksResponse(BaseModel):
    """Response for public tasks listing."""

    tasks: list[PublicTask]
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
    # Build query with dynamic ORDER BY clause (validated by FastAPI enum)
    # Use dictionary mapping to prevent any possibility of SQL injection
    order_clauses = {
        "popular": "ORDER BY t.view_count DESC, t.created_at DESC",
        "recent": "ORDER BY t.created_at DESC",
    }
    order_clause = order_clauses[sort_by]

    tasks_query = f"""
        SELECT t.*,
               e.id as exec_id,
               e.notification as exec_notification,
               e.started_at as exec_started_at,
               e.completed_at as exec_completed_at,
               e.status as exec_status,
               e.result as exec_result,
               e.grounding_sources as exec_grounding_sources,
               count(*) OVER() as total_count
        FROM tasks t
        LEFT JOIN task_executions e ON t.last_execution_id = e.id
        WHERE t.is_public = true
        {order_clause}
        LIMIT $1 OFFSET $2
    """

    rows = await db.fetch_all(tasks_query, limit, offset)
    if rows:
        total = rows[0]["total_count"]
    else:
        # Window function returns nothing when offset is past end; fall back to COUNT
        count_row = await db.fetch_one("SELECT COUNT(*) as total FROM tasks WHERE is_public = true")
        total = count_row["total"] if count_row else 0

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
        scrubbed_tasks.append(PublicTask.model_validate(task))

    return PublicTasksResponse(
        tasks=scrubbed_tasks,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/feed", response_model=list[PublicFeedExecution])
@limiter.limit("10/minute")
async def get_public_feed(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    db: Database = Depends(get_db),
):
    """
    Get a global feed of recent successful executions across all public tasks.
    Only returns executions that produced a notification (condition met).
    """
    executions = await fetch_feed_executions(
        db, where_clause="t.is_public = true", params=[], limit=limit
    )
    return [PublicFeedExecution.model_validate(e) for e in executions]


@router.get("/tasks/id/{task_id}", response_model=PublicTask)
@limiter.limit("20/minute")
async def get_public_task_by_id(
    request: Request,
    task_id: UUID,
    user: OptionalUser,
    db: Database = Depends(get_db),
):
    """
    Get a public task by UUID (NO AUTH REQUIRED).
    """
    # Delegates to the shared get_task logic (handles owner vs public access)
    task = await get_task(task_id, user, db)
    return PublicTask.model_validate(task)


# Separate router for root-level RSS feed (mounted without /api/v1 prefix)
rss_router = APIRouter(tags=["public"])


@rss_router.get("/tasks/{task_id}/rss")
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

    # Fetch last 50 successful executions
    executions_query = """
        SELECT id, completed_at, notification, result, grounding_sources
        FROM task_executions
        WHERE task_id = $1 AND status = 'success' AND completed_at IS NOT NULL
        ORDER BY completed_at DESC
        LIMIT 50
    """
    executions = await db.fetch_all(executions_query, task_id)

    task_link = f"{settings.frontend_url}/tasks/{task_id}"
    feed_url = str(request.url_for("get_task_rss_feed", task_id=task_id))

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
        result = parse_jsonb(execution["result"], "result", dict, {})
        grounding_sources = parse_jsonb(
            execution["grounding_sources"], "grounding_sources", list, []
        )

        # Build title from notification (condition met) or evidence
        evidence = result.get("evidence", "")
        notification_text = execution["notification"] or ""
        if notification_text:
            title_text = notification_text
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
                if url and url.startswith(("https://", "http://")):
                    description_parts.append(f"- {source_title}: {url}")

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title_text
        ET.SubElement(item, "link").text = task_link
        ET.SubElement(item, "guid", isPermaLink="false").text = str(execution["id"])
        ET.SubElement(item, "pubDate").text = format_datetime(execution["completed_at"])
        ET.SubElement(item, "description").text = "\n".join(description_parts)

        if notification_text:
            ET.SubElement(item, "category").text = "Condition Met"

    xml_output = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return Response(content=xml_output, media_type="application/rss+xml")
