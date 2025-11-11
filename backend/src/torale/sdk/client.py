"""Torale SDK client."""

from __future__ import annotations

import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import httpx

from torale.sdk.exceptions import APIError, AuthenticationError, NotFoundError, ValidationError


class ToraleClient:
    """
    Base client for interacting with the Torale API.

    Handles authentication, request/response processing, and error handling.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        timeout: float = 60.0,
    ):
        """
        Initialize Torale client.

        Args:
            api_key: API key for authentication. If not provided, will try to load from:
                1. TORALE_API_KEY environment variable
                2. ~/.torale/config.json file
            api_url: Base URL for API. Defaults to http://localhost:8000 or value from config.
            timeout: Request timeout in seconds. Defaults to 60.

        Raises:
            AuthenticationError: If no API key can be found and TORALE_NOAUTH is not set.
        """
        # Check for no-auth mode (local development)
        self.noauth_mode = os.getenv("TORALE_NOAUTH") == "1"

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

        self.http_client = httpx.Client(
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
                # OSError covers IOError, PermissionError, etc.
                # JSONDecodeError for malformed JSON
                # Config file is optional, so ignore if it's missing, malformed, or unreadable
                pass

        return None

    def _load_api_url(self) -> str:
        """Load API URL from environment or config file."""
        # Try environment variable first
        api_url = os.getenv("TORALE_API_URL")
        if api_url:
            return api_url

        # Try config file
        config_path = Path.home() / ".torale" / "config.json"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get("api_url", "http://localhost:8000")
            except (OSError, JSONDecodeError):
                # OSError covers IOError, PermissionError, etc.
                # JSONDecodeError for malformed JSON
                # Config file is optional, so ignore if it's missing, malformed, or unreadable
                pass

        return "http://localhost:8000"

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Try to parse error response
            error_data = None  # Initialize to ensure it's always defined
            try:
                error_data = response.json()
                error_message = error_data.get("detail", str(e))
            except Exception:
                error_message = str(e)

            # Raise appropriate exception based on status code
            if response.status_code == 401:
                raise AuthenticationError(error_message) from e
            elif response.status_code == 404:
                raise NotFoundError(error_message) from e
            elif response.status_code == 400 or response.status_code == 422:
                raise ValidationError(error_message) from e
            else:
                raise APIError(
                    error_message, status_code=response.status_code, response=error_data
                ) from e

        # Return JSON response
        return response.json()

    def get(self, path: str, **kwargs) -> Any:
        """Make GET request."""
        response = self.http_client.get(path, **kwargs)
        return self._handle_response(response)

    def post(self, path: str, **kwargs) -> Any:
        """Make POST request."""
        response = self.http_client.post(path, **kwargs)
        return self._handle_response(response)

    def put(self, path: str, **kwargs) -> Any:
        """Make PUT request."""
        response = self.http_client.put(path, **kwargs)
        return self._handle_response(response)

    def delete(self, path: str, **kwargs) -> Any:
        """Make DELETE request."""
        response = self.http_client.delete(path, **kwargs)
        if response.status_code == 204:
            return None
        return self._handle_response(response)

    def close(self):
        """Close HTTP client."""
        self.http_client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
