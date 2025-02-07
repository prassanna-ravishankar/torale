"""Tests for the main AmbiAlert module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ambi_alert.main import AmbiAlert


def test_is_valid_url():
    """Test URL validation."""
    ambi = AmbiAlert()

    # Test valid URLs
    assert ambi.is_valid_url("https://example.com")
    assert ambi.is_valid_url("http://test.com/path?query=1")
    assert ambi.is_valid_url("https://sub.domain.com/path#fragment")

    # Test invalid URLs
    assert not ambi.is_valid_url("")
    assert not ambi.is_valid_url("not a url")
    assert not ambi.is_valid_url("http://")
    assert not ambi.is_valid_url("https://")


def test_expand_query():
    """Test query expansion."""
    ambi = AmbiAlert()

    # Mock the query agent
    ambi.query_agent.run = MagicMock(
        return_value=[
            "original query",
            "expanded query 1",
            "expanded query 2",
        ]
    )

    expanded = ambi.expand_query("test query")
    assert len(expanded) == 3
    assert "original query" in expanded
    assert "expanded query 1" in expanded
    assert "expanded query 2" in expanded


def test_find_relevant_urls():
    """Test finding relevant URLs."""
    ambi = AmbiAlert()

    # Mock the search agent to return URLs line by line
    ambi.search_agent.run = MagicMock(
        return_value="""https://example.com/1
https://example.com/2
not a url
https://example.com/3"""
    )

    urls = ambi.find_relevant_urls("test query")
    assert len(urls) == 3  # Should only include valid URLs
    assert all(url.startswith("https://") for url in urls)
    assert "https://example.com/1" in urls
    assert "https://example.com/2" in urls
    assert "https://example.com/3" in urls


def test_check_content_relevance():
    """Test content relevance checking."""
    ambi = AmbiAlert()

    # Mock the relevance agent
    ambi.relevance_agent.run = MagicMock(
        return_value="YES\nThis content is relevant because it contains key information.\nSummary of the changes: ..."
    )

    is_relevant, explanation = ambi.check_content_relevance(
        "test content",
        "test query",
    )

    assert is_relevant is True
    assert explanation == "This content is relevant because it contains key information.\nSummary of the changes: ..."


@pytest.mark.asyncio
async def test_add_monitoring_query():
    """Test adding a new monitoring query."""
    ambi = AmbiAlert()

    # Mock dependencies
    ambi.expand_query = MagicMock(return_value=["query 1", "query 2"])
    ambi.find_relevant_urls = MagicMock(return_value=["https://example.com"])
    ambi.monitor.fetch_content = AsyncMock(return_value="<html>content</html>")
    ambi.monitor.get_content_hash_from_content = MagicMock(return_value="hash123")
    ambi.db.add_url = AsyncMock()

    await ambi.add_monitoring_query("test query")

    # Verify interactions
    ambi.expand_query.assert_called_once()
    assert ambi.find_relevant_urls.call_count == 2  # Once for each expanded query
    ambi.monitor.fetch_content.assert_called()
    ambi.db.add_url.assert_called()


@pytest.mark.asyncio
async def test_check_for_updates():
    """Test checking for updates."""
    ambi = AmbiAlert()

    # Mock dependencies
    ambi.db.get_urls_to_check = AsyncMock(
        return_value=[
            MagicMock(
                url="https://example.com",
                query="test query",
                last_content_hash="old_hash",
                id=1,
            )
        ]
    )
    ambi.monitor.fetch_content = AsyncMock(return_value="<html>new content</html>")
    ambi.monitor.get_content_hash_from_content = MagicMock(return_value="new_hash")
    ambi.monitor.check_relevance = AsyncMock(return_value=(True, "Changes found"))
    ambi.alert_manager.send_change_alert = AsyncMock(return_value=True)
    ambi.db.update_url_check = AsyncMock()

    await ambi.check_for_updates()

    # Verify interactions
    ambi.db.get_urls_to_check.assert_called_once()
    ambi.monitor.fetch_content.assert_called_once()
    ambi.monitor.check_relevance.assert_called_once()
    ambi.alert_manager.send_change_alert.assert_called_once()
    ambi.db.update_url_check.assert_called_once()


@pytest.mark.asyncio
async def test_run_monitor():
    """Test the monitoring loop."""
    ambi = AmbiAlert(check_interval=0.1)  # Short interval for testing

    # Mock check_for_updates to run twice then raise KeyboardInterrupt
    check_count = 0

    async def mock_check():
        nonlocal check_count
        check_count += 1
        if check_count >= 2:
            raise KeyboardInterrupt

    ambi.check_for_updates = AsyncMock(side_effect=mock_check)

    # Run monitor
    await ambi.run_monitor()

    assert check_count == 2
    assert ambi.check_for_updates.call_count == 2


@pytest.mark.asyncio
async def test_context_manager():
    """Test AmbiAlert context manager."""
    async with AmbiAlert() as ambi:
        assert ambi.db._connection is not None
        # Perform some operation
        await ambi.db.add_url("https://example.com", "test", "hash123")

    # Verify cleanup
    assert ambi.db._connection is None
