#!/usr/bin/env python3
"""End-to-end integration tests for monitoring pipeline - requires API keys"""

import os

import pytest
from dotenv import load_dotenv

from torale.pipelines.monitoring_pipeline import MonitoringPipeline
from torale.providers.gemini.schema import GeminiSchemaProvider
from torale.providers.gemini.extraction import GeminiExtractionProvider
from torale.providers.gemini.comparison import GeminiComparisonProvider
from torale.providers.gemini.search import GeminiSearchProvider

load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"),
    reason="Integration tests require GOOGLE_API_KEY"
)


class TestMonitoringPipelineE2E:
    """End-to-end tests with real Gemini API calls"""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline with real Gemini providers"""
        return MonitoringPipeline(
            schema_provider=GeminiSchemaProvider(),
            extraction_provider=GeminiExtractionProvider(),
            comparison_provider=GeminiComparisonProvider(),
        )

    @pytest.mark.asyncio
    async def test_first_execution_unreleased_product(self, pipeline):
        """Test first execution with unreleased product (iPhone 18)"""
        # Use real search provider
        search_provider = GeminiSearchProvider()
        search_result = await search_provider.search(
            "iPhone 18 release date official announcement",
            "Check if iPhone 18 is officially announced"
        )

        assert search_result["success"] is True

        # Run pipeline
        result = await pipeline.execute(
            search_query="iPhone 18 release date",
            condition_description="Check if iPhone 18 is officially announced",
            search_results=search_result["answer"],
            sources=search_result.get("grounding_sources", []),
            previous_state=None,
        )

        # Verify result structure
        assert "summary" in result
        assert "sources" in result
        assert "metadata" in result

        # First execution should indicate change
        assert result["metadata"]["changed"] is True
        assert "first execution" in result["summary"].lower()

        # Should have current_state extracted
        assert "current_state" in result["metadata"]
        current_state = result["metadata"]["current_state"]
        assert len(current_state) > 0

        # For unreleased product, should likely have is_released=False or similar
        # (exact field depends on agent-generated schema)

    @pytest.mark.asyncio
    async def test_second_execution_no_change(self, pipeline):
        """Test second execution detects no change (hash pre-filter)"""
        search_provider = GeminiSearchProvider()

        # First execution
        search_result1 = await search_provider.search(
            "What is 2+2?",
            "A numerical answer is provided"
        )

        result1 = await pipeline.execute(
            search_query="What is 2+2?",
            condition_description="A numerical answer is provided",
            search_results=search_result1["answer"],
            sources=search_result1.get("grounding_sources", []),
            previous_state=None,
        )

        previous_state = result1["metadata"]["current_state"]

        # Second execution (immediately after, should be same)
        search_result2 = await search_provider.search(
            "What is 2+2?",
            "A numerical answer is provided"
        )

        result2 = await pipeline.execute(
            search_query="What is 2+2?",
            condition_description="A numerical answer is provided",
            search_results=search_result2["answer"],
            sources=search_result2.get("grounding_sources", []),
            previous_state=previous_state,
        )

        # Should detect no change (hash pre-filter should work)
        # Note: This might fail if search results vary, but for stable queries like "2+2" should work
        assert result2["metadata"]["changed"] is False
        assert "no update" in result2["summary"].lower() or "no change" in result2["summary"].lower()

    @pytest.mark.asyncio
    async def test_released_product_with_change_detection(self, pipeline):
        """Test with released product and simulated change"""
        search_provider = GeminiSearchProvider()

        # First execution - check iPhone 16 status
        search_result1 = await search_provider.search(
            "iPhone 16 release date official",
            "Check if iPhone 16 is released"
        )

        result1 = await pipeline.execute(
            search_query="iPhone 16 release date",
            condition_description="Track iPhone 16 release status",
            search_results=search_result1["answer"],
            sources=search_result1.get("grounding_sources", []),
            previous_state=None,
        )

        # Should extract that iPhone 16 is released
        assert result1["metadata"]["changed"] is True  # First execution
        current_state = result1["metadata"]["current_state"]

        # Check that state captured release info
        # (exact fields depend on agent-generated schema)
        assert len(current_state) > 0

        # Second execution with different query (simulate checking price now)
        search_result2 = await search_provider.search(
            "iPhone 16 Pro Max pricing official",
            "Check iPhone 16 pricing"
        )

        # Use simulated "old state" where price wasn't known
        simulated_old_state = {"is_released": True, "price_usd": None}

        result2 = await pipeline.execute(
            search_query="iPhone 16 Pro Max price",
            condition_description="Track iPhone 16 pricing",
            search_results=search_result2["answer"],
            sources=search_result2.get("grounding_sources", []),
            previous_state=simulated_old_state,
        )

        # If current search found price, should detect change
        # This test verifies semantic comparison works
        assert "metadata" in result2
        assert "changed" in result2["metadata"]

    @pytest.mark.asyncio
    async def test_result_includes_all_sources(self, pipeline):
        """Test that result includes all grounding sources"""
        search_provider = GeminiSearchProvider()

        search_result = await search_provider.search(
            "Python programming language latest version",
            "What is the latest Python version?"
        )

        result = await pipeline.execute(
            search_query="Python latest version",
            condition_description="Track Python version",
            search_results=search_result["answer"],
            sources=search_result.get("grounding_sources", []),
            previous_state=None,
        )

        # Should preserve all sources from search
        assert len(result["sources"]) > 0
        assert len(result["sources"]) == len(search_result.get("grounding_sources", []))

        # Each source should have uri
        for source in result["sources"]:
            assert "uri" in source

    @pytest.mark.asyncio
    async def test_summary_is_natural_language(self, pipeline):
        """Test that summary is natural language, not JSON"""
        search_provider = GeminiSearchProvider()

        search_result = await search_provider.search(
            "What is the capital of France?",
            "Provide the capital city name"
        )

        result = await pipeline.execute(
            search_query="Capital of France",
            condition_description="Find capital city",
            search_results=search_result["answer"],
            sources=search_result.get("grounding_sources", []),
            previous_state=None,
        )

        summary = result["summary"]

        # Should be natural language
        assert isinstance(summary, str)
        assert len(summary) > 20  # Not just a few words
        assert not summary.strip().startswith("{")  # Not JSON
        assert not summary.strip().startswith("[")  # Not array

        # Should contain useful context
        assert any(word in summary.lower() for word in ["paris", "france", "capital", "city"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
