"""Authentication provider abstraction and implementations."""

import logging
import uuid
from abc import ABC, abstractmethod

import bcrypt
from clerk_backend_api import Clerk
from clerk_backend_api.security import verify_token
from clerk_backend_api.security.types import TokenVerificationError, VerifyTokenOptions
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from torale.core.config import settings
from torale.core.database import Database
from torale.repositories import ApiKeyRepository, UserRepository

logger = logging.getLogger(__name__)


class User:
    """Generic authenticated user model."""

    def __init__(
        self,
        user_id: str,
        email: str,
        email_verified: bool = False,
        db_user_id: uuid.UUID | None = None,
    ):
        """
        Initialize a User.

        Args:
            user_id: Unique identifier for the user (from auth provider)
            email: User's email address
            email_verified: Whether the email is verified
            db_user_id: Database UUID (if None, derived from user_id)
        """
        self.user_id = user_id
        self.email = email
        self.email_verified = email_verified
        # Use provided db_user_id or generate from user_id
        self.id = db_user_id or uuid.uuid5(uuid.NAMESPACE_DNS, f"auth:{user_id}")

        # Backwards compatibility: clerk_user_id alias for existing code
        self.clerk_user_id = user_id

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, email={self.email})"


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""

    @abstractmethod
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        db: Database,
    ) -> User:
        """
        Authenticate the user based on credentials.

        Args:
            credentials: The HTTP credentials (Bearer token).
            db: Database instance.

        Returns:
            User: The authenticated user.

        Raises:
            HTTPException: If authentication fails.
        """
        pass

    @abstractmethod
    async def verify_role(self, user: User, required_role: str) -> bool:
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
    """Production authentication provider using Clerk and API Keys."""

    def __init__(self):
        """Initialize the Clerk client."""
        self.clerk_client = None
        if settings.clerk_secret_key:
            self.clerk_client = Clerk(bearer_auth=settings.clerk_secret_key)

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        db: Database,
    ) -> User:
        """Authenticate user via Clerk JWT or API key."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials

        # Check if it's an API key (starts with 'sk_')
        if token.startswith("sk_"):
            return await self._verify_api_key(token, db)

        # Otherwise try Clerk JWT
        return await self._verify_clerk_token(token, db)

    async def _verify_clerk_token(self, token: str, db: Database) -> User:
        """
        Verify Clerk session token and return user information.

        Args:
            token: JWT token from Clerk
            db: Database instance

        Returns:
            User object with user information

        Raises:
            HTTPException: If token is invalid, expired, or user not found
        """
        if not settings.clerk_secret_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clerk authentication not configured",
            )

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
            if not self.clerk_client:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Clerk client not initialized",
                )

            try:
                # Fetch user directly - response is the User object
                clerk_user = self.clerk_client.users.get(user_id=clerk_user_id)

                # Get primary email
                primary_email = None
                email_verified = False

                if clerk_user and clerk_user.email_addresses:
                    for email_obj in clerk_user.email_addresses:
                        if email_obj.id == clerk_user.primary_email_address_id:
                            primary_email = email_obj.email_address
                            # Check if verification exists and status is "verified"
                            email_verified = (
                                email_obj.verification is not None
                                and email_obj.verification.status == "verified"
                            )
                            break

                if not primary_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User has no email address",
                    )

                # Fetch database user_id using repository
                user_repo = UserRepository(db)
                db_user = await user_repo.find_by_clerk_id(clerk_user_id)
                db_user_id = db_user["id"] if db_user else None

                return User(
                    user_id=clerk_user_id,
                    email=primary_email,
                    email_verified=email_verified,
                    db_user_id=db_user_id,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to fetch user from Clerk API: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch user data: {str(e)}",
                ) from e

        except TokenVerificationError as e:
            logger.warning(f"Clerk token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Clerk token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def _verify_api_key(self, api_key: str, db: Database) -> User:
        """
        Verify API key and return user information.

        Uses bcrypt for secure verification. Since bcrypt hashes include unique salts,
        we look up by key prefix and then verify the hash with bcrypt.checkpw().

        Args:
            api_key: The API key to verify
            db: Database instance

        Returns:
            User object with user information

        Raises:
            HTTPException: If API key is invalid or inactive
        """
        # Extract prefix for lookup (first 15 chars + "...")
        key_prefix = api_key[:15] + "..."

        # Look up API key by prefix
        api_key_repo = ApiKeyRepository(db)
        key_data = await api_key_repo.find_by_prefix(key_prefix)

        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify the hash using bcrypt
        stored_hash = key_data["key_hash"].encode()
        if not bcrypt.checkpw(api_key.encode(), stored_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last_used_at timestamp
        await api_key_repo.update_last_used(key_data["key_id"])

        return User(
            user_id=key_data["clerk_user_id"],
            email=key_data["email"],
            email_verified=True,  # API keys are only created for verified users
            db_user_id=key_data["user_id"],
        )

    async def verify_role(self, user: User, required_role: str) -> bool:
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
        if not self.clerk_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Clerk client not initialized",
            )

        try:
            clerk_user = self.clerk_client.users.get(user_id=user.user_id)
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
            logger.error(f"Failed to verify {required_role} role: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to verify {required_role} role",
            ) from e


# Fixed UUID for noauth test user - must match the user seeded in local dev DB
NOAUTH_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class NoAuthProvider(AuthProvider):
    """
    No-auth provider for development/testing.
    Returns a static test user and grants all roles.
    """

    def __init__(self):
        """Initialize with test user definition."""
        self.test_user = User(
            user_id="test_user_noauth",
            email=settings.torale_noauth_email,
            email_verified=True,
            db_user_id=NOAUTH_TEST_USER_ID,
        )

    async def setup(self, db: Database):
        """
        Set up the test user in the database.

        Args:
            db: Database instance for executing queries

        This creates or updates the test user in the database to ensure
        it exists for development/testing scenarios.
        """
        from pypika_tortoise import Field, Parameter, PostgreSQLQuery

        user_repo = UserRepository(db)

        # Check if test user already exists
        existing_user = await user_repo.find_by_clerk_id(self.test_user.user_id)

        if existing_user:
            # Update email if it has changed
            if existing_user["email"] != self.test_user.email:
                await user_repo.update_user(existing_user["id"], email=self.test_user.email)
        else:
            # Create new user with specific UUID using PyPika
            # (create_user doesn't support custom IDs, which we need for noauth)
            query = PostgreSQLQuery.into(user_repo.users)
            query = query.columns("id", "clerk_user_id", "email", "is_active")
            query = query.insert(Parameter("$1"), Parameter("$2"), Parameter("$3"), True)
            query = query.on_conflict("clerk_user_id").do_update(Field("email"), Parameter("$3"))

            await db.execute(
                str(query),
                NOAUTH_TEST_USER_ID,
                self.test_user.user_id,
                self.test_user.email,
            )

        logger.info(f"✓ Test user ready ({self.test_user.email})")

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        db: Database,
    ) -> User:
        """Return the test user (ignoring credentials in dev mode)."""
        return self.test_user

    async def verify_role(self, user: User, required_role: str) -> bool:
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
    """Set the global authentication provider."""
    global _auth_provider
    _auth_provider = provider


def get_auth_provider() -> AuthProvider:
    """Get the global authentication provider."""
    if _auth_provider is None:
        raise RuntimeError("AuthProvider not initialized")
    return _auth_provider
