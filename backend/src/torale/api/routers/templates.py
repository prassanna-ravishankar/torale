"""Task templates API endpoints."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from torale.core.database import Database, get_db
from torale.core.models import TaskTemplate

router = APIRouter(prefix="/templates", tags=["templates"])


def parse_template_row(row) -> dict:
    """Parse a template row from the database, converting JSON strings to dicts"""
    template_dict = dict(row)
    # Parse config if it's a string
    if isinstance(template_dict.get("config"), str):
        template_dict["config"] = json.loads(template_dict["config"])
    return template_dict


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

    templates = [TaskTemplate(**parse_template_row(row)) for row in rows]
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

    return TaskTemplate(**parse_template_row(row))
