"""Torale SDK exceptions."""


class ToraleError(Exception):
    """Base exception for all Torale SDK errors."""


class AuthenticationError(ToraleError):
    """Raised when authentication fails."""


class NotFoundError(ToraleError):
    """Raised when a resource is not found."""


class ValidationError(ToraleError):
    """Raised when request validation fails."""


class RateLimitError(ToraleError):
    """Raised when rate limit is exceeded."""


class APIError(ToraleError):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
