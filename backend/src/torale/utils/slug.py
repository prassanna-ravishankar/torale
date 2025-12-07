"""Slug generation utilities for shareable tasks."""

from uuid import UUID, uuid4

from slugify import slugify

from torale.core.database import Database


async def generate_unique_slug(name: str, user_id: UUID, db: Database) -> str:
    """
    Generate a unique slug for a task.

    Slugs are unique per user (not globally). If a collision occurs,
    appends -2, -3, etc. until a unique slug is found.

    Args:
        name: Task name to slugify
        user_id: User ID who owns the task
        db: Database connection

    Returns:
        Unique slug for the task
    """
    # Generate base slug from task name
    base_slug = slugify(name, max_length=50)

    # If slugify returns empty (e.g., all special chars), use a default
    if not base_slug:
        base_slug = "task"

    slug = base_slug
    counter = 2

    # Keep trying until we find a unique slug for this user
    while True:
        # Check if slug exists for this user
        result = await db.fetch_one(
            "SELECT id FROM tasks WHERE user_id = $1 AND slug = $2",
            user_id,
            slug,
        )

        if not result:
            return slug

        # Collision detected, try next number
        slug = f"{base_slug}-{counter}"
        counter += 1

        # Safety check to prevent infinite loop (shouldn't happen in practice)
        if counter > 1000:
            # Fallback to UUID-based slug
            return f"{base_slug}-{uuid4().hex[:8]}"
