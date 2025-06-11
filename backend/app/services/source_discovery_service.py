import logging

from app.services.ai_integrations.interface import AIModelInterface

logger = logging.getLogger(__name__)


class SourceDiscoveryService:
    def __init__(self, ai_model: AIModelInterface):
        self.ai_model = ai_model

    async def discover_sources(self, raw_query: str, **kwargs) -> list[str]:
        """
        Discovers relevant source URLs for a given raw query.
        It refines the query and then identifies sources using the AI model.
        """
        # Step 1: Refine the raw query
        refined_query = await self.ai_model.refine_query(
            raw_query, **kwargs.get("refine_kwargs", {})
        )

        # Step 2: Identify sources using the refined query
        # Assuming identify_sources returns a list of URL strings
        source_urls = await self.ai_model.identify_sources(
            refined_query, **kwargs.get("identify_kwargs", {})
        )

        return source_urls
