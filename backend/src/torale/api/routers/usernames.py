"""Username management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from torale.api.auth import CurrentUserOrTestUser, OptionalUser
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
    username: str = Query(..., min_length=3, max_length=30),
    user: OptionalUser,
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
    user: CurrentUserOrTestUser,
    db: Database = Depends(get_db),
):
    """
    Set or update the current user's username (AUTH REQUIRED).

    Args:
        request: SetUsernameRequest with desired username
        user: Current authenticated user
        db: Database connection

    Returns:
        SetUsernameResponse with the new username

    Raises:
        HTTPException: If username is invalid or already taken
    """
    username = request.username.lower().strip()

    # Validate username format
    is_valid, error = await validate_username(username, db)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Check availability (exclude current user's existing username)
    available = await check_username_available(username, db, exclude_user_id=user.id)

    if not available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Update username in database
    await db.execute(
        "UPDATE users SET username = $1, updated_at = NOW() WHERE id = $2",
        username,
        user.id,
    )

    return SetUsernameResponse(username=username, updated=True)
