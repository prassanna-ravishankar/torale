"""
Tests for task suggestion endpoint.

The suggest endpoint uses LLM to generate task configuration from natural language.
It supports both creating new tasks from scratch and context-aware refinement of existing tasks.
"""

import os
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from torale.api.routers.tasks import SuggestTaskRequest, suggest_task


class TestSuggestEndpoint:
    """Test suite for the AI-powered task suggestion endpoint."""

    @pytest.mark.asyncio
    async def test_suggest_new_task_from_scratch(self):
        """
        Test suggesting a new task from natural language prompt.

        Scenario: User provides a prompt without current task context.
        Expected: LLM generates complete task configuration.
        """
        # Skip test if GOOGLE_API_KEY not configured
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(
            prompt="Notify me when the PS5 Pro is in stock at Best Buy",
            model="gemini-2.0-flash-exp",
        )

        # Mock LLM response
        mock_response = MagicMock()
        mock_response.text = """{
            "name": "PS5 Pro Stock Monitor",
            "search_query": "PS5 Pro in stock Best Buy",
            "condition_description": "PS5 Pro is available for purchase at Best Buy",
            "schedule": "*/30 * * * *",
            "notify_behavior": "once"
        }"""

        mock_generate = AsyncMock(return_value=mock_response)

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await suggest_task(request, mock_user, mock_genai_client)

        # Verify result structure
        assert result["name"] == "PS5 Pro Stock Monitor"
        assert "PS5 Pro" in result["search_query"]
        assert "Best Buy" in result["search_query"]
        assert result["notify_behavior"] == "once"
        assert result["schedule"] == "*/30 * * * *"

        # Verify LLM was called with correct prompt
        assert mock_generate.called
        call_args = mock_generate.call_args
        assert "PS5 Pro" in str(call_args)

    @pytest.mark.asyncio
    async def test_suggest_with_context_aware_refinement(self):
        """
        Test context-aware task refinement.

        Scenario: User provides current task context and a refinement prompt.
        Expected: LLM updates task while preserving existing context.
        """
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(
            prompt="add river facing",
            current_task={
                "name": "London Apartment Monitor",
                "search_query": "apartments for sale london e2 0fq",
                "condition_description": "Price below 450000 GBP",
                "schedule": "0 9 * * *",
                "notify_behavior": "track_state",
            },
            model="gemini-2.0-flash-exp",
        )

        # Mock LLM response that preserves context
        mock_response = MagicMock()
        mock_response.text = """{
            "name": "London Apartment Monitor",
            "search_query": "apartments for sale london e2 0fq river facing",
            "condition_description": "Price below 450000 GBP",
            "schedule": "0 9 * * *",
            "notify_behavior": "track_state"
        }"""

        mock_generate = AsyncMock(return_value=mock_response)

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await suggest_task(request, mock_user, mock_genai_client)

        # Verify context was preserved
        assert result["name"] == "London Apartment Monitor"
        assert "e2 0fq" in result["search_query"]
        assert "river facing" in result["search_query"]
        assert result["condition_description"] == "Price below 450000 GBP"
        assert result["schedule"] == "0 9 * * *"

        # Verify LLM received current task context
        call_args = mock_generate.call_args
        assert "Current Task Configuration" in str(call_args)
        assert "london e2 0fq" in str(call_args)

    @pytest.mark.asyncio
    async def test_suggest_handles_llm_errors(self):
        """
        Test that suggest endpoint handles LLM API errors gracefully.

        Scenario: Gemini API returns error.
        Expected: Returns HTTP 500 with helpful error message.
        """
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(prompt="Test prompt", model="gemini-2.0-flash-exp")

        # Mock failing genai client
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )

        with pytest.raises(HTTPException) as exc_info:
            await suggest_task(request, mock_user, mock_genai_client)

        assert exc_info.value.status_code == 500
        assert "Failed to generate task suggestion" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_suggest_handles_invalid_json_response(self):
        """
        Test that suggest endpoint handles malformed LLM responses.

        Scenario: LLM returns invalid JSON.
        Expected: Returns HTTP 500 with error message.
        """
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(prompt="Test prompt", model="gemini-2.0-flash-exp")

        # Mock LLM response with invalid JSON
        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON"

        mock_generate = AsyncMock(return_value=mock_response)

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        with pytest.raises(HTTPException) as exc_info:
            await suggest_task(request, mock_user, mock_genai_client)

        assert exc_info.value.status_code == 500


class TestSuggestPromptGeneration:
    """Test suite for prompt generation logic."""

    @pytest.mark.asyncio
    async def test_prompt_includes_context_when_provided(self):
        """
        Test that generated prompt includes current task context.

        Scenario: User provides current_task in request.
        Expected: Prompt includes "Current Task Configuration" section.
        """
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(
            prompt="add river facing",
            current_task={
                "name": "Apartment Monitor",
                "search_query": "apartments london",
                "condition_description": "Price below 500k",
                "schedule": "0 9 * * *",
                "notify_behavior": "track_state",
            },
            model="gemini-2.0-flash-exp",
        )

        mock_response = MagicMock()
        mock_response.text = '{"name": "Test", "search_query": "test", "condition_description": "test", "schedule": "0 9 * * *", "notify_behavior": "once"}'

        mock_generate = AsyncMock(return_value=mock_response)
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        await suggest_task(request, mock_user, mock_genai_client)

        # Verify prompt structure
        call_args = mock_generate.call_args
        prompt_text = str(call_args)
        assert "Current Task Configuration" in prompt_text
        assert "apartments london" in prompt_text
        assert "add river facing" in prompt_text

    @pytest.mark.asyncio
    async def test_prompt_excludes_context_when_not_provided(self):
        """
        Test that generated prompt doesn't include context when creating new task.

        Scenario: User doesn't provide current_task.
        Expected: Prompt uses "User Description" format.
        """
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = SuggestTaskRequest(prompt="Monitor PS5 stock", model="gemini-2.0-flash-exp")

        mock_response = MagicMock()
        mock_response.text = '{"name": "Test", "search_query": "test", "condition_description": "test", "schedule": "0 9 * * *", "notify_behavior": "once"}'

        mock_generate = AsyncMock(return_value=mock_response)
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        await suggest_task(request, mock_user, mock_genai_client)

        # Verify prompt structure
        call_args = mock_generate.call_args
        prompt_text = str(call_args)
        assert "User Description" in prompt_text
        assert "Current Task Configuration" not in prompt_text

    @pytest.mark.asyncio
    async def test_suggest_digest_tasks_get_always_behavior(self):
        """
        Test that periodic digest tasks correctly suggest 'always' notify behavior.

        Scenario: User wants daily/weekly/monthly digests or summaries.
        Expected: System instruction guides LLM to use 'always' (not 'once').

        This is a regression test for Issue #5 where digests were incorrectly
        getting 'once' behavior. The system instruction now explicitly guides
        the LLM to use 'always' for DAILY/WEEKLY/MONTHLY patterns.
        """
        mock_user = MagicMock()
        mock_user.id = uuid4()

        # Test that system instruction includes digest guidance
        request = SuggestTaskRequest(
            prompt="weekly digest of ai news", model="gemini-2.0-flash-exp"
        )

        # Mock response with 'always' behavior
        mock_response = MagicMock()
        mock_response.text = """{
            "name": "AI News Weekly",
            "search_query": "weekly digest of ai news",
            "condition_description": "New weekly AI news digest available",
            "schedule": "0 9 * * 1",
            "notify_behavior": "always"
        }"""

        mock_generate = AsyncMock(return_value=mock_response)
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await suggest_task(request, mock_user, mock_genai_client)

        # Verify notify_behavior is 'always' for digests
        assert result["notify_behavior"] == "always", (
            f"Expected 'always' for digest, got '{result['notify_behavior']}'"
        )

        # Verify system instruction includes explicit digest guidance
        call_args = mock_generate.call_args
        prompt_text = str(call_args)
        assert "DAILY/WEEKLY/MONTHLY" in prompt_text, (
            "System instruction should include 'DAILY/WEEKLY/MONTHLY' guidance for digests"
        )
        assert "use 'always'" in prompt_text.lower(), (
            "System instruction should explicitly say to use 'always' for digests"
        )
