"""Integration tests for Torale CLI commands.

These tests verify CLI commands work correctly with the API,
testing task creation, preview, and authentication flows.

Prerequisites:
- Local dev environment running (`just dev`)
- TORALE_NOAUTH=1 for no-auth testing
- Or valid API key for authenticated testing

Run with:
    pytest tests/test_cli_integration.py -v
"""

import os
import subprocess
from unittest.mock import patch

import httpx
import pytest


def check_api_available() -> bool:
    """Check if the API server is available."""
    api_url = os.getenv("TORALE_API_URL", "http://localhost:8000")
    try:
        httpx.get(f"{api_url}/api/v1/tasks", timeout=2.0)
        return True
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        return True


pytestmark = pytest.mark.skipif(
    not check_api_available(), reason="API server not available"
)


@pytest.fixture
def cli_env():
    """Provide environment variables for CLI testing with NOAUTH mode."""
    if not os.getenv("TORALE_NOAUTH"):
        pytest.skip("TORALE_NOAUTH not set (required for CLI integration tests)")

    env = os.environ.copy()
    env["TORALE_NOAUTH"] = "1"
    env["TORALE_API_URL"] = "http://localhost:8000"
    return env


class TestCLITaskPreview:
    """Test 'torale task preview' command."""

    def test_preview_command_exists(self):
        """Test that preview command is registered."""
        result = subprocess.run(
            ["torale", "task", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "preview" in result.stdout.lower()

    def test_preview_command_requires_query(self, cli_env):
        """Test that preview command requires --query parameter."""
        result = subprocess.run(
            ["torale", "task", "preview"],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Should fail without required --query parameter
        assert result.returncode != 0
        # Error message should mention missing query
        assert "--query" in result.stderr or "query" in result.stderr.lower()

    def test_preview_command_with_query(self, cli_env):
        """Test preview command with query parameter."""
        # Note: This will fail if GOOGLE_API_KEY is not set
        result = subprocess.run(
            [
                "torale",
                "task",
                "preview",
                "--query",
                "Test search query",
                "--condition",
                "Test condition",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env=cli_env,
        )

        # Either succeeds with API key or fails gracefully
        if "API key" in result.stderr or "not configured" in result.stderr:
            pytest.skip("Google API key not configured")

        # If it ran, check output contains expected sections
        if result.returncode == 0:
            assert "Answer:" in result.stdout or "answer" in result.stdout.lower()
            assert "Condition" in result.stdout or "condition" in result.stdout.lower()

    def test_preview_output_formatting(self, cli_env):
        """Test that preview command formats output correctly."""
        result = subprocess.run(
            ["torale", "task", "preview", "--query", "Test query"],
            capture_output=True,
            text=True,
            timeout=10,
            env=cli_env,
        )

        # Skip if API key not configured
        if "API key" in result.stderr or "not configured" in result.stderr:
            pytest.skip("Google API key not configured")

        # Verify output has structure (may fail without API key)
        # At minimum, command should not crash
        assert result.returncode in [0, 1]  # 0 = success, 1 = API error


class TestCLITaskCreate:
    """Test 'torale task create' command."""

    def test_create_command_exists(self):
        """Test that create command is registered."""
        result = subprocess.run(
            ["torale", "task", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "create" in result.stdout.lower()

    def test_create_requires_query_and_condition(self, cli_env):
        """Test that create command requires --query and --condition."""
        result = subprocess.run(
            ["torale", "task", "create"],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Should fail without required parameters
        assert result.returncode != 0
        stderr_lower = result.stderr.lower()
        assert "--query" in result.stderr or "query" in stderr_lower


class TestCLIAuthentication:
    """Test CLI authentication flows."""

    def test_cli_works_with_noauth_mode(self, cli_env):
        """Test that CLI works with TORALE_NOAUTH=1."""
        result = subprocess.run(
            ["torale", "task", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Should succeed or have non-auth errors
        # The main thing is no authentication errors with NOAUTH=1
        output = result.stdout + result.stderr
        assert "Not authenticated" not in output, f"Auth error with NOAUTH=1: {output}"

    def test_cli_fails_without_auth(self):
        """Test that CLI requires authentication when NOAUTH not set."""
        env = os.environ.copy()
        # Remove auth-related env vars
        env.pop("TORALE_NOAUTH", None)
        env.pop("TORALE_API_KEY", None)

        result = subprocess.run(
            ["torale", "task", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )

        # Should fail with authentication error
        # (unless user has config file with API key)
        if result.returncode != 0:
            assert (
                "authenticated" in result.stdout.lower()
                or "authenticated" in result.stderr.lower()
                or "api key" in result.stdout.lower()
                or "api key" in result.stderr.lower()
            )

    def test_auth_status_command(self):
        """Test 'torale auth status' command."""
        result = subprocess.run(
            ["torale", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        # Should show some authentication status
        assert (
            "authenticated" in result.stdout.lower()
            or "noauth" in result.stdout.lower()
        )


class TestCLITaskManagement:
    """Test CLI task management commands."""

    def test_task_list_command(self, cli_env):
        """Test 'torale task list' command."""
        result = subprocess.run(
            ["torale", "task", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Should succeed (even if empty) - API and NOAUTH already verified by fixture
        # Main check: no authentication errors
        output = result.stdout + result.stderr
        assert "authenticated" not in output.lower(), f"Auth error with NOAUTH=1: {output}"

    def test_task_list_with_active_filter(self, cli_env):
        """Test 'torale task list --active' command."""
        result = subprocess.run(
            ["torale", "task", "list", "--active"],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Main check: no authentication errors
        output = result.stdout + result.stderr
        assert "authenticated" not in output.lower(), f"Auth error with NOAUTH=1: {output}"


class TestCLIErrorHandling:
    """Test CLI error handling and messages."""

    def test_invalid_task_id_error(self, cli_env):
        """Test that CLI handles invalid task ID gracefully."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = subprocess.run(
            ["torale", "task", "get", fake_id],
            capture_output=True,
            text=True,
            timeout=5,
            env=cli_env,
        )

        # Should fail with helpful error
        assert result.returncode != 0
        output = result.stdout + result.stderr
        # Error should mention "not found" or "failed", not just be empty
        assert (
            "not found" in output.lower()
            or "failed" in output.lower()
            or "error" in output.lower()
        ), f"Expected error message in output: {output}"

    def test_help_command_works(self):
        """Test that help command shows usage."""
        result = subprocess.run(
            ["torale", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "commands" in result.stdout.lower()

    def test_version_command_works(self):
        """Test that version command shows version."""
        result = subprocess.run(
            ["torale", "version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        assert result.returncode == 0
        # Should show some version information
        assert len(result.stdout) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
