"""Test that 429 errors trigger paid tier fallback."""

from unittest.mock import AsyncMock, patch

import pytest
from a2a.client.errors import A2AClientHTTPError
from a2a.types import TaskState

from tests.conftest import data_artifact, make_a2a_task, poll_success, send_success
from torale.scheduler.agent import call_agent
from torale.scheduler.models import MonitoringResponse


@pytest.mark.asyncio
class TestPaidTierFallback:
    """Test automatic fallback to paid tier on 429 errors."""

    @patch("torale.scheduler.agent.settings")
    async def test_429_triggers_paid_tier_fallback(self, mock_settings):
        """When free tier returns 429, should automatically try paid tier."""
        mock_settings.agent_url_free = "http://agent-free:8000"
        mock_settings.agent_url_paid = "http://agent-paid:8000"

        completed_task = make_a2a_task(
            task_id="task-paid-123",
            artifacts=[
                data_artifact({
                    "evidence": "Test evidence",
                    "sources": ["http://example.com"],
                    "confidence": 95,
                    "next_run": None,
                    "notification": "Test notification",
                })
            ],
        )

        with patch("torale.scheduler.agent.A2AClient") as mock_client_class:
            # First call (free tier) raises 429
            free_client = AsyncMock()
            free_client.send_message = AsyncMock(
                side_effect=A2AClientHTTPError(429, "Rate limit exceeded")
            )

            # Second call (paid tier) succeeds
            paid_client = AsyncMock()
            paid_client.send_message = AsyncMock(
                return_value=send_success(
                    make_a2a_task(task_id="task-paid-123", status_state=TaskState.submitted)
                )
            )
            paid_client.get_task = AsyncMock(return_value=poll_success(completed_task))

            # Return different clients based on url kwarg
            def get_client(**kwargs):
                url = kwargs.get("url", "")
                if "free" in url:
                    return free_client
                return paid_client

            mock_client_class.side_effect = get_client

            result = await call_agent("test prompt")

            assert isinstance(result, MonitoringResponse)
            assert result.evidence == "Test evidence"
            assert result.notification == "Test notification"

            # Verify both clients were created
            assert mock_client_class.call_count == 2
            # First call should be to free tier
            assert "free" in mock_client_class.call_args_list[0][1]["url"]
            # Second call should be to paid tier
            assert "paid" in mock_client_class.call_args_list[1][1]["url"]

    @patch("torale.scheduler.agent.settings")
    async def test_non_429_error_does_not_fallback(self, mock_settings):
        """Non-429 errors should not trigger paid tier fallback."""
        mock_settings.agent_url_free = "http://agent-free:8000"
        mock_settings.agent_url_paid = "http://agent-paid:8000"

        with patch("torale.scheduler.agent.A2AClient") as mock_client_class:
            # Free tier raises 503 (not 429)
            free_client = AsyncMock()
            free_client.send_message = AsyncMock(
                side_effect=A2AClientHTTPError(503, "Service unavailable")
            )

            mock_client_class.return_value = free_client

            # Should raise RuntimeError (wrapped 503), not try paid tier
            with pytest.raises(RuntimeError, match="Failed to send task to agent"):
                await call_agent("test prompt")

            # Verify only free tier was tried
            assert mock_client_class.call_count == 1
            assert "free" in mock_client_class.call_args[1]["url"]

    @patch("torale.scheduler.agent.settings")
    async def test_429_during_poll_propagates(self, mock_settings):
        """429 during polling should not trigger fallback (already submitted)."""
        mock_settings.agent_url_free = "http://agent-free:8000"
        mock_settings.agent_url_paid = "http://agent-paid:8000"

        with patch("torale.scheduler.agent.A2AClient") as mock_client_class:
            # Free tier send succeeds, but poll gets 429
            client = AsyncMock()
            client.send_message = AsyncMock(
                return_value=send_success(
                    make_a2a_task(task_id="task-123", status_state=TaskState.submitted)
                )
            )
            # Poll raises 429 (unusual but possible)
            client.get_task = AsyncMock(
                side_effect=A2AClientHTTPError(429, "Rate limit during poll")
            )

            mock_client_class.return_value = client

            # Should raise RuntimeError after max consecutive poll failures
            with pytest.raises(RuntimeError, match="Agent poll failed"):
                await call_agent("test prompt")

            # Should only create one client (free tier)
            assert mock_client_class.call_count == 1

    @patch("torale.scheduler.agent.settings")
    async def test_both_tiers_429_propagates_error(self, mock_settings):
        """If both free and paid tiers return 429, error should propagate."""
        mock_settings.agent_url_free = "http://agent-free:8000"
        mock_settings.agent_url_paid = "http://agent-paid:8000"

        with patch("torale.scheduler.agent.A2AClient") as mock_client_class:
            # Both free and paid return 429
            client = AsyncMock()
            client.send_message = AsyncMock(
                side_effect=A2AClientHTTPError(429, "Rate limit exceeded")
            )

            mock_client_class.return_value = client

            # Should raise A2AClientHTTPError from paid tier
            with pytest.raises(A2AClientHTTPError) as exc_info:
                await call_agent("test prompt")

            assert exc_info.value.status_code == 429

            # Should try both tiers
            assert mock_client_class.call_count == 2
