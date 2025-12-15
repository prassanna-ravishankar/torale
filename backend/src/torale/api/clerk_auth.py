"""Clerk authentication integration for FastAPI."""

import hashlib
import logging
import uuid

from clerk_backend_api import Clerk
from clerk_backend_api.security import verify_token
from clerk_backend_api.security.types import TokenVerificationError, VerifyTokenOptions
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.core.config import settings

logger = logging.getLogger(__name__)

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
    credentials: HTTPAuthorizationCredentials,
    session: AsyncSession,
) -> ClerkUser:
    """
    Verify Clerk session token and return user information.

    Args:
        credentials: HTTP Bearer token from Authorization header
        session: Database session.

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
            db_user_id = None

            result = await session.execute(
                text("SELECT id FROM users WHERE clerk_user_id = :clerk_user_id"),
                {"clerk_user_id": clerk_user_id},
            )
            row = result.first()
            if row:
                db_user_id = row[0]

            return ClerkUser(
                clerk_user_id=clerk_user_id,
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
        # Log the error in production
        logger.error(f"Clerk token verification error: {e}")
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


# Fixed UUID for noauth test user - must match the user seeded in local dev DB
NOAUTH_TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _get_noauth_test_user() -> ClerkUser:
    """
    Get the test user for TORALE_NOAUTH mode.

    Single source of truth for the test user - used by NoAuthProvider.
    """
    return ClerkUser(
        clerk_user_id="test_user_noauth",
        email=settings.torale_noauth_email,
        email_verified=True,
        db_user_id=NOAUTH_TEST_USER_ID,
    )
