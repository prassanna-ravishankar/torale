"""Webhooks resource for Torale SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from torale.sdk.client import ToraleClient


class WebhooksResource:
    """Resource for managing webhooks."""

    def __init__(self, client: ToraleClient):
        self.client = client

    def get_config(self) -> dict[str, Any]:
        """
        Get user's default webhook configuration.

        Returns:
            Dictionary with webhook config:
            - url: Webhook URL (or None)
            - secret: Webhook secret for signature verification
            - enabled: Whether webhooks are enabled

        Example:
            >>> config = client.webhooks.get_config()
            >>> print(f"Webhook URL: {config['url']}")
            >>> print(f"Secret: {config['secret']}")
            >>> print(f"Enabled: {config['enabled']}")
        """
        response = self.client.get("/api/v1/webhooks/config")
        return response

    def update_config(
        self,
        url: str | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """
        Update user's default webhook configuration.

        Args:
            url: Webhook URL to send notifications to
            enabled: Whether to enable webhook notifications

        Returns:
            Updated webhook config with url, secret, and enabled status

        Example:
            >>> config = client.webhooks.update_config(
            ...     url="https://myapp.com/webhooks/torale",
            ...     enabled=True
            ... )
            >>> print(f"Webhook configured: {config['url']}")
            >>> print(f"Use this secret: {config['secret']}")
        """
        data = {
            "webhook_url": url,
            "enabled": enabled,
        }
        response = self.client.put("/api/v1/webhooks/config", json=data)
        return response

    def test(
        self,
        url: str,
        secret: str,
    ) -> dict[str, Any]:
        """
        Test webhook delivery with a sample payload.

        Sends a test webhook to verify your endpoint is configured correctly.
        The test payload will include sample task and execution data.

        Args:
            url: Webhook URL to test
            secret: Webhook secret for signature verification

        Returns:
            Test result with success status and message

        Raises:
            Exception: If webhook delivery fails

        Example:
            >>> result = client.webhooks.test(
            ...     url="https://webhook.site/unique-id",
            ...     secret="your-webhook-secret"
            ... )
            >>> print(result['message'])
            'Webhook delivered successfully (HTTP 200)'
        """
        data = {
            "webhook_url": url,
            "webhook_secret": secret,
        }
        response = self.client.post("/api/v1/webhooks/test", json=data)
        return response

    def list_deliveries(
        self,
        task_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        List webhook delivery history.

        Args:
            task_id: Optional task ID to filter deliveries
            limit: Maximum number of deliveries to return (default: 10)

        Returns:
            List of webhook delivery records with status, timestamps, and errors

        Example:
            >>> deliveries = client.webhooks.list_deliveries(limit=5)
            >>> for delivery in deliveries:
            ...     print(f"{delivery['created_at']}: {delivery['status']}")
        """
        params = {"limit": limit}
        if task_id:
            params["task_id"] = task_id

        response = self.client.get("/api/v1/webhooks/deliveries", params=params)
        return response
