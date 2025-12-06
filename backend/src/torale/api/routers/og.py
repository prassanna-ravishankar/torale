"""OpenGraph image generation for shareable tasks."""

import asyncio
import io
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from PIL import Image, ImageDraw, ImageFont
from slowapi import Limiter

from torale.core.database import Database, get_db

router = APIRouter(prefix="/api/v1/og", tags=["opengraph"])

# Rate limiter for OG image generation (CPU-intensive)
# Global limit: 10 requests per minute across all IPs (cost control)
limiter = Limiter(key_func=lambda request: "global")

# Paths to assets
STATIC_DIR = Path(__file__).parent.parent.parent.parent.parent / "static"
TEMPLATE_PATH = STATIC_DIR / "og-template.jpeg"
FONT_DIR = STATIC_DIR / "fonts"
TITLE_FONT_PATH = FONT_DIR / "SpaceGrotesk-Bold.ttf"
DESC_FONT_PATH = FONT_DIR / "Inter-Regular.ttf"


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """
    Wrap text to fit within max_width pixels.

    Args:
        text: Text to wrap
        font: Font to use for measuring
        max_width: Maximum width in pixels

    Returns:
        List of text lines
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def _generate_og_image_sync(task_name: str, search_query: str) -> bytes:
    """
    Synchronous image generation function (CPU/IO intensive).

    This function performs blocking operations and should be called via
    asyncio.to_thread() to avoid blocking the event loop.

    Args:
        task_name: Task name to display
        search_query: Search query to display

    Returns:
        JPEG image bytes

    Raises:
        HTTPException if template not found
    """
    # Load template image
    if not TEMPLATE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OG template not found",
        )

    img = Image.open(TEMPLATE_PATH).copy()
    draw = ImageDraw.Draw(img)

    # Load Torale brand fonts (Space Grotesk for titles, Inter for body)
    try:
        # Use Torale design system fonts
        title_font = ImageFont.truetype(str(TITLE_FONT_PATH), 28)  # Space Grotesk Bold
        desc_font = ImageFont.truetype(str(DESC_FONT_PATH), 18)  # Inter Regular
    except OSError:
        # Fallback to system fonts (try Linux paths first, then macOS)
        try:
            # Try Linux system fonts (common in Docker containers)
            title_font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28
            )
            desc_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except OSError:
            try:
                # Try macOS system fonts
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
                desc_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
            except OSError:
                # Final fallback (basic PIL font)
                title_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()

    # Text overlay zones (in 1200x630 dimensions)
    # Title box: (344,217) to (950,294)
    title_y = 217 + 10
    title_max_width = (950 - 344) - 20  # Box width minus padding

    # Description box: (368,334) to (828,421)
    desc_y = 334 + 10
    desc_max_width = (828 - 368) - 20  # Box width minus padding

    # Draw title (task name) - wrapped and centered
    title_lines = wrap_text(task_name, title_font, title_max_width)

    # Calculate total height for vertical centering
    total_title_height = 0
    for line in title_lines[:2]:
        bbox = title_font.getbbox(line)
        total_title_height += (bbox[3] - bbox[1]) + 10
    total_title_height -= 10  # Remove last spacing

    # Start position for vertical centering in title box
    title_box_height = 294 - 217
    y_position = title_y + (title_box_height - total_title_height) // 2

    for line in title_lines[:2]:  # Max 2 lines for title
        # Horizontal centering
        bbox = title_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        title_box_width = 950 - 344
        x_centered = 344 + (title_box_width - text_width) // 2

        draw.text((x_centered, y_position), line, fill="#1e293b", font=title_font)  # Dark slate
        line_height = bbox[3] - bbox[1]
        y_position += line_height + 10

    # Draw search query - wrapped and centered
    query_lines = wrap_text(search_query, desc_font, desc_max_width)

    # Calculate total height for vertical centering
    total_desc_height = 0
    for line in query_lines[:3]:
        bbox = desc_font.getbbox(line)
        total_desc_height += (bbox[3] - bbox[1]) + 8
    total_desc_height -= 8  # Remove last spacing

    # Start position for vertical centering in description box
    desc_box_height = 421 - 334
    y_position = desc_y + (desc_box_height - total_desc_height) // 2

    for line in query_lines[:3]:  # Max 3 lines for description
        # Horizontal centering
        bbox = desc_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        desc_box_width = 828 - 368
        x_centered = 368 + (desc_box_width - text_width) // 2

        draw.text((x_centered, y_position), line, fill="#64748b", font=desc_font)  # Slate gray
        line_height = bbox[3] - bbox[1]
        y_position += line_height + 8

    # Convert to JPEG bytes (much smaller than PNG for photos/gradients)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG", quality=85, optimize=True)
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()


@router.get("/tasks/{task_id}.jpg")
@limiter.limit("10/minute")
async def generate_task_og_image(
    request: Request,
    task_id: UUID,
    db: Database = Depends(get_db),
):
    """
    Generate OpenGraph image for a task.

    Returns a 1200x630 JPEG image with task details.
    Only works for public tasks.

    Image generation is CPU/IO intensive and runs in a thread pool
    to avoid blocking the async event loop.
    """
    # Get task info
    task_query = """
        SELECT t.name, t.search_query, t.is_public
        FROM tasks t
        WHERE t.id = $1
    """

    task = await db.fetch_one(task_query, task_id)

    if not task or not task["is_public"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not public",
        )

    # Generate image in thread pool to avoid blocking event loop
    # This keeps the server responsive during CPU/IO intensive operations
    image_bytes = await asyncio.to_thread(
        _generate_og_image_sync, task["name"], task["search_query"]
    )

    # Cache for 1 hour (social media crawlers will cache this)
    # TODO: Implement Redis/S3 caching for immutable images
    return Response(
        content=image_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )
