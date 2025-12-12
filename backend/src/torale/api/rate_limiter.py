"""Shared rate limiter configuration for public endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global rate limiter for public endpoints (based on IP)
limiter = Limiter(key_func=get_remote_address)

# Global limiter for endpoints that need global (not per-IP) limits
global_limiter = Limiter(key_func=lambda: "global")
