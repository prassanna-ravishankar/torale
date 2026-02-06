"""Tests for error classification and user-friendly message sanitization."""

from torale.scheduler.errors import ErrorCategory, classify_error, get_user_friendly_message


def test_user_error_sanitized_invalid():
    """Verify USER_ERROR with 'invalid' keyword is sanitized."""
    error = ValueError("Invalid column 'secret_api_key' in database schema")
    category = classify_error(error)
    message = get_user_friendly_message(error, category)

    # Should NOT contain sensitive database details
    assert "secret_api_key" not in message.lower()
    assert "database" not in message.lower()
    assert "column" not in message.lower()
    # Should be generic user-friendly message
    assert "invalid data" in message.lower()


def test_user_error_sanitized_malformed():
    """Verify USER_ERROR with 'malformed' keyword is sanitized."""
    error = ValueError("Malformed JSON in field 'user_credentials'")
    category = classify_error(error)
    message = get_user_friendly_message(error, category)

    # Should NOT contain sensitive field names
    assert "user_credentials" not in message.lower()
    assert "json" not in message.lower()
    # Should be generic user-friendly message
    assert "malformed" in message.lower()


def test_user_error_fallback():
    """Verify USER_ERROR without specific keywords gets generic message."""
    error = ValueError("Something invalid but not matching patterns")
    category = ErrorCategory.USER_ERROR
    message = get_user_friendly_message(error, category)

    # Should NOT contain the raw error
    assert "something" not in message.lower()
    # Should be generic fallback message
    assert "unable to process" in message.lower() or "check your input" in message.lower()


def test_network_error_message():
    """Verify NETWORK errors get appropriate message."""
    error = ConnectionError("Connection refused to internal-api.torale.local:8080")
    category = classify_error(error)
    message = get_user_friendly_message(error, category)

    # Should NOT leak internal hostnames/ports
    assert "internal-api" not in message.lower()
    assert "8080" not in message
    # Should be user-friendly
    assert "connection" in message.lower() or "retrying" in message.lower()


def test_rate_limit_classification():
    """Verify rate limit errors are classified correctly."""
    error = Exception("429 Rate limit exceeded")
    category = classify_error(error)
    assert category == ErrorCategory.RATE_LIMIT


def test_timeout_classification():
    """Verify timeout errors are classified correctly."""
    error = TimeoutError("Request timed out after 30s")
    category = classify_error(error)
    assert category == ErrorCategory.TIMEOUT


def test_network_classification():
    """Verify network errors are classified correctly."""
    error = ConnectionError("Connection refused")
    category = classify_error(error)
    assert category == ErrorCategory.NETWORK
