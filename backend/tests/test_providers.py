#!/usr/bin/env python3
"""Tests for provider abstraction layer"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock settings before importing providers
with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}):
    from torale.providers.gemini.comparison import GeminiComparisonProvider
    from torale.providers.gemini.extraction import GeminiExtractionProvider
    from torale.providers.gemini.schema import GeminiSchemaProvider
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
        mock_response.text = json.dumps(
            {
                "is_released": {"type": "boolean", "description": "Whether product is released"},
                "release_date": {"type": "string", "description": "Release date if known"},
            }
        )
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        provider.client = mock_client

        schema = await provider.generate_schema(
            {
                "search_query": "iPhone 16 release date",
                "condition_description": "Check if iPhone 16 is officially released",
            }
        )

        assert "is_released" in schema
        assert schema["is_released"]["type"] == "boolean"
        assert "release_date" in schema

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_generate_schema_with_sources(self):
        """Test schema generation includes source references (integration test)"""
        provider = GeminiSchemaProvider()

        schema = await provider.generate_schema(
            {
                "search_query": "Tesla Model 3 pricing",
                "condition_description": "Track Tesla Model 3 price changes",
            }
        )

        # Verify schema has expected structure
        assert isinstance(schema, dict)
        assert len(schema) > 0
        # Schema should have field definitions
        for _field_name, field_def in schema.items():
            assert isinstance(field_def, dict)


class TestExtractionProvider:
    """Test extraction provider"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_extract_with_schema(self):
        """Test structured extraction with provided schema (integration test)"""
        provider = GeminiExtractionProvider()

        schema = {
            "answer": {"type": "string", "description": "The numerical answer"},
        }

        search_result = {
            "answer": "The answer to 2+2 is 4",
            "grounding_sources": [{"uri": "https://example.com"}],
        }

        extracted = await provider.extract(search_result, schema)

        # Verify extraction returns dict with schema fields
        assert isinstance(extracted, dict)
        assert "answer" in extracted

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_extract_handles_missing_fields(self):
        """Test extraction handles when schema fields are not found (integration test)"""
        provider = GeminiExtractionProvider()

        schema = {
            "is_released": {"type": "boolean", "description": "Product release status"},
            "price": {"type": "number", "description": "Product price"},
        }

        search_result = {
            "answer": "No pricing information available yet. Release status unknown.",
            "grounding_sources": [{"uri": "https://example.com"}],
        }

        extracted = await provider.extract(search_result, schema)

        # Verify extraction returns dict
        assert isinstance(extracted, dict)


class TestComparisonProvider:
    """Test semantic comparison provider"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_compare_detects_change(self):
        """Test comparison detects semantic changes (integration test)"""
        provider = GeminiComparisonProvider()

        previous = {"answer": "2+2 equals 3"}
        current = {"answer": "2+2 equals 4"}
        schema = {"answer": {"type": "string", "description": "The numerical answer"}}

        result = await provider.compare(previous, current, schema)

        # Verify result structure
        assert isinstance(result, dict)
        assert "changed" in result
        assert "explanation" in result

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_compare_no_change(self):
        """Test comparison detects no meaningful change (integration test)"""
        provider = GeminiComparisonProvider()

        previous = {"answer": "2+2 equals 4"}
        current = {"answer": "2+2 equals 4"}
        schema = {"answer": {"type": "string", "description": "The numerical answer"}}

        result = await provider.compare(previous, current, schema)

        # Verify result structure
        assert isinstance(result, dict)
        assert "changed" in result
        assert "explanation" in result
        # Likely should detect no change
        assert result["changed"] is False

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_compare_minor_wording_change(self):
        """Test comparison ignores minor wording differences (integration test)"""
        provider = GeminiComparisonProvider()

        previous = {"description": "Available now"}
        current = {"description": "In stock now"}
        schema = {"description": {"type": "string", "description": "Availability status"}}

        result = await provider.compare(previous, current, schema)

        # Verify result structure
        assert isinstance(result, dict)
        assert "changed" in result
        assert "explanation" in result


class TestSearchProvider:
    """Test grounded search provider"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires GOOGLE_API_KEY")
    async def test_search_integration(self):
        """Integration test for grounded search (requires API key)"""
        provider = GeminiSearchProvider()

        result = await provider.search("What is 2+2?", "A numerical answer is provided")

        assert result["success"] is True
        assert "answer" in result
        assert len(result.get("grounding_sources", [])) > 0

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"), reason="Integration test - requires GOOGLE_API_KEY"
    )
    async def test_search_handles_error(self):
        """Test search handles API errors gracefully (integration test)"""
        provider = GeminiSearchProvider()

        # Mock the client to raise an error
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API Error"))
        provider.client = mock_client

        result = await provider.search("test query")

        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
