"""Task templates API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from torale.core.database import Database, get_db
from torale.tasks import TaskTemplate

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/", response_model=list[TaskTemplate])
async def list_templates(category: str | None = None, db: Database = Depends(get_db)):
    """
    List all active task templates.

    Optionally filter by category.
    """
    if category:
        query = """
            SELECT * FROM task_templates
            WHERE is_active = true AND category = $1
            ORDER BY category, name
        """
        rows = await db.fetch_all(query, category)
    else:
        query = """
            SELECT * FROM task_templates
            WHERE is_active = true
            ORDER BY category, name
        """
        rows = await db.fetch_all(query)

    templates = [TaskTemplate(**dict(row)) for row in rows]
    return templates


@router.get("/{template_id}", response_model=TaskTemplate)
async def get_template(template_id: UUID, db: Database = Depends(get_db)):
    """Get a specific template by ID."""
    query = """
        SELECT * FROM task_templates
        WHERE id = $1 AND is_active = true
    """
    row = await db.fetch_one(query, template_id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    return TaskTemplate(**dict(row))
