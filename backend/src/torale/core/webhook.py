"""Webhook delivery service with HMAC signing and retry logic."""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Literal

import httpx
from pydantic import BaseModel


class WebhookPayload(BaseModel):
    """Standard webhook payload format (inspired by Stripe/GitHub)."""

    # Event metadata
    id: str  # Unique event ID (task_execution.id)
    event_type: Literal["task.condition_met"]
    created_at: int  # Unix timestamp

    # Torale metadata
    object: str = "event"
    api_version: str = "v1"

    # Event data
    data: dict  # Contains task, execution, and result details


class WebhookSignature:
    """Generate and verify HMAC-SHA256 webhook signatures."""

    @staticmethod
    def generate_secret() -> str:
        """Generate a secure random webhook secret (32 bytes)."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def sign(payload: str, secret: str, timestamp: int) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.

        Format: t=<timestamp>,v1=<signature>
        Follows Stripe's signature format for industry compatibility.
        """
        signed_payload = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return f"t={timestamp},v1={signature}"

    @staticmethod
    def verify(
        payload: str,
        signature_header: str,
        secret: str,
        tolerance: int = 300,  # 5 minutes tolerance for clock skew
    ) -> bool:
        """
        Verify webhook signature with timestamp validation.

        Prevents replay attacks by checking timestamp tolerance.
        """
        try:
            # Parse signature header
            sig_parts = dict(part.split("=") for part in signature_header.split(","))
            timestamp = int(sig_parts["t"])
            expected_sig = sig_parts["v1"]

            # Check timestamp tolerance (prevent replay attacks)
            current_time = int(time.time())
            if abs(current_time - timestamp) > tolerance:
                return False

            # Verify signature
            signed_payload = f"{timestamp}.{payload}"
            computed_sig = hmac.new(
                secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
            ).hexdigest()

            # Timing-safe comparison
            return hmac.compare_digest(computed_sig, expected_sig)

        except (KeyError, ValueError):
            return False


class WebhookDeliveryService:
    """Handle webhook HTTP delivery with retries."""

    # Exponential backoff schedule: 1min, 5min, 15min (total ~21 minutes)
    RETRY_DELAYS = [60, 300, 900]  # seconds
    TIMEOUT = 10  # seconds

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)

    async def deliver(
        self, url: str, payload: WebhookPayload, secret: str, attempt: int = 1
    ) -> tuple[bool, int | None, str | None, str]:
        """
        Deliver webhook with HMAC signature.

        Returns: (success, http_status, error_message, signature)
        """
        # Generate signature
        timestamp = int(time.time())
        payload_json = payload.model_dump_json()
        signature = WebhookSignature.sign(payload_json, secret, timestamp)

        # Prepare headers (following GitHub/Stripe conventions)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Torale-Webhooks/1.0",
            "X-Torale-Event": payload.event_type,
            "X-Torale-Signature": signature,
            "X-Torale-Delivery": payload.id,
            "X-Torale-Timestamp": str(timestamp),
        }

        try:
            response = await self.client.post(url, content=payload_json, headers=headers)

            # Consider 2xx as success
            if 200 <= response.status_code < 300:
                return (True, response.status_code, None, signature)
            else:
                return (
                    False,
                    response.status_code,
                    f"HTTP {response.status_code}: {response.text[:200]}",
                    signature,
                )

        except httpx.TimeoutException:
            return (False, None, f"Timeout after {self.TIMEOUT}s", signature)
        except httpx.RequestError as e:
            return (False, None, f"Request error: {str(e)}", signature)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    @classmethod
    def get_next_retry_time(cls, attempt: int) -> datetime | None:
        """Calculate next retry time based on attempt number."""
        if attempt > len(cls.RETRY_DELAYS):
            return None  # No more retries

        delay_seconds = cls.RETRY_DELAYS[attempt - 1]
        return datetime.utcnow() + timedelta(seconds=delay_seconds)


def build_webhook_payload(
    execution_id: str, task: dict, execution: dict, result: dict
) -> WebhookPayload:
    """Build standardized webhook payload."""
    return WebhookPayload(
        id=execution_id,
        event_type="task.condition_met",
        created_at=int(time.time()),
        data={
            "task": {
                "id": str(task["id"]),
                "name": task["name"],
                "search_query": task.get("search_query", ""),
                "condition_description": task.get("condition_description", ""),
            },
            "execution": {
                "id": execution_id,
                "condition_met": execution.get("condition_met"),
                "change_summary": execution.get("change_summary"),
                "completed_at": str(execution.get("completed_at", "")),
            },
            "result": {
                "answer": result.get("answer", ""),
                "grounding_sources": result.get("grounding_sources", []),
            },
        },
    )
