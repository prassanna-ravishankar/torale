from abc import ABC, abstractmethod

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from torale.api.clerk_auth import (
    ClerkUser,
    _get_noauth_test_user,
    verify_api_key,
    verify_clerk_token,
)


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        session: AsyncSession,
    ) -> ClerkUser:
        """
        Authenticate the user based on credentials.

        Args:
            credentials: The HTTP credentials (Bearer token).
            session: Database session.

        Returns:
            ClerkUser: The authenticated user.

        Raises:
            HTTPException: If authentication fails.
        """
        pass


class ProductionAuthProvider(AuthProvider):
    """
    Production authentication provider using Clerk and API Keys.
    """

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        session: AsyncSession,
    ) -> ClerkUser:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials

        # Check if it's an API key (starts with 'sk_')
        if token.startswith("sk_"):
            # Use injected session
            return await verify_api_key(credentials, session)

        # Otherwise try Clerk JWT
        return await verify_clerk_token(credentials, session)


class NoAuthProvider(AuthProvider):
    """
    No-auth provider for development/testing.
    Returns a static test user.
    """

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        session: AsyncSession,
    ) -> ClerkUser:
        # In no-auth mode, we ignore credentials and session, returning the test user
        return _get_noauth_test_user()


# Global instance, to be set at startup
_auth_provider: AuthProvider | None = None


def set_auth_provider(provider: AuthProvider):
    global _auth_provider
    _auth_provider = provider


def get_auth_provider() -> AuthProvider:
    if _auth_provider is None:
        raise RuntimeError("AuthProvider not initialized")
    return _auth_provider
