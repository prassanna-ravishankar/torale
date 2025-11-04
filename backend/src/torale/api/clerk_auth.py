"""Clerk authentication integration for FastAPI."""

import uuid
from typing import Optional

from clerk_backend_sdk import Clerk
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from torale.core.config import settings

# Initialize Clerk client
clerk = Clerk(bearer_auth=settings.clerk_secret_key)

# Security scheme for Bearer token
security = HTTPBearer()


class ClerkUser:
    """User information from Clerk session."""

    def __init__(self, clerk_user_id: str, email: str, email_verified: bool = False):
        self.clerk_user_id = clerk_user_id
        self.email = email
        self.email_verified = email_verified
        # Generate a stable UUID from clerk_user_id for compatibility with existing code
        self.id = uuid.uuid5(uuid.NAMESPACE_DNS, f"clerk:{clerk_user_id}")

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
    token = credentials.credentials

    try:
        # Verify the JWT token with Clerk
        # clerk.verify_token() validates the JWT signature and expiration
        jwt_payload = clerk.verify_token(token)

        if not jwt_payload or "sub" not in jwt_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        clerk_user_id = jwt_payload["sub"]

        # Get full user information from Clerk
        user_response = clerk.users.get(user_id=clerk_user_id)

        if not user_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract email from primary email address
        primary_email = None
        email_verified = False

        if hasattr(user_response, "email_addresses") and user_response.email_addresses:
            for email_obj in user_response.email_addresses:
                # Find the primary email
                if hasattr(email_obj, "id") and email_obj.id == user_response.primary_email_address_id:
                    primary_email = email_obj.email_address
                    email_verified = getattr(email_obj, "verification", {}).get("status") == "verified"
                    break

        if not primary_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no email address",
            )

        return ClerkUser(
            clerk_user_id=clerk_user_id,
            email=primary_email,
            email_verified=email_verified,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the error in production
        print(f"Clerk token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Dependency for protected routes
async def get_current_user(user: ClerkUser = Depends(verify_clerk_token)) -> ClerkUser:
    """
    Get current authenticated user.

    This is a dependency that can be used in FastAPI routes to require authentication.

    Example:
        @app.get("/protected")
        async def protected_route(user: ClerkUser = Depends(get_current_user)):
            return {"user_id": user.clerk_user_id, "email": user.email}
    """
    return user


# Alias for compatibility with existing code that uses current_active_user
current_active_user = get_current_user
