"""
PostHog analytics client for backend.

Thread-safe singleton with double-checked locking.
This pattern is safe in Python due to GIL guaranteeing atomic reference
assignment. The outer check avoids lock contention after initialization.

All functions gracefully handle errors - analytics failures never break core functionality.
"""

import logging
import threading

from posthog import Posthog

from torale.core.config import settings

logger = logging.getLogger(__name__)

_posthog_client: Posthog | None = None
_lock = threading.Lock()


def get_posthog() -> Posthog | None:
    """Get PostHog client singleton in a thread-safe manner."""
    global _posthog_client

    if not settings.posthog_enabled or not settings.posthog_api_key:
        return None

    if _posthog_client is None:
        with _lock:
            # Double-check inside the lock to prevent race conditions
            if _posthog_client is None:
                try:
                    _posthog_client = Posthog(
                        project_api_key=settings.posthog_api_key,
                        host=settings.posthog_host,
                    )
                    logger.info("PostHog client initialized successfully")
                except Exception as e:
                    logger.error(
                        "Failed to initialize PostHog client - analytics disabled",
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "posthog_host": settings.posthog_host,
                        },
                        exc_info=True,
                    )
                    # Return None to disable analytics for this session
                    return None

    return _posthog_client


def capture(distinct_id: str, event: str, properties: dict | None = None):
    """Capture event if PostHog is enabled. Never crashes on failure."""
    client = get_posthog()
    if not client:
        return

    try:
        client.capture(distinct_id=distinct_id, event=event, properties=properties or {})
    except Exception as e:
        # Never let analytics failures break core functionality
        logger.warning(
            f"PostHog event capture failed for '{event}'",
            extra={
                "event": event,
                "error_type": type(e).__name__,
                "error_message": str(e)[:200],
                "distinct_id": distinct_id,
            },
        )


def shutdown():
    """Flush and shutdown PostHog client. Never blocks app shutdown."""
    global _posthog_client
    with _lock:
        if _posthog_client:
            try:
                _posthog_client.shutdown()
                logger.info("PostHog client shut down successfully")
            except Exception as e:
                logger.warning(
                    "PostHog shutdown failed - some events may be lost",
                    extra={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    },
                )
            finally:
                # Always clear the client reference even if shutdown fails
                _posthog_client = None
