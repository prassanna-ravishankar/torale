#!/usr/bin/env python3
"""Tests for monitoring pipeline orchestration"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from torale.core.state_utils import compute_state_hash
from torale.pipelines.monitoring_pipeline import MonitoringPipeline


class TestMonitoringPipeline:
    """Test monitoring pipeline orchestration"""

    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing"""
        schema_provider = MagicMock()
        extraction_provider = MagicMock()
        comparison_provider = MagicMock()

        return {
            "schema": schema_provider,
            "extraction": extraction_provider,
            "comparison": comparison_provider,
        }

    @pytest.mark.asyncio
    async def test_first_execution_no_comparison(self, mock_providers):
        """Test first execution (no previous state) still calls comparison with None"""
        # Setup mocks
        mock_providers["schema"].get_or_create_schema = AsyncMock(
            return_value={"is_released": {"type": "boolean"}}
        )
        mock_providers["extraction"].extract = AsyncMock(return_value={"is_released": False})
        mock_providers["comparison"].compare = AsyncMock(
            return_value={
                "changed": False,
                "explanation": "First check - no previous state to compare",
            }
        )

        pipeline = MonitoringPipeline(
            schema_provider=mock_providers["schema"],
            extraction_provider=mock_providers["extraction"],
            comparison_provider=mock_providers["comparison"],
        )

        result = await pipeline.execute(
            task={
                "search_query": "iPhone 18 release date",
                "condition_description": "Check if released",
            },
            search_result={
                "answer": "No official announcement yet",
                "grounding_sources": [{"uri": "https://example.com"}],
            },
            previous_state=None,  # First execution
        )

        # Should generate schema and extract
        mock_providers["schema"].get_or_create_schema.assert_called_once()
        mock_providers["extraction"].extract.assert_called_once()

        # Should call comparison with None as previous_state
        mock_providers["comparison"].compare.assert_called_once()

        # Result should indicate first execution
        assert "first" in result.summary.lower()
        assert result.metadata["current_state"] == {"is_released": False}

    @pytest.mark.asyncio
    async def test_hash_prefilter_blocks_comparison(self, mock_providers):
        """Test hash pre-filter prevents redundant LLM comparison"""
        current_state = {"is_released": True, "release_date": "September 2024"}
        previous_state = current_state.copy()

        # Setup mocks
        mock_providers["schema"].get_or_create_schema = AsyncMock(
            return_value={"is_released": {"type": "boolean"}, "release_date": {"type": "string"}}
        )
        mock_providers["extraction"].extract = AsyncMock(return_value=current_state)

        pipeline = MonitoringPipeline(
            schema_provider=mock_providers["schema"],
            extraction_provider=mock_providers["extraction"],
            comparison_provider=mock_providers["comparison"],
        )

        result = await pipeline.execute(
            task={
                "search_query": "iPhone 16 release",
                "condition_description": "Check for changes",
            },
            search_result={
                "answer": "iPhone 16 released September 2024",
                "grounding_sources": [{"uri": "https://apple.com"}],
            },
            previous_state=previous_state,
        )

        # Should extract but NOT call comparison (hash matched)
        mock_providers["extraction"].extract.assert_called_once()
        mock_providers["comparison"].compare.assert_not_called()

        # Result should indicate no change
        assert result.metadata["changed"] is False
        assert "no change" in result.summary.lower()

    @pytest.mark.asyncio
    async def test_semantic_comparison_after_hash_diff(self, mock_providers):
        """Test semantic comparison runs when hash differs"""
        previous_state = {"is_released": False}
        current_state = {"is_released": True, "release_date": "September 2024"}

        # Setup mocks
        mock_providers["schema"].get_or_create_schema = AsyncMock(
            return_value={"is_released": {"type": "boolean"}, "release_date": {"type": "string"}}
        )
        mock_providers["extraction"].extract = AsyncMock(return_value=current_state)
        mock_providers["comparison"].compare = AsyncMock(
            return_value={
                "changed": True,
                "explanation": "Product officially released with date announced",
            }
        )

        pipeline = MonitoringPipeline(
            schema_provider=mock_providers["schema"],
            extraction_provider=mock_providers["extraction"],
            comparison_provider=mock_providers["comparison"],
        )

        result = await pipeline.execute(
            task={
                "search_query": "iPhone 16 release",
                "condition_description": "Track release status",
            },
            search_result={
                "answer": "iPhone 16 released September 2024",
                "grounding_sources": [{"uri": "https://apple.com"}],
            },
            previous_state=previous_state,
        )

        # Should call comparison (hash changed) - now takes 3 args: previous, current, schema
        schema = {"is_released": {"type": "boolean"}, "release_date": {"type": "string"}}
        mock_providers["comparison"].compare.assert_called_once()
        mock_providers["comparison"].compare.assert_called_with(
            previous_state, current_state, schema
        )

        # Result should reflect semantic change
        assert result.metadata["changed"] is True
        # Summary should mention what changed
        assert "changed" in result.summary.lower() or "released" in result.summary.lower()
        # Change explanation from comparison provider (but stored in metadata)
        assert "released" in result.metadata["change_explanation"].lower()

    @pytest.mark.asyncio
    async def test_hash_diff_but_no_semantic_change(self, mock_providers):
        """Test hash differs but semantic comparison says no meaningful change"""
        # Minor wording difference but same meaning
        previous_state = {"status": "Available now", "price": "$999"}
        current_state = {"status": "In stock now", "price": "$999"}

        # Setup mocks
        mock_providers["schema"].get_or_create_schema = AsyncMock(
            return_value={"status": {"type": "string"}, "price": {"type": "string"}}
        )
        mock_providers["extraction"].extract = AsyncMock(return_value=current_state)
        mock_providers["comparison"].compare = AsyncMock(
            return_value={
                "changed": False,
                "explanation": "Only minor wording changes, no semantic difference",
            }
        )

        pipeline = MonitoringPipeline(
            schema_provider=mock_providers["schema"],
            extraction_provider=mock_providers["extraction"],
            comparison_provider=mock_providers["comparison"],
        )

        result = await pipeline.execute(
            task={
                "search_query": "Product availability",
                "condition_description": "Track meaningful changes",
            },
            search_result={
                "answer": "Product in stock now for $999",
                "grounding_sources": [{"uri": "https://example.com"}],
            },
            previous_state=previous_state,
        )

        # Should call comparison (hash changed)
        mock_providers["comparison"].compare.assert_called_once()

        # But result should indicate no meaningful change
        assert result.metadata["changed"] is False
        assert "no change" in result.summary.lower()

    @pytest.mark.asyncio
    async def test_result_format(self, mock_providers):
        """Test result has correct MonitoringResult format"""
        mock_providers["schema"].get_or_create_schema = AsyncMock(
            return_value={"is_released": {"type": "boolean"}}
        )
        mock_providers["extraction"].extract = AsyncMock(return_value={"is_released": False})
        mock_providers["comparison"].compare = AsyncMock(
            return_value={"changed": False, "explanation": "First check"}
        )

        pipeline = MonitoringPipeline(
            schema_provider=mock_providers["schema"],
            extraction_provider=mock_providers["extraction"],
            comparison_provider=mock_providers["comparison"],
        )

        sources = [
            {"uri": "https://example.com", "title": "Test Source"},
            {"uri": "https://example2.com", "title": "Test Source 2"},
        ]

        result = await pipeline.execute(
            task={
                "search_query": "Test query",
                "condition_description": "Test condition",
            },
            search_result={
                "answer": "Test content",
                "grounding_sources": sources,
            },
            previous_state=None,
        )

        # Verify MonitoringResult structure (Pydantic BaseModel)
        assert hasattr(result, "summary")
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0

        assert hasattr(result, "sources")
        # sources might not match exactly if pipeline transforms them
        assert isinstance(result.sources, list)

        assert hasattr(result, "metadata")
        assert isinstance(result.metadata, dict)
        assert "changed" in result.metadata
        assert "current_state" in result.metadata
        assert "schema" in result.metadata


class TestStateHashing:
    """Test state hashing utilities"""

    def test_hash_deterministic(self):
        """Test hash is deterministic for same input"""
        state = {"is_released": True, "price": 999}

        hash1 = compute_state_hash(state)
        hash2 = compute_state_hash(state)

        assert hash1 == hash2

    def test_hash_different_for_different_states(self):
        """Test hash differs for different states"""
        state1 = {"is_released": True}
        state2 = {"is_released": False}

        hash1 = compute_state_hash(state1)
        hash2 = compute_state_hash(state2)

        assert hash1 != hash2

    def test_hash_order_independent(self):
        """Test hash is same regardless of key order"""
        state1 = {"a": 1, "b": 2, "c": 3}
        state2 = {"c": 3, "a": 1, "b": 2}

        hash1 = compute_state_hash(state1)
        hash2 = compute_state_hash(state2)

        assert hash1 == hash2

    def test_hash_handles_nested_dicts(self):
        """Test hash handles nested dictionaries"""
        state = {"product": {"name": "iPhone 16", "specs": {"ram": "8GB", "storage": "256GB"}}}

        hash_result = compute_state_hash(state)
        assert isinstance(hash_result, str)
        assert len(hash_result) == 16  # First 16 chars of SHA256


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
