"""Rate limiting module."""

import asyncio
import time


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: int, per: int = 60):
        """Initialize rate limiter.

        Args:
            rate: Number of requests allowed per time period
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary.

        This implements a simple token bucket algorithm.
        """
        async with self._lock:
            while self.tokens <= 0:
                now = time.monotonic()
                time_passed = now - self.last_update
                self.tokens = min(self.rate, self.tokens + (time_passed * self.rate / self.per))
                self.last_update = now
                if self.tokens <= 0:
                    await asyncio.sleep(self.per / self.rate)

            self.tokens -= 1
