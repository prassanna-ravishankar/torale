"""Tests for the rate limiter module."""

import asyncio
import time

import pytest

from ambi_alert.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiting functionality."""
    limiter = RateLimiter(rate=2)  # 2 requests per minute

    # First two requests should be immediate
    start = time.time()
    await limiter.acquire()
    await limiter.acquire()
    duration = time.time() - start

    assert duration < 0.1  # Should be near-instant


@pytest.mark.asyncio
async def test_rate_limiter_throttling():
    """Test that rate limiter properly throttles requests."""
    limiter = RateLimiter(rate=2)  # 2 requests per minute

    # Use up the initial tokens
    await limiter.acquire()
    await limiter.acquire()

    # Third request should be delayed
    start = time.time()
    await limiter.acquire()
    duration = time.time() - start

    # Should wait about 30 seconds (60 seconds / 2 requests per minute)
    assert duration >= 29  # Allow for small timing variations


@pytest.mark.asyncio
async def test_rate_limiter_concurrent():
    """Test rate limiter with concurrent requests."""
    limiter = RateLimiter(rate=2)  # 2 requests per minute

    async def make_request(id_):
        await limiter.acquire()
        return id_

    # Start 4 concurrent requests
    start = time.time()
    results = await asyncio.gather(
        make_request(1),
        make_request(2),
        make_request(3),
        make_request(4),
    )
    duration = time.time() - start

    # First two should be immediate, next two should each wait ~30 seconds
    assert duration >= 59  # Allow for small timing variations
    assert results == [1, 2, 3, 4]  # Order should be preserved


@pytest.mark.asyncio
async def test_rate_limiter_high_rate():
    """Test rate limiter with a high rate limit."""
    limiter = RateLimiter(rate=1000)  # 1000 requests per minute

    # Multiple requests should be near-instant
    start = time.time()
    for _ in range(10):
        await limiter.acquire()
    duration = time.time() - start

    assert duration < 0.1  # Should be very quick


@pytest.mark.asyncio
async def test_rate_limiter_zero_rate():
    """Test rate limiter with zero rate (should raise error)."""
    with pytest.raises(ValueError):
        RateLimiter(rate=0)


@pytest.mark.asyncio
async def test_rate_limiter_negative_rate():
    """Test rate limiter with negative rate (should raise error)."""
    with pytest.raises(ValueError):
        RateLimiter(rate=-1)
