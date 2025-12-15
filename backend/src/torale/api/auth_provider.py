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

    @abstractmethod
    async def verify_role(self, user: ClerkUser, required_role: str) -> bool:
        """
        Verify if the user has the required role.

        Args:
            user: The authenticated user.
            required_role: The role to verify (e.g., "admin", "developer").

        Returns:
            bool: True if user has the required role.

        Raises:
            HTTPException: If role verification fails or user lacks the role.
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

    async def verify_role(self, user: ClerkUser, required_role: str) -> bool:
        """
        Verify if the user has the required role by checking Clerk public metadata.

        Args:
            user: The authenticated user.
            required_role: The role to verify (e.g., "admin", "developer").

        Returns:
            bool: True if user has the required role.

        Raises:
            HTTPException: If Clerk client not available or role verification fails.
        """
        from torale.core.config import settings

        # Import clerk_client
        from torale.api.clerk_auth import clerk_client

        if not clerk_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clerk client not initialized",
            )

        try:
            clerk_user = clerk_client.users.get(user_id=user.clerk_user_id)
            public_metadata = clerk_user.public_metadata or {}
            role = public_metadata.get("role")

            # For developer role, accept both "developer" and "admin"
            if required_role == "developer":
                if role not in ["developer", "admin"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Developer access required. Please contact support to enable API access.",
                    )
            else:
                # For other roles (like "admin"), require exact match
                if role != required_role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"{required_role.capitalize()} access required",
                    )

            return True

        except HTTPException:
            raise
        except Exception as e:
            print(f"Failed to verify {required_role} role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify {required_role} role",
            ) from e


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

    async def verify_role(self, user: ClerkUser, required_role: str) -> bool:
        """
        In no-auth mode, always grant all roles for development/testing.

        Args:
            user: The authenticated user (test user in no-auth mode).
            required_role: The role to verify (ignored in no-auth mode).

        Returns:
            bool: Always True in no-auth mode.
        """
        # In development mode, grant all roles
        return True


# Global instance, to be set at startup
_auth_provider: AuthProvider | None = None


def set_auth_provider(provider: AuthProvider):
    global _auth_provider
    _auth_provider = provider


def get_auth_provider() -> AuthProvider:
    if _auth_provider is None:
        raise RuntimeError("AuthProvider not initialized")
    return _auth_provider
