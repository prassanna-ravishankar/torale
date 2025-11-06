"""Authentication utilities and type aliases."""

from typing import Annotated

from fastapi import Depends

from torale.api.clerk_auth import ClerkUser, get_current_user, get_current_user_or_test_user

# Type alias for production routes - requires authentication
CurrentUser = Annotated[ClerkUser, Depends(get_current_user)]

# Type alias for test/development routes - supports TORALE_NOAUTH mode
# SECURITY WARNING: Only use CurrentUserOrTestUser for endpoints that are safe for testing!
CurrentUserOrTestUser = Annotated[ClerkUser, Depends(get_current_user_or_test_user)]
