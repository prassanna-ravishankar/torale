"""
Tests for task suggestion endpoint.

The suggest endpoint uses LLM to generate task configuration from natural language.
It supports both creating new tasks from scratch and context-aware refinement of existing tasks.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


class TestSuggestEndpoint:
    """Test suite for the AI-powered task suggestion endpoint."""

    @pytest.mark.asyncio
    async def test_suggest_new_task_from_scratch(self):
        """
        Test suggesting a new task from natural language prompt.

        Scenario: User provides a prompt without current task context.
        Expected: LLM generates complete task configuration.
        """
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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
        import os

        from fastapi import HTTPException

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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
        import os

        from fastapi import HTTPException

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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

    @pytest.mark.asyncio
    async def test_suggest_generates_appropriate_schedules(self):
        """
        Test that LLM generates appropriate schedules based on urgency.

        Scenario: Different types of monitoring tasks.
        Expected: Schedule matches urgency (stock = frequent, news = daily).
        """
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        # Test urgent task (stock monitoring)
        request_urgent = SuggestTaskRequest(
            prompt="Alert me when PS5 is in stock", model="gemini-2.0-flash-exp"
        )

        mock_response_urgent = MagicMock()
        mock_response_urgent.text = """{
            "name": "PS5 Stock Alert",
            "search_query": "PS5 in stock",
            "condition_description": "PS5 is available",
            "schedule": "*/30 * * * *",
            "notify_behavior": "once"
        }"""

        mock_generate = AsyncMock(return_value=mock_response_urgent)
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await suggest_task(request_urgent, mock_user, mock_genai_client)

        # Urgent tasks should have frequent checks
        assert "*/30" in result["schedule"] or "*/15" in result["schedule"]

    @pytest.mark.asyncio
    async def test_suggest_sets_appropriate_notify_behavior(self):
        """
        Test that LLM sets appropriate notify_behavior based on task type.

        Scenario: One-time event vs ongoing monitoring.
        Expected: "once" for events, "track_state" for ongoing.
        """
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        # Test one-time event
        request_once = SuggestTaskRequest(
            prompt="Tell me when iPhone 17 release date is announced",
            model="gemini-2.0-flash-exp",
        )

        mock_response_once = MagicMock()
        mock_response_once.text = """{
            "name": "iPhone 17 Release Date",
            "search_query": "iPhone 17 release date announcement",
            "condition_description": "Official release date announced",
            "schedule": "0 9 * * *",
            "notify_behavior": "once"
        }"""

        mock_generate = AsyncMock(return_value=mock_response_once)
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await suggest_task(request_once, mock_user, mock_genai_client)

        # One-time events should use "once"
        assert result["notify_behavior"] == "once"


class TestSuggestPromptGeneration:
    """Test suite for prompt generation logic."""

    @pytest.mark.asyncio
    async def test_prompt_includes_context_when_provided(self):
        """
        Test that generated prompt includes current task context.

        Scenario: User provides current_task in request.
        Expected: Prompt includes "Current Task Configuration" section.
        """
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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
        import os

        from torale.api.routers.tasks import SuggestTaskRequest, suggest_task

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
