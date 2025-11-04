"""Clerk authentication integration for FastAPI."""

import hashlib
import uuid
from typing import Optional

from clerk_backend_api.security import verify_token
from clerk_backend_api.security.types import VerifyTokenOptions, TokenVerificationError
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.core.config import settings

# Security scheme for Bearer token
security = HTTPBearer()


class ClerkUser:
    """User information from Clerk session or API key."""

    def __init__(self, clerk_user_id: str, email: str, email_verified: bool = False, db_user_id: Optional[uuid.UUID] = None):
        self.clerk_user_id = clerk_user_id
        self.email = email
        self.email_verified = email_verified
        # Use provided db_user_id (from API key) or generate from clerk_user_id
        self.id = db_user_id or uuid.uuid5(uuid.NAMESPACE_DNS, f"clerk:{clerk_user_id}")

    def __repr__(self) -> str:
        return f"ClerkUser(clerk_user_id={self.clerk_user_id}, email={self.email})"


async def verify_clerk_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> ClerkUser:
    """
    Verify Clerk session token and return user information.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        ClerkUser object with user information

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    if not settings.clerk_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk authentication not configured",
        )

    token = credentials.credentials

    try:
        # Verify the JWT token with Clerk
        verify_options = VerifyTokenOptions(
            secret_key=settings.clerk_secret_key,
        )
        jwt_payload = verify_token(token, verify_options)

        if not jwt_payload or "sub" not in jwt_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        clerk_user_id = jwt_payload["sub"]

        # Extract email from JWT payload
        # Clerk JWT includes email in the payload
        primary_email = jwt_payload.get("email")
        email_verified = jwt_payload.get("email_verified", False)

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no email address in token",
            )

        return ClerkUser(
            clerk_user_id=clerk_user_id,
            email=primary_email,
            email_verified=email_verified,
        )

    except TokenVerificationError as e:
        print(f"Clerk token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log the error in production
        print(f"Clerk token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials,
    session: AsyncSession,
) -> ClerkUser:
    """
    Verify API key and return user information.

    Args:
        credentials: HTTP Bearer token containing API key
        session: Database session

    Returns:
        ClerkUser object with user information

    Raises:
        HTTPException: If API key is invalid or inactive
    """
    api_key = credentials.credentials
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Look up API key in database
    result = await session.execute(
        text("""
        SELECT ak.user_id, ak.id as key_id, u.clerk_user_id, u.email
        FROM api_keys ak
        JOIN users u ON ak.user_id = u.id
        WHERE ak.key_hash = :key_hash AND ak.is_active = true
        """),
        {"key_hash": key_hash},
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id, key_id, clerk_user_id, email = row

    # Update last_used_at timestamp (don't wait for commit)
    await session.execute(
        text("""
        UPDATE api_keys
        SET last_used_at = NOW()
        WHERE id = :key_id
        """),
        {"key_id": key_id},
    )
    await session.commit()

    return ClerkUser(
        clerk_user_id=clerk_user_id,
        email=email,
        email_verified=True,  # API keys are only created for verified users
        db_user_id=user_id,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> ClerkUser:
    """
    Get current authenticated user from either Clerk token or API key.

    Tries authentication methods in order:
    1. API key (if token starts with 'sk_')
    2. Clerk JWT token

    This is a dependency that can be used in FastAPI routes to require authentication.

    Example:
        @app.get("/protected")
        async def protected_route(user: ClerkUser = Depends(get_current_user)):
            return {"user_id": user.clerk_user_id, "email": user.email}
    """
    token = credentials.credentials

    # Check if it's an API key (starts with 'sk_')
    if token.startswith("sk_"):
        # Need session for API key verification
        from torale.api.users import get_async_session

        async for session in get_async_session():
            try:
                return await verify_api_key(credentials, session)
            finally:
                await session.close()

    # Otherwise try Clerk JWT
    return await verify_clerk_token(credentials)


# Alias for compatibility with existing code that uses current_active_user
current_active_user = get_current_user
