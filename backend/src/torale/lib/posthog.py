import threading

from posthog import Posthog

from torale.core.config import settings

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
                _posthog_client = Posthog(
                    project_api_key=settings.posthog_api_key,
                    host=settings.posthog_host,
                )

    return _posthog_client


def capture(distinct_id: str, event: str, properties: dict | None = None):
    """Capture event if PostHog is enabled."""
    client = get_posthog()
    if client:
        client.capture(distinct_id=distinct_id, event=event, properties=properties or {})


def shutdown():
    """Flush and shutdown PostHog client."""
    global _posthog_client
    with _lock:
        if _posthog_client:
            _posthog_client.shutdown()
            _posthog_client = None
