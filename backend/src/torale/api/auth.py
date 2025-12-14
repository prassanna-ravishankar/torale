"""Authentication utilities and type aliases."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from torale.api.auth_provider import get_auth_provider
from torale.api.clerk_auth import ClerkUser
from torale.api.users import get_async_session

# Security scheme for Bearer token
security = HTTPBearer()

# Optional security for public endpoints
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
    session: AsyncSession = Depends(get_async_session),
) -> ClerkUser:
    """
    Get current authenticated user.
    Delegates to the configured AuthProvider.
    """
    provider = get_auth_provider()
    return await provider.get_current_user(credentials, session)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
    session: AsyncSession = Depends(get_async_session),
) -> ClerkUser | None:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work both authenticated and unauthenticated.
    """
    provider = get_auth_provider()
    try:
        return await provider.get_current_user(credentials, session)
    except HTTPException:
        # If auth fails (invalid token, etc.) or no credentials provided for production provider,
        # return None.
        # Note: NoAuthProvider always returns a user, so it won't raise HTTPException usually.
        return None


# Type alias for production routes - requires authentication
CurrentUser = Annotated[ClerkUser, Depends(get_current_user)]

# For backward compatibility or if we want to distinguish, but with the new provider pattern,
# get_current_user handles both cases based on configuration.
# We map CurrentUserOrTestUser to CurrentUser as the underlying logic is now in the provider.
CurrentUserOrTestUser = CurrentUser

# Type alias for optional auth
OptionalUser = Annotated[ClerkUser | None, Depends(get_current_user_optional)]
