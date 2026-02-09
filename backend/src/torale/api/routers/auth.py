"""Authentication and user management endpoints."""

import logging
import secrets
import uuid
from datetime import UTC, datetime
from typing import Annotated

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from torale.access import (
    TEST_USER_NOAUTH_ID,
    CurrentUser,
    ProductionAuthProvider,
    get_auth_provider,
    require_developer,
)
from torale.access import (
    User as AuthUser,
)
from torale.access import (
    UserDBModel as User,
)
from torale.access.models import UserRead
from torale.core.database_alchemy import get_async_session

router = APIRouter()


class SyncUserResponse(BaseModel):
    """Response from sync-user endpoint."""

    user: UserRead
    created: bool


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_user(
    clerk_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Sync Clerk user to local database.

    Called automatically on first login from frontend.
    Creates user if doesn't exist, updates email and first_name if changed.
    """
    # Fetch full user data from Clerk to get first_name
    first_name = None
    provider = get_auth_provider()
    if isinstance(provider, ProductionAuthProvider) and provider.clerk_client:
        try:
            clerk_user_data = provider.clerk_client.users.get(user_id=clerk_user.clerk_user_id)
            first_name = clerk_user_data.first_name if clerk_user_data else None
        except Exception:
            # Continue without first_name if Clerk API fails
            pass

    # Check if user exists by clerk_user_id
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user.clerk_user_id)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # Update email and first_name if changed
        needs_update = existing_user.email != clerk_user.email or (
            first_name and existing_user.first_name != first_name
        )

        if needs_update:
            old_email = existing_user.email
            new_email = clerk_user.email

            # Update email, first_name and verified_notification_emails array
            await session.execute(
                text("""
                    UPDATE users
                    SET email = :new_email,
                        first_name = :first_name,
                        updated_at = :now,
                        verified_notification_emails = (
                            -- Remove old email from array
                            array_remove(
                                COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                                :old_email
                            )
                            ||
                            -- Add new email if not already present
                            CASE
                                WHEN :new_email = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
                                THEN ARRAY[]::TEXT[]
                                ELSE ARRAY[:new_email]::TEXT[]
                            END
                        )
                    WHERE id = :user_id
                """),
                {
                    "user_id": existing_user.id,
                    "old_email": old_email,
                    "new_email": new_email,
                    "first_name": first_name,
                    "now": datetime.now(UTC),
                },
            )
            await session.commit()
            await session.refresh(existing_user)

        return SyncUserResponse(
            user=UserRead.model_validate(existing_user),
            created=False,
        )

    # Create new user with Clerk email auto-verified
    # Handle race condition where user might be created between check and insert
    try:
        new_user_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO users (
                    id, clerk_user_id, email, first_name, is_active,
                    verified_notification_emails, created_at, updated_at
                )
                VALUES (
                    :id, :clerk_user_id, :email, :first_name, :is_active,
                    ARRAY[:email]::TEXT[], :now, :now
                )
            """),
            {
                "id": new_user_id,
                "clerk_user_id": clerk_user.clerk_user_id,
                "email": clerk_user.email,
                "first_name": first_name,
                "is_active": True,
                "now": datetime.now(UTC),
            },
        )
        await session.commit()

        # Fetch created user
        result = await session.execute(select(User).where(User.id == new_user_id))
        new_user = result.scalar_one()

        return SyncUserResponse(
            user=UserRead.model_validate(new_user),
            created=True,
        )
    except IntegrityError:
        # Race condition: user was created by another request
        # Rollback and fetch the existing user
        await session.rollback()
        result = await session.execute(
            select(User).where(User.clerk_user_id == clerk_user.clerk_user_id)
        )
        existing_user = result.scalar_one()
        return SyncUserResponse(
            user=UserRead.model_validate(existing_user),
            created=False,
        )


# API Key management
class APIKey(BaseModel):
    """API key model."""

    id: uuid.UUID
    user_id: uuid.UUID
    key_prefix: str
    name: str
    created_at: datetime
    last_used_at: datetime | None
    is_active: bool

    class Config:
        from_attributes = True


class CreateAPIKeyRequest(BaseModel):
    """Request to create new API key."""

    name: str


class CreateAPIKeyResponse(BaseModel):
    """Response with new API key (only time full key is shown)."""

    key: str
    key_info: APIKey


@router.post("/api-keys", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    clerk_user: Annotated[AuthUser, Depends(require_developer)],
    session: AsyncSession = Depends(get_async_session),
):
    """
    Generate a new API key for CLI authentication.

    Requires developer role in Clerk publicMetadata.
    Returns the full key once - store it securely!
    """
    # Get user and check for existing active key in a single query
    result = await session.execute(
        text("""
        SELECT u.id, u.clerk_user_id, u.email, COUNT(ak.id) as active_key_count
        FROM users u
        LEFT JOIN api_keys ak ON u.id = ak.user_id AND ak.is_active = true
        WHERE u.clerk_user_id = :clerk_user_id
        GROUP BY u.id, u.clerk_user_id, u.email
        """),
        {"clerk_user_id": clerk_user.clerk_user_id},
    )
    user_row = result.first()

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync user first.",
        )

    user_id, user_clerk_id, user_email, active_key_count = user_row

    if active_key_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active API key. Please revoke it before creating a new one.",
        )

    # Generate random API key
    key = f"sk_{secrets.token_urlsafe(32)}"
    # Use bcrypt for secure hashing (computationally expensive, resistant to brute force)
    key_hash = bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()
    key_prefix = key[:15] + "..."

    # Store in database
    api_key_data = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "key_prefix": key_prefix,
        "key_hash": key_hash,
        "name": request.name,
        "created_at": datetime.now(UTC),
        "is_active": True,
    }

    await session.execute(
        text("""
        INSERT INTO api_keys (id, user_id, key_prefix, key_hash, name, created_at, is_active)
        VALUES (:id, :user_id, :key_prefix, :key_hash, :name, :created_at, :is_active)
        """),
        api_key_data,
    )
    await session.commit()

    # Return full key (only time it's shown)
    return CreateAPIKeyResponse(
        key=key,
        key_info=APIKey(**api_key_data, last_used_at=None),
    )


@router.get("/api-keys", response_model=list[APIKey])
async def list_api_keys(
    clerk_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    """List all API keys for current user."""
    # Get user from database
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user.clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return []

    # Get API keys
    result = await session.execute(
        text("""
        SELECT id, user_id, key_prefix, name, created_at, last_used_at, is_active
        FROM api_keys
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        """),
        {"user_id": user.id},
    )

    keys = []
    for row in result:
        keys.append(
            APIKey(
                id=row[0],
                user_id=row[1],
                key_prefix=row[2],
                name=row[3],
                created_at=row[4],
                last_used_at=row[5],
                is_active=row[6],
            )
        )

    return keys


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    clerk_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    """Revoke (deactivate) an API key."""
    # Get user from database
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user.clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Deactivate key
    result = await session.execute(
        text("""
        UPDATE api_keys
        SET is_active = false
        WHERE id = :key_id AND user_id = :user_id
        """),
        {"key_id": key_id, "user_id": user.id},
    )
    await session.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"status": "revoked"}


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    clerk_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    """Get current user information (supports noauth mode for testing)."""
    result = await session.execute(
        select(User).where(User.clerk_user_id == clerk_user.clerk_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync user first.",
        )

    return UserRead.model_validate(user)


@router.post("/mark-welcome-seen")
async def mark_welcome_seen(
    clerk_user: CurrentUser,
):
    """Mark that the user has seen the welcome flow."""
    # Handle NoAuth mode
    if clerk_user.clerk_user_id == TEST_USER_NOAUTH_ID:
        return {"status": "success", "note": "NoAuth mode - metadata not persisted"}

    # Get auth provider and Clerk client
    provider = get_auth_provider()
    if not isinstance(provider, ProductionAuthProvider) or not provider.clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not available",
        )

    try:
        # Update user in Clerk - Clerk performs a deep merge on metadata
        # Only send the specific field to avoid race conditions
        provider.clerk_client.users.update(
            user_id=clerk_user.clerk_user_id,
            public_metadata={"has_seen_welcome": True},
        )

        return {"status": "success"}
    except Exception as e:
        # Log the full exception for debugging
        logging.exception("Failed to update user metadata")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user metadata. Please try again later.",
        ) from e
