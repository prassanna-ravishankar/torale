#!/usr/bin/env python3
"""Tests for provider abstraction layer"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock settings before importing providers
with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
    from torale.providers.gemini.schema import GeminiSchemaProvider
    from torale.providers.gemini.extraction import GeminiExtractionProvider
    from torale.providers.gemini.comparison import GeminiComparisonProvider
    from torale.providers.gemini.search import GeminiSearchProvider


class TestSchemaProvider:
    """Test schema generation provider"""

    @pytest.mark.asyncio
    async def test_generate_schema_basic(self):
        """Test basic schema generation"""
        provider = GeminiSchemaProvider()

        # Mock the genai.Client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "is_released": {"type": "boolean", "description": "Whether product is released"},
            "release_date": {"type": "string", "description": "Release date if known"}
        })
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        provider.client = mock_client

        schema = await provider.generate_schema({
            "search_query": "iPhone 16 release date",
            "condition_description": "Check if iPhone 16 is officially released"
        })

        assert "is_released" in schema
        assert schema["is_released"]["type"] == "boolean"
        assert "release_date" in schema

    @pytest.mark.asyncio
    async def test_generate_schema_with_sources(self):
        """Test schema generation includes source references"""
        provider = GeminiSchemaProvider()

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "schema": {
                "price": {"type": "number", "description": "Current price"},
                "source_url": {"type": "string", "description": "Official source URL"}
            }
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.schema.genai.GenerativeModel", return_value=mock_model):
            schema = await provider.generate_schema(
                "Tesla Model 3 pricing",
                "Track Tesla Model 3 price changes",
                [{"uri": "https://tesla.com/model3"}]
            )

        assert "price" in schema or "source_url" in schema


class TestExtractionProvider:
    """Test extraction provider"""

    @pytest.mark.asyncio
    async def test_extract_with_schema(self):
        """Test structured extraction with provided schema"""
        provider = GeminiExtractionProvider()

        schema = {
            "is_released": {"type": "boolean", "description": "Whether product is released"},
            "release_date": {"type": "string", "description": "Release date"}
        }

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "is_released": True,
            "release_date": "September 20, 2024"
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.extraction.genai.GenerativeModel", return_value=mock_model):
            extracted = await provider.extract(
                "iPhone 16 was released on September 20, 2024",
                schema,
                [{"uri": "https://apple.com"}]
            )

        assert extracted["is_released"] is True
        assert "September" in extracted["release_date"]

    @pytest.mark.asyncio
    async def test_extract_handles_missing_fields(self):
        """Test extraction handles when schema fields are not found"""
        provider = GeminiExtractionProvider()

        schema = {
            "is_released": {"type": "boolean"},
            "price": {"type": "number"}
        }

        mock_model = MagicMock()
        mock_response = MagicMock()
        # Only some fields present
        mock_response.text = json.dumps({
            "is_released": False
            # price missing - not mentioned in sources
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.extraction.genai.GenerativeModel", return_value=mock_model):
            extracted = await provider.extract(
                "No pricing information available yet",
                schema,
                [{"uri": "https://example.com"}]
            )

        assert extracted["is_released"] is False
        assert "price" not in extracted or extracted["price"] is None


class TestComparisonProvider:
    """Test semantic comparison provider"""

    @pytest.mark.asyncio
    async def test_compare_detects_change(self):
        """Test comparison detects semantic changes"""
        provider = GeminiComparisonProvider()

        previous = {"is_released": False, "release_date": None}
        current = {"is_released": True, "release_date": "September 20, 2024"}

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "changed": True,
            "change_explanation": "Product has been officially released with a confirmed date"
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.comparison.genai.GenerativeModel", return_value=mock_model):
            result = await provider.compare(previous, current)

        assert result["changed"] is True
        assert "released" in result["change_explanation"].lower()

    @pytest.mark.asyncio
    async def test_compare_no_change(self):
        """Test comparison detects no meaningful change"""
        provider = GeminiComparisonProvider()

        previous = {"is_released": True, "release_date": "September 20, 2024"}
        current = {"is_released": True, "release_date": "September 20, 2024"}

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "changed": False,
            "change_explanation": "No meaningful changes detected"
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.comparison.genai.GenerativeModel", return_value=mock_model):
            result = await provider.compare(previous, current)

        assert result["changed"] is False

    @pytest.mark.asyncio
    async def test_compare_minor_wording_change(self):
        """Test comparison ignores minor wording differences"""
        provider = GeminiComparisonProvider()

        previous = {"price": "$999", "description": "Available now"}
        current = {"price": "$999", "description": "In stock now"}

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "changed": False,
            "change_explanation": "Only minor wording changes, no semantic difference"
        })
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)

        with patch("torale.providers.gemini.comparison.genai.GenerativeModel", return_value=mock_model):
            result = await provider.compare(previous, current)

        assert result["changed"] is False


class TestSearchProvider:
    """Test grounded search provider"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
    async def test_search_integration(self):
        """Integration test for grounded search (requires API key)"""
        provider = GeminiSearchProvider()

        result = await provider.search(
            "What is 2+2?",
            "A numerical answer is provided"
        )

        assert result["success"] is True
        assert "answer" in result
        assert len(result.get("grounding_sources", [])) > 0

    @pytest.mark.asyncio
    async def test_search_handles_error(self):
        """Test search handles API errors gracefully"""
        provider = GeminiSearchProvider()

        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))

        with patch("torale.providers.gemini.search.genai.GenerativeModel", return_value=mock_model):
            result = await provider.search("test query", "test condition")

        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
