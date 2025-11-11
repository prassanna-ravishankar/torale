"""
Torale SDK - Python client for the Torale API.

Beautiful, Pythonic API for creating and managing monitoring tasks.
"""

from __future__ import annotations

from torale.sdk.builders import MonitorBuilder, monitor
from torale.sdk.client import ToraleClient
from torale.sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ToraleError,
    ValidationError,
)
from torale.sdk.resources import TasksResource


class Torale(ToraleClient):
    """
    Main Torale SDK client.

    Provides access to all Torale API resources with both traditional
    resource-based API and fluent builder patterns.

    Example (Traditional API):
        >>> from torale import Torale
        >>> client = Torale(api_key="sk_...")
        >>> task = client.tasks.create(
        ...     name="iPhone Monitor",
        ...     search_query="When is iPhone 16 being released?",
        ...     condition_description="A specific release date is announced",
        ...     notifications=[{"type": "webhook", "url": "https://myapp.com/alert"}]
        ... )

    Example (Fluent API):
        >>> from torale import monitor
        >>> task = (monitor("When is iPhone 16 being released?")
        ...     .when("A specific release date is announced")
        ...     .notify(webhook="https://myapp.com/alert")
        ...     .create())
    """

    def __init__(
        self, api_key: str | None = None, api_url: str | None = None, timeout: float = 60.0
    ):
        """
        Initialize Torale SDK client.

        Args:
            api_key: API key for authentication. If not provided, will try to load from:
                1. TORALE_API_KEY environment variable
                2. ~/.torale/config.json file
            api_url: Base URL for API. Defaults to http://localhost:8000 or value from config.
            timeout: Request timeout in seconds. Defaults to 60.

        Example:
            >>> # Using API key from environment
            >>> client = Torale()
            >>> # Or provide explicitly
            >>> client = Torale(api_key="sk_...")
            >>> # Or for local development without auth
            >>> import os
            >>> os.environ["TORALE_NOAUTH"] = "1"
            >>> client = Torale()
        """
        super().__init__(api_key=api_key, api_url=api_url, timeout=timeout)

        # Initialize resources
        self.tasks = TasksResource(self)

    def monitor(self, search_query: str) -> MonitorBuilder:
        """
        Create a monitoring task with fluent API.

        Args:
            search_query: Query to monitor

        Returns:
            MonitorBuilder for chaining

        Example:
            >>> client = Torale()
            >>> task = (client.monitor("Bitcoin price")
            ...     .when("price exceeds $50,000")
            ...     .check_every("5 minutes")
            ...     .notify(webhook="https://myapp.com/crypto-alert")
            ...     .create())
        """
        return MonitorBuilder(self, search_query)


__all__ = [
    "Torale",
    "monitor",
    "MonitorBuilder",
    "TasksResource",
    "ToraleError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "APIError",
]
