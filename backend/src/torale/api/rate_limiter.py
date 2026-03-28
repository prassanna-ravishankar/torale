"""Shared rate limiter configuration for public endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_user_or_ip(request: Request) -> str:
    """Extract auth token as rate limit key for authenticated endpoints, falling back to IP."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return f"user:{auth[7:]}"
    return get_remote_address(request)


# Global rate limiter for public endpoints (based on IP)
limiter = Limiter(key_func=get_remote_address)

# Global limiter for endpoints that need global (not per-IP) limits
global_limiter = Limiter(key_func=lambda: "global")
