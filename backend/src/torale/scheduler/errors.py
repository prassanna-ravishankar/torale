"""Error classification and retry strategy for task execution failures."""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of execution errors for different handling strategies."""

    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    NETWORK = "network"
    AGENT_ERROR = "agent_error"
    USER_ERROR = "user_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


# --- Classification patterns ---

_RATE_LIMIT_PATTERNS = ("429", "rate limit", "quota")
_TIMEOUT_PATTERNS = ("timeout", "timed out")
_NETWORK_PATTERNS = (
    "connection refused",
    "connection reset",
    "connection error",
    "failed to send",
    "all connection attempts",
)
_AGENT_PATTERNS = ("agent task failed", "agent returned error")
_USER_PATTERNS = ("invalid", "malformed")


def classify_error(error: Exception) -> ErrorCategory:
    """Classify an exception into a category for retry strategy."""
    # Check exception type first for more reliable classification
    error_type = type(error).__name__.lower()

    # Check for timeout exceptions
    if isinstance(error, TimeoutError) or "timeout" in error_type:
        return ErrorCategory.TIMEOUT

    # Check for connection exceptions
    if isinstance(error, ConnectionError) or "connection" in error_type:
        return ErrorCategory.NETWORK

    # Check for database exceptions
    if "psycopg" in error_type or "database" in error_type or "operational" in error_type:
        return ErrorCategory.SYSTEM_ERROR

    # Fall back to string pattern matching
    error_str = str(error).lower()

    if any(p in error_str for p in _RATE_LIMIT_PATTERNS):
        return ErrorCategory.RATE_LIMIT
    if any(p in error_str for p in _TIMEOUT_PATTERNS):
        return ErrorCategory.TIMEOUT
    if any(p in error_str for p in _NETWORK_PATTERNS):
        return ErrorCategory.NETWORK
    if any(p in error_str for p in _AGENT_PATTERNS):
        return ErrorCategory.AGENT_ERROR
    if any(p in error_str for p in _USER_PATTERNS):
        return ErrorCategory.USER_ERROR

    # Log when classification falls through to UNKNOWN
    logger.warning(
        f"Error classified as UNKNOWN - may need new category: "
        f"type={type(error).__name__}, message={str(error)[:200]}"
    )
    return ErrorCategory.UNKNOWN


# --- User-facing messages ---

_USER_MESSAGES: dict[ErrorCategory, str] = {
    ErrorCategory.RATE_LIMIT: "Temporarily unable to process due to high demand. We'll retry automatically.",
    ErrorCategory.TIMEOUT: "The search took longer than expected. We'll try again shortly.",
    ErrorCategory.NETWORK: "Temporary connection issue. Retrying automatically.",
    ErrorCategory.AGENT_ERROR: "Unable to complete the search. We'll try again.",
}

_DEFAULT_USER_MESSAGE = "An unexpected error occurred. We'll retry automatically."


def get_user_friendly_message(error: Exception, category: ErrorCategory) -> str:
    """Convert technical error to user-friendly message."""
    if category == ErrorCategory.USER_ERROR:
        return str(error)
    return _USER_MESSAGES.get(category, _DEFAULT_USER_MESSAGE)


# --- Retry strategy ---
# (base_seconds, multiplier, max_seconds)

_RETRY_DELAYS: dict[ErrorCategory, tuple[int, int, int]] = {
    ErrorCategory.RATE_LIMIT: (30, 4, 3600),  # 30s, 2min, 8min, 32min
    ErrorCategory.TIMEOUT: (10, 3, 300),  # 10s, 30s, 90s
    ErrorCategory.NETWORK: (10, 3, 300),  # 10s, 30s, 90s
    ErrorCategory.AGENT_ERROR: (60, 3, 900),  # 1min, 3min, 9min (capped at 15min)
}

_DEFAULT_RETRY_DELAY = (300, 3, 3600)  # 5min, 15min, 45min

_MAX_RETRIES: dict[ErrorCategory, int] = {
    ErrorCategory.RATE_LIMIT: 5,
    ErrorCategory.TIMEOUT: 3,
    ErrorCategory.NETWORK: 3,
    ErrorCategory.AGENT_ERROR: 2,
    ErrorCategory.USER_ERROR: 0,
    ErrorCategory.SYSTEM_ERROR: 1,
    ErrorCategory.UNKNOWN: 2,
}


def get_retry_delay(category: ErrorCategory, attempt: int) -> int:
    """Get retry delay in seconds based on error category and attempt number."""
    base, multiplier, cap = _RETRY_DELAYS.get(category, _DEFAULT_RETRY_DELAY)
    return min(base * (multiplier**attempt), cap)


def should_retry(category: ErrorCategory, attempt: int) -> bool:
    """Determine if error should be retried based on category and attempt count."""
    return attempt < _MAX_RETRIES.get(category, 2)
