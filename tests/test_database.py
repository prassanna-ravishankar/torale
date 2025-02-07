"""Tests for the database module."""

import pytest

from ambi_alert.database import MonitoredURL


@pytest.mark.asyncio
async def test_add_url(db_manager):
    """Test adding a URL to the database."""
    url = "https://example.com"
    query = "test query"
    content_hash = "abc123"

    await db_manager.add_url(url, query, content_hash)

    # Verify URL was added
    urls = await db_manager.get_urls_to_check()
    assert len(urls) == 1
    assert urls[0].url == url
    assert urls[0].query == query
    assert urls[0].last_content_hash == content_hash


@pytest.mark.asyncio
async def test_get_urls_to_check(db_manager):
    """Test retrieving URLs to check."""
    # Add multiple URLs
    urls = [
        ("https://example1.com", "query1", "hash1"),
        ("https://example2.com", "query2", "hash2"),
    ]

    for url, query, content_hash in urls:
        await db_manager.add_url(url, query, content_hash)

    # Verify all URLs are retrieved
    monitored_urls = await db_manager.get_urls_to_check()
    assert len(monitored_urls) == 2

    # Verify URL objects have correct data
    assert isinstance(monitored_urls[0], MonitoredURL)
    assert monitored_urls[0].url == urls[0][0]
    assert monitored_urls[1].url == urls[1][0]


@pytest.mark.asyncio
async def test_update_url_check(db_manager):
    """Test updating URL check information."""
    # Add a URL
    url = "https://example.com"
    query = "test query"
    old_hash = "old_hash"
    await db_manager.add_url(url, query, old_hash)

    # Get the URL's ID
    urls = await db_manager.get_urls_to_check()
    url_id = urls[0].id

    # Update with new hash
    new_hash = "new_hash"
    await db_manager.update_url_check(url_id, new_hash)

    # Verify update
    updated_urls = await db_manager.get_urls_to_check()
    assert updated_urls[0].last_content_hash == new_hash
    assert updated_urls[0].last_check > urls[0].last_check


@pytest.mark.asyncio
async def test_get_all_urls(db_manager):
    """Test retrieving all URLs with their queries and hashes."""
    # Add multiple URLs
    urls = [
        ("https://example1.com", "query1", "hash1"),
        ("https://example2.com", "query2", "hash2"),
    ]

    for url, query, content_hash in urls:
        await db_manager.add_url(url, query, content_hash)

    # Get all URLs
    all_urls = await db_manager.get_all_urls()
    assert len(all_urls) == 2

    # Verify data format
    for (url, query, hash_), (exp_url, exp_query, exp_hash) in zip(all_urls, urls):
        assert url == exp_url
        assert query == exp_query
        assert hash_ == exp_hash


@pytest.mark.asyncio
async def test_update_url_hash(db_manager):
    """Test updating URL hash directly."""
    # Add a URL
    url = "https://example.com"
    query = "test query"
    old_hash = "old_hash"
    await db_manager.add_url(url, query, old_hash)

    # Update hash
    new_hash = "new_hash"
    await db_manager.update_url_hash(url, new_hash)

    # Verify update
    all_urls = await db_manager.get_all_urls()
    assert all_urls[0][2] == new_hash  # Check hash in (url, query, hash) tuple


@pytest.mark.asyncio
async def test_database_context_manager(db_manager):
    """Test database context manager functionality."""
    async with db_manager as db:
        # Add a URL within context
        await db.add_url("https://example.com", "test", "hash")

        # Verify URL was added
        urls = await db.get_urls_to_check()
        assert len(urls) == 1

    # Verify connection is closed after context
    assert db._connection is None
