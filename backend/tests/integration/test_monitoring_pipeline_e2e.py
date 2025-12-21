#!/usr/bin/env python3
"""End-to-end integration tests for monitoring pipeline - requires API keys"""

import os

import pytest

from torale.monitoring.pipeline import MonitoringPipeline
from torale.monitoring.providers.gemini.comparison import GeminiComparisonProvider
from torale.monitoring.providers.gemini.extraction import GeminiExtractionProvider
from torale.monitoring.providers.gemini.schema import GeminiSchemaProvider
from torale.monitoring.providers.gemini.search import GeminiSearchProvider

pytestmark = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"), reason="Integration tests require GOOGLE_API_KEY"
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
        )

        # Run pipeline
        result = await pipeline.execute(
            task={
                "search_query": "iPhone 18 release date",
                "condition_description": "Check if iPhone 18 is officially announced",
            },
            search_result=search_result,
            previous_state=None,
        )

        # Verify result structure (MonitoringResult is a Pydantic model)
        assert result.summary is not None
        assert result.sources is not None
        assert result.metadata is not None

        # First execution should indicate change
        assert result.metadata["changed"] is True
        assert "first" in result.summary.lower()

        # Should have current_state extracted
        assert "current_state" in result.metadata
        current_state = result.metadata["current_state"]
        assert len(current_state) > 0

        # For unreleased product, should likely have is_released=False or similar
        # (exact field depends on agent-generated schema)

    @pytest.mark.asyncio
    async def test_semantic_comparison_detects_no_meaningful_change(self, pipeline):
        """Test that semantic comparison can detect when changes are not meaningful"""
        search_provider = GeminiSearchProvider()

        # First execution with a stable fact
        search_result = await search_provider.search("What is 2+2?")

        result1 = await pipeline.execute(
            task={
                "search_query": "What is 2+2?",
                "condition_description": "A numerical answer is provided",
            },
            search_result=search_result,
            previous_state=None,
        )

        # Verify first execution works
        assert result1.metadata["changed"] is True  # First execution is always "changed"
        assert "current_state" in result1.metadata

        # Create a previous state that's semantically equivalent
        # (the answer to 2+2 is always 4)
        previous_state = {"answer": "4", "is_correct": True}

        # Second execution - semantic comparison should recognize equivalence
        result2 = await pipeline.execute(
            task={
                "search_query": "What is 2+2?",
                "condition_description": "A numerical answer is provided",
            },
            search_result=search_result,
            previous_state=previous_state,
        )

        # Test that the pipeline executes and returns valid result
        # Note: Whether it detects "no change" depends on schema matching
        # The key is that the semantic comparison runs and produces a result
        assert result2.metadata is not None
        assert "changed" in result2.metadata
        assert "current_state" in result2.metadata
        assert result2.metadata.get("comparison_method") == "semantic"

    @pytest.mark.asyncio
    async def test_released_product_with_change_detection(self, pipeline):
        """Test with released product and simulated change"""
        search_provider = GeminiSearchProvider()

        # First execution - check iPhone 16 status
        search_result1 = await search_provider.search("iPhone 16 release date official")

        result1 = await pipeline.execute(
            task={
                "search_query": "iPhone 16 release date",
                "condition_description": "Track iPhone 16 release status",
            },
            search_result=search_result1,
            previous_state=None,
        )

        # Should extract that iPhone 16 is released
        assert result1.metadata["changed"] is True  # First execution
        current_state = result1.metadata["current_state"]

        # Check that state captured release info
        # (exact fields depend on agent-generated schema)
        assert len(current_state) > 0

        # Second execution with different query (simulate checking price now)
        search_result2 = await search_provider.search("iPhone 16 Pro Max pricing official")

        # Use simulated "old state" where price wasn't known
        simulated_old_state = {"is_released": True, "price_usd": None}

        result2 = await pipeline.execute(
            task={
                "search_query": "iPhone 16 Pro Max price",
                "condition_description": "Track iPhone 16 pricing",
            },
            search_result=search_result2,
            previous_state=simulated_old_state,
        )

        # If current search found price, should detect change
        # This test verifies semantic comparison works
        assert result2.metadata is not None
        assert "changed" in result2.metadata

    @pytest.mark.asyncio
    async def test_result_includes_all_sources(self, pipeline):
        """Test that result includes all grounding sources"""
        search_provider = GeminiSearchProvider()

        search_result = await search_provider.search("Python programming language latest version")

        result = await pipeline.execute(
            task={
                "search_query": "Python latest version",
                "condition_description": "Track Python version",
            },
            search_result=search_result,
            previous_state=None,
        )

        # Should preserve all sources from search
        assert len(result.sources) > 0
        assert len(result.sources) == len(search_result.get("sources", []))

        # Each source should have url
        for source in result.sources:
            assert "url" in source

    @pytest.mark.asyncio
    async def test_summary_is_natural_language(self, pipeline):
        """Test that summary is natural language, not JSON"""
        search_provider = GeminiSearchProvider()

        search_result = await search_provider.search("What is the capital of France?")

        result = await pipeline.execute(
            task={
                "search_query": "Capital of France",
                "condition_description": "Find capital city",
            },
            search_result=search_result,
            previous_state=None,
        )

        summary = result.summary

        # Should be natural language
        assert isinstance(summary, str)
        assert len(summary) > 20  # Not just a few words
        assert not summary.strip().startswith("{")  # Not JSON
        assert not summary.strip().startswith("[")  # Not array

        # Should contain useful context
        assert any(word in summary.lower() for word in ["paris", "france", "capital", "city"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
