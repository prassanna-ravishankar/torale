"""Webhook retry job - processes failed deliveries."""

import logging

from torale.core.database import db
from torale.notifications.webhook import WebhookDeliveryService, WebhookPayload
from torale.repositories.webhook import WebhookRepository

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = len(WebhookDeliveryService.RETRY_DELAYS) + 1


async def execute_webhook_retry_job():
    """Find and retry pending webhook deliveries.

    Runs every 5 minutes via APScheduler.
    Retries deliveries where: delivered_at IS NULL AND next_retry_at <= NOW()
    """
    repo = WebhookRepository(db)
    pending = await repo.find_pending_retries()

    if not pending:
        logger.debug("No pending webhook retries")
        return

    logger.info(f"Processing {len(pending)} webhook retries")

    service = WebhookDeliveryService()
    try:
        for delivery in pending:
            await _retry_webhook_delivery(service, repo, delivery)
    finally:
        await service.close()


async def _retry_webhook_delivery(
    service: WebhookDeliveryService, repo: WebhookRepository, delivery: dict
):
    """Retry a single webhook delivery."""
    delivery_id = delivery["id"]
    attempt = delivery["attempt_number"] + 1

    logger.info(f"Retrying webhook delivery {delivery_id} (attempt {attempt}/{MAX_ATTEMPTS})")

    webhook_secret = delivery.get("webhook_secret")
    if not webhook_secret:
        logger.error(
            f"Webhook delivery {delivery_id} missing secret, marking as permanently failed"
        )
        await repo.mark_permanently_failed(delivery_id, "Missing webhook secret for retry")
        return

    payload = WebhookPayload(**delivery["payload"])

    success, http_status, error, signature = await service.deliver(
        url=delivery["webhook_url"], payload=payload, secret=webhook_secret, attempt=attempt
    )

    if success:
        await repo.update_delivery(delivery_id, delivered_at="NOW()")
        logger.info(f"Webhook delivery {delivery_id} succeeded on retry {attempt}")
        return

    if attempt < MAX_ATTEMPTS:
        next_retry = service.get_next_retry_time(attempt)
        await repo.update_delivery(
            delivery_id,
            attempt_number=attempt,
            next_retry_at=next_retry.isoformat() if next_retry else None,
            error_message=error,
        )
        logger.warning(
            f"Webhook delivery {delivery_id} failed (attempt {attempt}), will retry at {next_retry}"
        )
    else:
        await repo.mark_permanently_failed(delivery_id, error or "Unknown error")
        logger.error(
            f"Webhook delivery {delivery_id} permanently failed after {attempt} attempts: {error}"
        )
