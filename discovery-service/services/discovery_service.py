from typing import Optional
import structlog
from clients.ai_interface import AIModelInterface

logger = structlog.get_logger()


class DiscoveryService:
    """Service that handles source discovery from natural language queries"""
    
    def __init__(self, ai_client: AIModelInterface):
        self.ai_client = ai_client
        logger.info("discovery_service_initialized")
    
    async def discover_sources(self, raw_query: str) -> list[str]:
        """
        Discover monitorable sources from a natural language query.
        
        Args:
            raw_query: The user's natural language query
            
        Returns:
            List of monitorable URLs
        """
        logger.info("discovering_sources", query_length=len(raw_query))
        
        try:
            # Step 1: Refine the query
            refined_query = await self.ai_client.refine_query(raw_query)
            logger.debug("query_refined", refined_query=refined_query)
            
            # Step 2: Identify sources
            sources = await self.ai_client.identify_sources(refined_query)
            logger.info("sources_discovered", count=len(sources))
            
            # Filter out duplicates while preserving order
            unique_sources = []
            seen = set()
            for source in sources:
                if source not in seen:
                    seen.add(source)
                    unique_sources.append(source)
            
            return unique_sources
            
        except Exception as e:
            logger.error("discovery_error", error=str(e), query=raw_query)
            raise