"""
Tests for task suggestion endpoint.

The suggest endpoint uses the torale-agent (via A2A JSON-RPC) to generate
task configuration from natural language.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.tasks import SuggestTaskRequest, suggest_task


class TestSuggestEndpoint:
    """Test suite for the AI-powered task suggestion endpoint."""

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_suggest_new_task_from_scratch(self, mock_call_agent):
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.return_value = {
            "name": "PS5 Pro Stock Monitor",
            "search_query": "PS5 Pro in stock Best Buy",
            "condition_description": "PS5 Pro is available for purchase at Best Buy",
            "schedule": "*/30 * * * *",
            "notify_behavior": "once",
        }

        request = SuggestTaskRequest(
            prompt="Notify me when the PS5 Pro is in stock at Best Buy",
        )

        result = await suggest_task(request, mock_user)

        assert result.name == "PS5 Pro Stock Monitor"
        assert "PS5 Pro" in result.search_query
        assert result.notify_behavior == "once"

        # Verify agent was called with prompt containing user description
        prompt_arg = mock_call_agent.call_args[0][0]
        assert "PS5 Pro" in prompt_arg
        assert "User Description" in prompt_arg

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_suggest_with_context_aware_refinement(self, mock_call_agent):
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.return_value = {
            "name": "London Apartment Monitor",
            "search_query": "apartments for sale london e2 0fq river facing",
            "condition_description": "Price below 450000 GBP",
            "schedule": "0 9 * * *",
            "notify_behavior": "track_state",
        }

        request = SuggestTaskRequest(
            prompt="add river facing",
            current_task={
                "name": "London Apartment Monitor",
                "search_query": "apartments for sale london e2 0fq",
                "condition_description": "Price below 450000 GBP",
                "schedule": "0 9 * * *",
                "notify_behavior": "track_state",
            },
        )

        result = await suggest_task(request, mock_user)

        assert result.name == "London Apartment Monitor"
        assert "river facing" in result.search_query
        assert "e2 0fq" in result.search_query

        # Verify prompt includes current task context
        prompt_arg = mock_call_agent.call_args[0][0]
        assert "Current Task Configuration" in prompt_arg
        assert "london e2 0fq" in prompt_arg

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_suggest_handles_agent_errors(self, mock_call_agent):
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.side_effect = RuntimeError("Agent task failed")

        request = SuggestTaskRequest(prompt="Test prompt")

        with pytest.raises(HTTPException) as exc_info:
            await suggest_task(request, mock_user)

        assert exc_info.value.status_code == 500
        assert "Failed to generate task suggestion" in exc_info.value.detail


class TestSuggestPromptGeneration:
    """Test suite for prompt generation logic."""

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_prompt_includes_context_when_provided(self, mock_call_agent):
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.return_value = {
            "name": "Test",
            "search_query": "test",
            "condition_description": "test",
            "schedule": "0 9 * * *",
            "notify_behavior": "once",
        }

        request = SuggestTaskRequest(
            prompt="add river facing",
            current_task={
                "name": "Apartment Monitor",
                "search_query": "apartments london",
                "condition_description": "Price below 500k",
                "schedule": "0 9 * * *",
                "notify_behavior": "track_state",
            },
        )

        await suggest_task(request, mock_user)

        prompt_arg = mock_call_agent.call_args[0][0]
        assert "Current Task Configuration" in prompt_arg
        assert "apartments london" in prompt_arg
        assert "add river facing" in prompt_arg

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_prompt_excludes_context_when_not_provided(self, mock_call_agent):
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.return_value = {
            "name": "Test",
            "search_query": "test",
            "condition_description": "test",
            "schedule": "0 9 * * *",
            "notify_behavior": "once",
        }

        request = SuggestTaskRequest(prompt="Monitor PS5 stock")

        await suggest_task(request, mock_user)

        prompt_arg = mock_call_agent.call_args[0][0]
        assert "User Description" in prompt_arg
        assert "Current Task Configuration" not in prompt_arg

    @pytest.mark.asyncio
    @patch("torale.api.routers.tasks.call_agent", new_callable=AsyncMock)
    async def test_suggest_digest_tasks_get_always_behavior(self, mock_call_agent):
        """Regression test: digest tasks should use 'always' notify behavior."""
        mock_user = MagicMock()
        mock_user.id = uuid4()

        mock_call_agent.return_value = {
            "name": "AI News Weekly",
            "search_query": "weekly digest of ai news",
            "condition_description": "New weekly AI news digest available",
            "schedule": "0 9 * * 1",
            "notify_behavior": "always",
        }

        request = SuggestTaskRequest(prompt="weekly digest of ai news")

        result = await suggest_task(request, mock_user)

        assert result.notify_behavior == "always"

        # Verify prompt includes digest guidance
        prompt_arg = mock_call_agent.call_args[0][0]
        assert "always" in prompt_arg.lower()
