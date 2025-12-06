"""OpenGraph image serving for shareable tasks."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from torale.core.config import PROJECT_ROOT
from torale.core.database import Database, get_db

router = APIRouter(prefix="/api/v1/og", tags=["opengraph"])

# Path to static OG image
STATIC_DIR = PROJECT_ROOT / "static"
OG_IMAGE_PATH = STATIC_DIR / "og-default.jpg"


@router.get("/tasks/{task_id}.jpg")
async def get_task_og_image(
    task_id: UUID,
    db: Database = Depends(get_db),
):
    """
    Serve OpenGraph image for a task.

    Returns a static 1200x630 JPEG image for all public tasks.
    Validates that the task exists and is public before serving.

    This uses a generic branded OG image rather than dynamic generation
    to avoid font dependencies and CPU-intensive processing.
    """
    # Verify task exists and is public
    task = await db.fetch_one(
        "SELECT is_public FROM tasks WHERE id = $1",
        task_id,
    )

    if not task or not task["is_public"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not public",
        )

    # Serve static OG image
    # Cache for 1 year since image is static and never changes
    return FileResponse(
        OG_IMAGE_PATH,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
