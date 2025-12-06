"""Username validation and availability checking utilities."""

import re
from uuid import UUID

from torale.core.database import Database


async def validate_username(username: str, db: Database) -> tuple[bool, str]:
    """
    Validate username format and check against reserved usernames.

    Args:
        username: The username to validate
        db: Database connection for checking reserved usernames

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 30:
        return False, "Username must be 30 characters or less"

    # Must start with a letter and contain only lowercase letters, numbers, hyphens, and underscores
    if not re.match(r"^[a-z][a-z0-9_-]*$", username):
        return (
            False,
            "Username must start with a letter and contain only lowercase letters, numbers, hyphens, and underscores",
        )

    # Check against reserved usernames table (single source of truth)
    reserved = await db.fetch_one(
        "SELECT username FROM reserved_usernames WHERE username = $1",
        username,
    )
    if reserved:
        return False, "This username is reserved"

    return True, ""


async def check_username_available(
    username: str, db: Database, exclude_user_id: UUID | None = None
) -> bool:
    """
    Check if username is available.

    Args:
        username: The username to check
        db: Database connection
        exclude_user_id: Optional user ID to exclude from check (for updates)

    Returns:
        True if username is available, False otherwise
    """
    if exclude_user_id:
        result = await db.fetch_one(
            "SELECT id FROM users WHERE username = $1 AND id != $2",
            username,
            exclude_user_id,
        )
    else:
        result = await db.fetch_one(
            "SELECT id FROM users WHERE username = $1",
            username,
        )

    return result is None
