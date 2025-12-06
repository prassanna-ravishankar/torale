"""OpenGraph image serving for shareable tasks."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from torale.core.config import PROJECT_ROOT
from torale.core.database import Database, get_db

router = APIRouter(prefix="/api/v1/og", tags=["opengraph"])

# Rate limiter for OG image endpoint (based on IP)
limiter = Limiter(key_func=get_remote_address)

# Path to static OG image
STATIC_DIR = PROJECT_ROOT / "static"
OG_IMAGE_PATH = STATIC_DIR / "og-default.jpg"


@router.get("/tasks/{task_id}.jpg")
@limiter.limit("10/minute")
async def get_task_og_image(
    request: Request,
    task_id: UUID,
    db: Database = Depends(get_db),
):
    """
    Serve OpenGraph image for a task.

    Returns a static 1200x630 JPEG image for all public tasks.
    Validates that the task exists and is public before serving.

    This uses a generic branded OG image rather than dynamic generation
    to avoid font dependencies and CPU-intensive processing.

    Rate limited to 10 requests/minute per IP to prevent abuse.
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
    # Cache for 1 hour (matches PR description)
    return FileResponse(
        OG_IMAGE_PATH,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )
