"""Tests for error classification and user-friendly message sanitization."""

import asyncpg.exceptions as asyncpg_ex
import pytest

from torale.scheduler.errors import ErrorCategory, classify_error, get_user_friendly_message


class TestErrorClassification:
    """Tests for classify_error mapping."""

    @pytest.mark.parametrize(
        "error,expected_category",
        [
            (Exception("429 Rate limit exceeded"), ErrorCategory.RATE_LIMIT),
            (TimeoutError("Request timed out after 30s"), ErrorCategory.TIMEOUT),
            (ConnectionError("Connection refused"), ErrorCategory.NETWORK),
            (asyncpg_ex.PostgresConnectionError("connection lost"), ErrorCategory.NETWORK),
            (asyncpg_ex.OutOfMemoryError("out of memory"), ErrorCategory.SYSTEM_ERROR),
            (
                asyncpg_ex.InsufficientResourcesError("too many connections"),
                ErrorCategory.SYSTEM_ERROR,
            ),
        ],
        ids=[
            "rate_limit",
            "timeout",
            "connection_error",
            "asyncpg_connection",
            "asyncpg_oom",
            "asyncpg_resources",
        ],
    )
    def test_classification(self, error, expected_category):
        assert classify_error(error) == expected_category


class TestMessageSanitization:
    """Tests for get_user_friendly_message -- verifies no sensitive data leaks."""

    def test_user_error_sanitized_invalid(self):
        """USER_ERROR with 'invalid' keyword is sanitized."""
        error = ValueError("Invalid column 'secret_api_key' in database schema")
        category = classify_error(error)
        message = get_user_friendly_message(error, category)

        assert "secret_api_key" not in message.lower()
        assert "database" not in message.lower()
        assert "column" not in message.lower()
        assert "invalid data" in message.lower()

    def test_user_error_sanitized_malformed(self):
        """USER_ERROR with 'malformed' keyword is sanitized."""
        error = ValueError("Malformed JSON in field 'user_credentials'")
        category = classify_error(error)
        message = get_user_friendly_message(error, category)

        assert "user_credentials" not in message.lower()
        assert "json" not in message.lower()
        assert "malformed" in message.lower()

    def test_user_error_fallback(self):
        """USER_ERROR without specific keywords gets generic message."""
        error = ValueError("Something invalid but not matching patterns")
        category = ErrorCategory.USER_ERROR
        message = get_user_friendly_message(error, category)

        assert "something" not in message.lower()
        assert "unable to process" in message.lower() or "check your input" in message.lower()

    def test_network_error_message(self):
        """NETWORK errors do not leak internal hostnames/ports."""
        error = ConnectionError("Connection refused to internal-api.torale.local:8080")
        category = classify_error(error)
        message = get_user_friendly_message(error, category)

        assert "internal-api" not in message.lower()
        assert "8080" not in message
        assert "connection" in message.lower() or "retrying" in message.lower()
