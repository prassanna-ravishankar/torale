import logging
from typing import Optional

from app.services.ai_integrations.interface import AIModelInterface
from app.clients.discovery_client import DiscoveryServiceClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SourceDiscoveryService:
    def __init__(self, ai_model: Optional[AIModelInterface] = None):
        # If DISCOVERY_SERVICE_URL is set, use the microservice
        # Otherwise fall back to the legacy AI model approach
        if settings.DISCOVERY_SERVICE_URL:
            self.use_microservice = True
            self.discovery_client = DiscoveryServiceClient()
            logger.info("Using discovery microservice")
        else:
            self.use_microservice = False
            self.ai_model = ai_model
            if not self.ai_model:
                raise ValueError("AI model is required when not using discovery microservice")
            logger.info("Using legacy AI model for discovery")

    async def discover_sources(self, raw_query: str, **kwargs) -> list[str]:
        """
        Discovers relevant source URLs for a given raw query.
        
        This will use the discovery microservice if configured,
        otherwise falls back to the legacy AI model approach.
        """
        if self.use_microservice:
            try:
                # Use the microservice
                return await self.discovery_client.discover_sources(raw_query)
            except Exception as e:
                logger.error(f"Discovery microservice failed: {e}")
                # Could implement fallback to AI model here if desired
                raise
        else:
            # Legacy approach using AI model directly
            # Step 1: Refine the raw query
            refined_query = await self.ai_model.refine_query(
                raw_query, **kwargs.get("refine_kwargs", {})
            )

            # Step 2: Identify sources using the refined query
            source_urls = await self.ai_model.identify_sources(
                refined_query, **kwargs.get("identify_kwargs", {})
            )

            return source_urls
