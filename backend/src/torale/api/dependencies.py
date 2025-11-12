"""FastAPI dependencies for dependency injection."""

from functools import lru_cache

from torale.core.config import settings


@lru_cache(maxsize=1)
def get_genai_client():
    """
    Get or create a singleton Google Genai client.

    Using lru_cache ensures the client is instantiated only once
    and reused across requests, avoiding the overhead of repeated
    authentication and resource setup.

    Returns:
        genai.Client: Singleton Genai client instance
    """
    from google import genai

    if not settings.google_api_key:
        raise ValueError("Google API key is required but not configured")

    return genai.Client(api_key=settings.google_api_key)
