"""Slug generation utilities for shareable tasks."""

from uuid import UUID, uuid4

from slugify import slugify

from torale.core.database import Database


async def generate_unique_slug(name: str, user_id: UUID, db: Database) -> str:
    """
    Generate a unique slug for a task.

    Slugs are unique per user (not globally). If a collision occurs,
    appends -2, -3, etc. until a unique slug is found.

    Optimized to fetch all matching slugs in a single query instead of
    multiple database round-trips.

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

    # Fetch all existing slugs that start with the base slug for this user in one query
    query = "SELECT slug FROM tasks WHERE user_id = $1 AND slug LIKE $2"
    existing_slugs_rows = await db.fetch_all(query, user_id, f"{base_slug}%")
    existing_slugs = {row["slug"] for row in existing_slugs_rows}

    # Find a unique slug in memory (avoids multiple DB round-trips)
    slug = base_slug
    if slug not in existing_slugs:
        return slug

    # Base slug exists, try numbered suffixes
    counter = 2
    while counter <= 1000:
        slug = f"{base_slug}-{counter}"
        if slug not in existing_slugs:
            return slug
        counter += 1

    # Safety fallback if counter exceeds 1000 (shouldn't happen in practice)
    return f"{base_slug}-{uuid4().hex[:8]}"
