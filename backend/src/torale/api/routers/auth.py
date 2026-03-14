"""Authentication and user management endpoints."""

import secrets
import uuid
from datetime import UTC, datetime
from typing import Annotated

import asyncpg
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from torale.access import (
    TEST_USER_NOAUTH_ID,
    ApiKeyRepository,
    CurrentUser,
    ProductionAuthProvider,
    UserRepository,
    get_auth_provider,
    require_developer,
)
from torale.access import (
    User as AuthUser,
)
from torale.access.models import UserRead
from torale.core.database import Database, get_db

router = APIRouter()


class SyncUserResponse(BaseModel):
    """Response from sync-user endpoint."""

    user: UserRead
    created: bool


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_user(
    clerk_user: CurrentUser,
    db: Database = Depends(get_db),
):
    """
    Sync Clerk user to local database.

    Called automatically on first login from frontend.
    Creates user if doesn't exist, updates email and first_name if changed.
    """
    first_name = None
    provider = get_auth_provider()
    if isinstance(provider, ProductionAuthProvider) and provider.clerk_client:
        try:
            clerk_user_data = provider.clerk_client.users.get(user_id=clerk_user.clerk_user_id)
            first_name = clerk_user_data.first_name if clerk_user_data else None
        except Exception:
            pass

    user_repo = UserRepository(db)
    existing = await user_repo.find_by_clerk_id(clerk_user.clerk_user_id)

    if existing:
        needs_update = existing["email"] != clerk_user.email or (
            first_name and existing["first_name"] != first_name
        )

        if needs_update:
            old_email = existing["email"]
            new_email = clerk_user.email

            existing = await db.fetch_one(
                """
                UPDATE users
                SET email = $1,
                    first_name = $2,
                    updated_at = $3,
                    verified_notification_emails = (
                        array_remove(
                            COALESCE(verified_notification_emails, ARRAY[]::TEXT[]),
                            $4
                        )
                        ||
                        CASE
                            WHEN $1 = ANY(COALESCE(verified_notification_emails, ARRAY[]::TEXT[]))
                            THEN ARRAY[]::TEXT[]
                            ELSE ARRAY[$1]::TEXT[]
                        END
                    )
                WHERE id = $5
                RETURNING *
                """,
                new_email,
                first_name,
                datetime.now(UTC),
                old_email,
                existing["id"],
            )

        return SyncUserResponse(
            user=UserRead(**existing),
            created=False,
        )

    # Create new user with Clerk email auto-verified
    try:
        new_user = await db.fetch_one(
            """
            INSERT INTO users (
                id, clerk_user_id, email, first_name, is_active,
                verified_notification_emails, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, ARRAY[$3]::TEXT[], $6, $6)
            RETURNING *
            """,
            uuid.uuid4(),
            clerk_user.clerk_user_id,
            clerk_user.email,
            first_name,
            True,
            datetime.now(UTC),
        )

        return SyncUserResponse(
            user=UserRead(**new_user),
            created=True,
        )
    except asyncpg.UniqueViolationError:
        # Race condition: user was created by another request
        existing = await user_repo.find_by_clerk_id(clerk_user.clerk_user_id)
        return SyncUserResponse(
            user=UserRead(**existing),
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
    db: Database = Depends(get_db),
):
    """
    Generate a new API key for SDK authentication.

    Requires developer role in Clerk publicMetadata.
    Returns the full key once - store it securely!
    """
    user_row = await db.fetch_one(
        """
        SELECT u.id, u.clerk_user_id, u.email, COUNT(ak.id) as active_key_count
        FROM users u
        LEFT JOIN api_keys ak ON u.id = ak.user_id AND ak.is_active = true
        WHERE u.clerk_user_id = $1
        GROUP BY u.id, u.clerk_user_id, u.email
        """,
        clerk_user.clerk_user_id,
    )

    if not user_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync user first.",
        )

    if user_row["active_key_count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active API key. Please revoke it before creating a new one.",
        )

    key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()
    key_prefix = key[:15] + "..."

    api_key_repo = ApiKeyRepository(db)
    created = await api_key_repo.create_key(
        user_id=user_row["id"],
        key_prefix=key_prefix,
        key_hash=key_hash,
        name=request.name,
    )

    return CreateAPIKeyResponse(
        key=key,
        key_info=APIKey(
            id=created["id"],
            user_id=created["user_id"],
            key_prefix=created["key_prefix"],
            name=created["name"],
            created_at=created["created_at"],
            last_used_at=created.get("last_used_at"),
            is_active=created["is_active"],
        ),
    )


@router.get("/api-keys", response_model=list[APIKey])
async def list_api_keys(
    clerk_user: CurrentUser,
    db: Database = Depends(get_db),
):
    """List all API keys for current user."""
    user_repo = UserRepository(db)
    user = await user_repo.find_by_clerk_id(clerk_user.clerk_user_id)

    if not user:
        return []

    api_key_repo = ApiKeyRepository(db)
    rows = await api_key_repo.find_by_user(user["id"], include_inactive=True)

    return [
        APIKey(
            id=row["id"],
            user_id=row["user_id"],
            key_prefix=row["key_prefix"],
            name=row["name"],
            created_at=row["created_at"],
            last_used_at=row.get("last_used_at"),
            is_active=row["is_active"],
        )
        for row in rows
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    clerk_user: CurrentUser,
    db: Database = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    user_repo = UserRepository(db)
    user = await user_repo.find_by_clerk_id(clerk_user.clerk_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify key belongs to user and revoke
    row = await db.fetch_one(
        """
        UPDATE api_keys
        SET is_active = false, updated_at = NOW()
        WHERE id = $1 AND user_id = $2
        RETURNING id
        """,
        key_id,
        user["id"],
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"status": "revoked"}


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    clerk_user: CurrentUser,
    db: Database = Depends(get_db),
):
    """Get current user information (supports noauth mode for testing)."""
    user_repo = UserRepository(db)
    user = await user_repo.find_by_clerk_id(clerk_user.clerk_user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync user first.",
        )

    return UserRead(**user)


@router.post("/mark-welcome-seen")
async def mark_welcome_seen(
    clerk_user: CurrentUser,
    db: Database = Depends(get_db),
):
    """Mark that the user has seen the welcome flow."""
    if clerk_user.clerk_user_id == TEST_USER_NOAUTH_ID:
        await db.execute(
            "UPDATE users SET has_seen_welcome = true WHERE clerk_user_id = $1",
            clerk_user.clerk_user_id,
        )
        return {"status": "success"}

    row = await db.fetch_one(
        """
        UPDATE users SET has_seen_welcome = true
        WHERE clerk_user_id = $1
        RETURNING id
        """,
        clerk_user.clerk_user_id,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please sync user first.",
        )

    return {"status": "success"}
