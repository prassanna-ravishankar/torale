"""Authentication utilities and type aliases."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from torale.api.clerk_auth import (
    ClerkUser,
    _get_noauth_test_user,
    get_current_user,
    get_current_user_or_test_user,
)
from torale.core.config import settings

# Type alias for production routes - requires authentication
CurrentUser = Annotated[ClerkUser, Depends(get_current_user)]

# Type alias for test/development routes - supports TORALE_NOAUTH mode
# SECURITY WARNING: Only use CurrentUserOrTestUser for endpoints that are safe for testing!
CurrentUserOrTestUser = Annotated[ClerkUser, Depends(get_current_user_or_test_user)]

# Optional security for public endpoints
security_optional = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Security(security_optional),
) -> ClerkUser | None:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work both authenticated and unauthenticated.

    In TORALE_NOAUTH mode, returns the test user (simulates being logged in).
    """
    # In noauth mode, return test user (same as get_current_user_or_test_user)
    if settings.torale_noauth:
        return _get_noauth_test_user()

    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        # If auth fails (invalid token, etc.), return None
        # This allows public endpoints to gracefully handle missing/invalid auth
        return None


# Type alias for optional auth
OptionalUser = Annotated[ClerkUser | None, Depends(get_current_user_optional)]
