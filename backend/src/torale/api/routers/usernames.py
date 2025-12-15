"""Username management API endpoints."""

from asyncpg.exceptions import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from torale.api.auth import CurrentUser, OptionalUser
from torale.core.database import Database, get_db
from torale.utils.username import check_username_available, validate_username

router = APIRouter(prefix="/users", tags=["users"])


class UsernameAvailabilityResponse(BaseModel):
    """Response for username availability check."""

    available: bool
    error: str | None = None


class SetUsernameRequest(BaseModel):
    """Request to set or update username."""

    username: str = Field(..., min_length=3, max_length=30, description="Desired username")


class SetUsernameResponse(BaseModel):
    """Response after setting username."""

    username: str
    updated: bool


@router.get("/username/available", response_model=UsernameAvailabilityResponse)
async def check_username_availability(
    user: OptionalUser,
    username: str = Query(..., min_length=3, max_length=30),
    db: Database = Depends(get_db),
):
    """
    Check if a username is available (NO AUTH REQUIRED for public check).

    If authenticated, excludes the current user's username from the check,
    allowing them to keep their existing username.

    Args:
        username: The username to check

    Returns:
        UsernameAvailabilityResponse with availability status and any error message
    """
    # Validate username format
    is_valid, error = await validate_username(username, db)
    if not is_valid:
        return UsernameAvailabilityResponse(available=False, error=error)

    # Check availability in database, excluding current user if authenticated
    exclude_user_id = user.id if user else None
    available = await check_username_available(username, db, exclude_user_id=exclude_user_id)

    return UsernameAvailabilityResponse(available=available)


@router.patch("/me/username", response_model=SetUsernameResponse)
async def set_username(
    request: SetUsernameRequest,
    user: CurrentUser,
    db: Database = Depends(get_db),
):
    """
    Set the current user's username (AUTH REQUIRED).

    IMPORTANT: Username changes are NOT allowed after initial set to prevent
    breaking vanity URLs (e.g., /t/username/task-slug). Users must choose carefully.

    Args:
        request: SetUsernameRequest with desired username
        user: Current authenticated user
        db: Database connection

    Returns:
        SetUsernameResponse with the new username

    Raises:
        HTTPException: If username is invalid, already taken, or already set
    """
    # Check if user already has a username
    existing_username_query = "SELECT username FROM users WHERE id = $1"
    existing_user = await db.fetch_one(existing_username_query, user.id)

    if existing_user and existing_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username cannot be changed once set. This protects your public task URLs from breaking.",
        )

    username = request.username.lower().strip()

    # Validate username format
    is_valid, error = await validate_username(username, db)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Check availability (no need to exclude current user since we prevent changes)
    available = await check_username_available(username, db, exclude_user_id=None)

    if not available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Update username in database with race condition handling
    try:
        await db.execute(
            "UPDATE users SET username = $1, updated_at = NOW() WHERE id = $2",
            username,
            user.id,
        )
    except UniqueViolationError:
        # Handle race condition where username was taken between check and update
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        ) from None

    return SetUsernameResponse(username=username, updated=True)
