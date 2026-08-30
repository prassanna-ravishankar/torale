"""Authentication utilities and type aliases."""

from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from webwhen.core.database import Database, get_db

from .auth_provider import User, get_auth_provider

# Security scheme for Bearer token
security = HTTPBearer()

# Optional security for public endpoints
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
    db: Database = Depends(get_db),
) -> User:
    """
    Get current authenticated user.
    Delegates to the configured AuthProvider.
    """
    provider = get_auth_provider()
    return await provider.get_current_user(credentials, db)


# Type alias for production routes - requires authentication
CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
    db: Database = Depends(get_db),
) -> User:
    """
    Require admin role for accessing admin endpoints.

    This dependency:
    1. Authenticates the user (via Clerk JWT or API key)
    2. Verifies that the user has admin role (delegates to AuthProvider)

    In NoAuth mode, credentials can be None and the NoAuthProvider will
    return a test user. In production, ProductionAuthProvider will raise
    401 if credentials are missing.

    Raises:
        HTTPException: 401 if not authenticated, 403 if user is not an admin
    """
    # First authenticate the user (provider handles missing credentials)
    user = await get_current_user(credentials, db)

    # Delegate role verification to the auth provider
    provider = get_auth_provider()
    await provider.verify_role(user, "admin")

    return user


async def require_developer(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
    db: Database = Depends(get_db),
) -> User:
    """
    Require developer or admin role for accessing developer endpoints.

    This dependency:
    1. Authenticates the user (via Clerk JWT or API key)
    2. Verifies that the user has developer or admin role (delegates to AuthProvider)

    In NoAuth mode, credentials can be None and the NoAuthProvider will
    return a test user. In production, ProductionAuthProvider will raise
    401 if credentials are missing.

    Raises:
        HTTPException: 401 if not authenticated, 403 if user is not a developer or admin
    """
    # First authenticate the user (provider handles missing credentials)
    user = await get_current_user(credentials, db)

    # Delegate role verification to the auth provider
    provider = get_auth_provider()
    await provider.verify_role(user, "developer")

    return user
