"""
Tests for preview search endpoint.

The preview endpoint allows users to test search queries before creating tasks.
It performs grounded search and evaluates conditions without creating notifications.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest


class TestPreviewEndpoint:
    """Test suite for the preview search endpoint."""

    @pytest.mark.asyncio
    async def test_preview_with_explicit_condition(self):
        """
        Test preview endpoint with user-provided condition description.

        Scenario: User provides both query and condition.
        Expected: Returns search results without inferring condition.
        """
        import os

        from torale.api.routers.tasks import PreviewSearchRequest, preview_search

        # Skip test if GOOGLE_API_KEY not configured (pipeline requires it)
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = PreviewSearchRequest(
            search_query="When is iPhone 16 being released?",
            condition_description="A specific date is announced",
            model="gemini-2.0-flash-exp",
        )

        # Mock search result
        mock_search_result = {
            "success": True,
            "answer": "September 2024",
            "grounding_sources": [{"uri": "https://apple.com", "title": "Apple"}],
        }

        # Mock pipeline result (new MonitoringResult format)
        mock_pipeline_result = {
            "summary": "iPhone 16 will be released in September 2024",
            "sources": [{"uri": "https://apple.com", "title": "Apple"}],
            "metadata": {
                "changed": True,
                "change_explanation": "First execution",
                "current_state": {"date": "September 2024"},
            },
        }

        mock_search_provider = AsyncMock()
        mock_search_provider.search.return_value = mock_search_result

        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = mock_pipeline_result

        mock_genai_client = MagicMock()

        with patch(
            "torale.api.routers.tasks.GeminiSearchProvider", return_value=mock_search_provider
        ):
            with patch("torale.api.routers.tasks.MonitoringPipeline", return_value=mock_pipeline):
                result = await preview_search(request, mock_user, mock_genai_client)

        # Should return new format with summary
        assert result["summary"] == "iPhone 16 will be released in September 2024"
        assert result["condition_met"] is True
        assert "inferred_condition" not in result  # Condition was provided, not inferred
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_preview_with_condition_inference(self):
        """
        Test preview endpoint auto-infers condition when not provided.

        Scenario: User only provides query, no condition.
        Expected: System infers condition using LLM.
        """
        import os

        from torale.api.routers.tasks import PreviewSearchRequest, preview_search

        # Skip test if GOOGLE_API_KEY not configured (pipeline requires it)
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = PreviewSearchRequest(
            search_query="When is iPhone 16 being released?", model="gemini-2.0-flash-exp"
        )

        # Mock condition inference
        import json

        mock_response = MagicMock()
        mock_response.text = json.dumps({"condition": "A specific release date is announced"})

        mock_generate = AsyncMock(return_value=mock_response)

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        # Mock search and pipeline
        mock_search_result = {
            "success": True,
            "answer": "September 2024",
            "grounding_sources": [],
        }

        mock_pipeline_result = {
            "summary": "iPhone 16 will be released in September 2024",
            "sources": [],
            "metadata": {
                "changed": True,
                "change_explanation": "First execution",
                "current_state": {},
            },
        }

        mock_search_provider = AsyncMock()
        mock_search_provider.search.return_value = mock_search_result

        mock_pipeline = AsyncMock()
        mock_pipeline.execute.return_value = mock_pipeline_result

        with patch(
            "torale.api.routers.tasks.GeminiSearchProvider", return_value=mock_search_provider
        ):
            with patch("torale.api.routers.tasks.MonitoringPipeline", return_value=mock_pipeline):
                result = await preview_search(request, mock_user, mock_genai_client)

        # Should indicate condition was inferred
        assert "inferred_condition" in result
        assert result["inferred_condition"] == "A specific release date is announced"

    @pytest.mark.asyncio
    async def test_preview_handles_inference_failure(self):
        """
        Test preview endpoint handles condition inference failure gracefully.

        Scenario: LLM fails to infer condition.
        Expected: Returns HTTP 500 with helpful error message.
        """
        import os

        from fastapi import HTTPException

        from torale.api.routers.tasks import PreviewSearchRequest, preview_search

        # Skip test if GOOGLE_API_KEY not configured (pipeline requires it)
        if not os.getenv("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not configured")

        mock_user = MagicMock()
        mock_user.id = uuid4()

        request = PreviewSearchRequest(
            search_query="When is iPhone 16 being released?", model="gemini-2.0-flash-exp"
        )

        # Mock failing genai client
        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API error")
        )

        with pytest.raises(HTTPException) as exc_info:
            await preview_search(request, mock_user, mock_genai_client)

        assert exc_info.value.status_code == 500
        assert "Failed to automatically determine" in exc_info.value.detail


class TestConditionInference:
    """Test suite for automatic condition inference."""

    @pytest.mark.asyncio
    async def test_infer_condition_from_query(self):
        """
        Test that condition can be inferred from search query.

        Scenario: Query without explicit condition.
        Expected: LLM generates appropriate condition description.
        """
        import json

        from torale.api.routers.tasks import _infer_condition_from_query

        mock_response = MagicMock()
        mock_response.text = json.dumps({"condition": "A release date is officially announced"})

        mock_generate = AsyncMock(return_value=mock_response)

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = mock_generate

        result = await _infer_condition_from_query(
            "When is the new iPhone coming out?", "gemini-2.0-flash-exp", mock_genai_client
        )

        assert result == "A release date is officially announced"
        assert mock_generate.called

    @pytest.mark.asyncio
    async def test_inference_handles_llm_errors(self):
        """
        Test that condition inference handles LLM API errors.

        Scenario: Gemini API returns error.
        Expected: Exception is raised with context.
        """
        from torale.api.routers.tasks import _infer_condition_from_query

        mock_genai_client = MagicMock()
        mock_genai_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API rate limit")
        )

        with pytest.raises(Exception) as exc_info:
            await _infer_condition_from_query(
                "test query", "gemini-2.0-flash-exp", mock_genai_client
            )

        assert "API rate limit" in str(exc_info.value)
