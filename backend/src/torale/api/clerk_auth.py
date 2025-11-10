"""Clerk authentication integration for FastAPI."""

import hashlib
import uuid

from clerk_backend_api import Clerk
from clerk_backend_api.security import verify_token
from clerk_backend_api.security.types import TokenVerificationError, VerifyTokenOptions
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.core.config import settings

# Security scheme for Bearer token
security = HTTPBearer()

# Initialize Clerk client
clerk_client = None
if settings.clerk_secret_key:
    clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)


class ClerkUser:
    """User information from Clerk session or API key."""

    def __init__(
        self,
        clerk_user_id: str,
        email: str,
        email_verified: bool = False,
        db_user_id: uuid.UUID | None = None,
    ):
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

        # Fetch user data from Clerk API to get email
        # JWT payload doesn't include email by default
        if not clerk_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clerk client not initialized",
            )

        try:
            # Fetch user directly - response is the User object
            user = clerk_client.users.get(user_id=clerk_user_id)

            # Get primary email
            primary_email = None
            email_verified = False

            if user and user.email_addresses:
                for email_obj in user.email_addresses:
                    if email_obj.id == user.primary_email_address_id:
                        primary_email = email_obj.email_address
                        # Check if verification exists and has status
                        email_verified = bool(email_obj.verification)
                        break

            if not primary_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User has no email address",
                )

            # Fetch database user_id
            from torale.api.users import get_async_session

            db_user_id = None
            async for session in get_async_session():
                try:
                    result = await session.execute(
                        text("SELECT id FROM users WHERE clerk_user_id = :clerk_user_id"),
                        {"clerk_user_id": clerk_user_id},
                    )
                    row = result.first()
                    if row:
                        db_user_id = row[0]
                    break
                finally:
                    await session.close()

            return ClerkUser(
                clerk_user_id=clerk_user_id,
                email=primary_email,
                email_verified=email_verified,
                db_user_id=db_user_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            print(f"Failed to fetch user from Clerk API: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch user data: {str(e)}",
            ) from e

    except TokenVerificationError as e:
        print(f"Clerk token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        # Log the error in production
        print(f"Clerk token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


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


async def get_current_user_or_test_user(
    credentials: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False)),
) -> ClerkUser:
    """
    Get current user with support for TORALE_NOAUTH test mode.

    SECURITY WARNING: Only use this in test/development routes!
    Production routes MUST use get_current_user() instead.

    When TORALE_NOAUTH=1:
    - Returns a test user without authentication
    - Should ONLY be used in local development/testing

    When TORALE_NOAUTH=0 (default):
    - Requires proper authentication (same as get_current_user)
    """
    # If noauth mode is enabled, return test user
    if settings.torale_noauth:
        print("⚠️  WARNING: TORALE_NOAUTH mode enabled - authentication bypassed!")
        # Return a test user with a fixed UUID
        return ClerkUser(
            clerk_user_id="test_user_noauth",
            email=settings.torale_noauth_email,
            email_verified=True,
            db_user_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        )

    # In production mode, require authentication
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Use normal authentication
    token = credentials.credentials

    if token.startswith("sk_"):
        from torale.api.users import get_async_session

        async for session in get_async_session():
            try:
                return await verify_api_key(credentials, session)
            finally:
                await session.close()

    return await verify_clerk_token(credentials)


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> ClerkUser:
    """
    Require admin role for accessing admin endpoints.

    This dependency:
    1. Authenticates the user (via Clerk JWT or API key)
    2. Fetches the user's public metadata from Clerk
    3. Verifies that publicMetadata.role === "admin"

    Raises:
        HTTPException: 403 if user is not an admin

    Example:
        @router.get("/admin/stats")
        async def get_stats(admin: ClerkUser = Depends(require_admin)):
            return {"message": "Admin access granted"}
    """
    # First authenticate the user
    user = await get_current_user(credentials)

    # Fetch user's public metadata from Clerk to check role
    if not clerk_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk client not initialized",
        )

    try:
        clerk_user = clerk_client.users.get(user_id=user.clerk_user_id)

        # Check if user has admin role in publicMetadata
        public_metadata = clerk_user.public_metadata or {}
        if public_metadata.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"Failed to verify admin role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify admin role",
        ) from e
