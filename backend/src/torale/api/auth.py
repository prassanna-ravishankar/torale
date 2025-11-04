"""Authentication utilities and type aliases."""

from typing import Annotated

from fastapi import Depends

from torale.api.clerk_auth import ClerkUser, get_current_user

# Type alias for dependency injection
# This maintains compatibility with existing code while using Clerk
CurrentUser = Annotated[ClerkUser, Depends(get_current_user)]
