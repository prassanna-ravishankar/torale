"""Tests for the website monitor module."""

from unittest.mock import MagicMock

import pytest


def test_get_content_hash_from_content(website_monitor):
    """Test content hash generation from HTML content."""
    # Test with simple HTML
    content = """
    <html>
        <head>
            <script>var x = 1;</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <nav>Menu items</nav>
            <div>Main content</div>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    hash1 = website_monitor.get_content_hash_from_content(content)
    assert hash1  # Hash should not be empty

    # Test that scripts and navigation are ignored
    content2 = """
    <html>
        <head>
            <script>var x = 2;</script>
            <style>body { color: blue; }</style>
        </head>
        <body>
            <nav>Different menu</nav>
            <div>Main content</div>
            <footer>Footer content</footer>
        </body>
    </html>
    """

    hash2 = website_monitor.get_content_hash_from_content(content2)
    assert hash1 == hash2  # Hashes should match as main content is same


def test_get_content_hash_from_invalid_content(website_monitor):
    """Test content hash generation with invalid HTML."""
    # Test with empty content
    assert website_monitor.get_content_hash_from_content("") == ""

    # Test with invalid HTML
    hash_ = website_monitor.get_content_hash_from_content("<invalid>")
    assert hash_  # Should return a hash even for invalid HTML


@pytest.mark.asyncio
async def test_get_content_hash(website_monitor, mock_web_server):
    """Test getting content hash from URL."""
    hash_ = await website_monitor.get_content_hash(mock_web_server)
    assert hash_  # Hash should not be empty

    # Test with same URL again
    hash2 = await website_monitor.get_content_hash(mock_web_server)
    assert hash_ == hash2  # Hashes should match for same content


@pytest.mark.asyncio
async def test_get_content_hash_invalid_url(website_monitor):
    """Test getting content hash from invalid URL."""
    hash_ = await website_monitor.get_content_hash("http://invalid.url")
    assert hash_ == ""  # Should return empty string for invalid URL


@pytest.mark.asyncio
async def test_check_relevance(website_monitor):
    """Test content relevance checking."""
    content = """
    <html>
        <body>
            <div>Latest news about artificial intelligence and machine learning</div>
        </body>
    </html>
    """
    query = "artificial intelligence news"

    # Mock the model's generate method
    mock_model = MagicMock()
    mock_model.generate = MagicMock(return_value="YES\nThis is relevant because it contains AI news.")
    website_monitor.model = mock_model

    is_relevant, explanation = await website_monitor.check_relevance(content, query)
    assert isinstance(is_relevant, bool)
    assert is_relevant is True
    assert explanation == "This is relevant because it contains AI news."


@pytest.mark.asyncio
async def test_get_content_summary(website_monitor):
    """Test content summarization."""
    content = """
    <html>
        <body>
            <div>
                Major breakthrough in quantum computing announced today.
                Scientists have achieved quantum supremacy in a new experiment.
                This could revolutionize the field of computing.
            </div>
        </body>
    </html>
    """

    # Mock the model's generate method
    mock_model = MagicMock()
    mock_model.generate = MagicMock(return_value="Scientists have achieved quantum supremacy.")
    website_monitor.model = mock_model

    summary = await website_monitor.get_content_summary(content)
    assert summary == "Scientists have achieved quantum supremacy."
    assert len(summary.split()) < len(content.split())  # Summary should be shorter


@pytest.mark.asyncio
async def test_fetch_content(website_monitor, mock_web_server):
    """Test fetching content from URL."""
    content = await website_monitor.fetch_content(mock_web_server)
    assert content  # Should have content
    assert "<html>" in content.lower()
    assert "<body>" in content.lower()

    # Test with invalid URL
    content = await website_monitor.fetch_content("http://invalid.url")
    assert content is None


@pytest.mark.asyncio
async def test_monitor_cleanup(website_monitor):
    """Test monitor cleanup."""
    # Make a request to create a session
    await website_monitor.get_content_hash("http://example.com")

    # Close the monitor
    await website_monitor.close()
    assert website_monitor._session is None or website_monitor._session.closed
