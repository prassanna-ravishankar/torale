"""Async Torale SDK client."""

from __future__ import annotations

import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import httpx

from torale.sdk.exceptions import APIError, AuthenticationError, NotFoundError, ValidationError


class ToraleAsyncClient:
    """
    Async client for interacting with the Torale API.

    Handles authentication, request/response processing, and error handling.
    Supports async/await patterns for non-blocking I/O.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float = 60.0,
    ):
        """
        Initialize async Torale client.

        Args:
            api_key: API key for authentication. If not provided, will try to load from:
                1. TORALE_API_KEY environment variable
                2. ~/.torale/config.json file
            api_url: Base URL for API. Defaults to https://api.torale.ai or value from config.
                     For local development, set TORALE_DEV=1 to use http://localhost:8000
            timeout: Request timeout in seconds. Defaults to 60.

        Raises:
            AuthenticationError: If no API key can be found and TORALE_NOAUTH is not set.
        """
        # Check for no-auth mode (local development)
        self.noauth_mode = os.getenv("TORALE_NOAUTH") == "1"
        # Check for dev mode (local development with auth)
        self.dev_mode = os.getenv("TORALE_DEV") == "1"

        if not self.noauth_mode:
            # Try to get API key from various sources
            self.api_key = api_key or self._load_api_key()

            if not self.api_key:
                raise AuthenticationError(
                    "No API key provided. Set TORALE_API_KEY environment variable, "
                    "pass api_key parameter, or run `torale auth set-api-key` to configure."
                )
        else:
            self.api_key = None

        # Get API URL
        self.api_url = api_url or self._load_api_url()

        # Create HTTP client
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.http_client = httpx.AsyncClient(
            base_url=self.api_url, headers=headers, timeout=timeout, follow_redirects=True
        )

    def _load_api_key(self) -> str | None:
        """Load API key from environment or config file."""
        # Try environment variable first
        api_key = os.getenv("TORALE_API_KEY")
        if api_key:
            return api_key

        # Try config file
        config_path = Path.home() / ".torale" / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get("api_key")
            except (OSError, JSONDecodeError):
                pass

        return None

    def _load_api_url(self) -> str:
        """Load API URL from environment or config file."""
        # Try environment variable first (highest priority)
        api_url = os.getenv("TORALE_API_URL")
        if api_url:
            return api_url

        # Dev/NoAuth mode takes precedence over config file
        # This allows --local flag to override saved config
        if self.dev_mode or self.noauth_mode:
            return "http://localhost:8000"

        # Try config file (lower priority than dev mode)
        config_path = Path.home() / ".torale" / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    if "api_url" in config:
                        return config["api_url"]
            except (OSError, JSONDecodeError):
                pass

        # Default to production
        return "https://api.torale.ai"

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_data = None
            try:
                error_data = response.json()
            except json.JSONDecodeError:
                pass

            status_code = response.status_code

            if status_code == 401:
                detail = error_data.get("detail") if error_data else "Unauthorized"
                raise AuthenticationError(detail) from e
            elif status_code == 404:
                detail = error_data.get("detail") if error_data else "Not found"
                raise NotFoundError(detail) from e
            elif status_code in (400, 422):
                detail = error_data.get("detail") if error_data else "Validation error"
                raise ValidationError(detail) from e
            else:
                detail = error_data.get("detail") if error_data else str(e)
                raise APIError(detail, status_code=status_code, response=error_data) from e

        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise APIError("Failed to decode JSON response") from e

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Make GET request."""
        response = await self.http_client.get(path, params=params)
        return self._handle_response(response)

    async def post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make POST request."""
        response = await self.http_client.post(path, json=json)
        return self._handle_response(response)

    async def put(self, path: str, json: dict[str, Any] | None = None) -> Any:
        """Make PUT request."""
        response = await self.http_client.put(path, json=json)
        return self._handle_response(response)

    async def delete(self, path: str) -> Any:
        """Make DELETE request."""
        response = await self.http_client.delete(path)
        # DELETE may return 204 No Content
        if response.status_code == 204:
            return None
        return self._handle_response(response)

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
