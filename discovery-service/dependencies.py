from functools import lru_cache
import structlog

from config import get_settings
from clients.ai_interface import AIModelInterface
from clients.perplexity_client import PerplexityClient
from clients.openai_client import OpenAIClient
from services.discovery_service import DiscoveryService

logger = structlog.get_logger()


@lru_cache()
def get_ai_client() -> AIModelInterface:
    """Get the configured AI client based on settings"""
    settings = get_settings()
    
    if settings.ai_provider == "perplexity":
        if not settings.perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY is required when using Perplexity provider")
        
        logger.info("using_perplexity_provider")
        return PerplexityClient(
            api_key=settings.perplexity_api_key,
            model=settings.ai_model or "sonar"
        )
    
    elif settings.ai_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        
        logger.info("using_openai_provider")
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.ai_model or "gpt-4-turbo-preview"
        )
    
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")


@lru_cache()
def get_discovery_service() -> DiscoveryService:
    """Get the discovery service with injected dependencies"""
    ai_client = get_ai_client()
    return DiscoveryService(ai_client=ai_client)