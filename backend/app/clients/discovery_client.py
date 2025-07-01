import aiohttp
from typing import Optional
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DiscoveryServiceClient:
    """Client for interacting with the Discovery microservice"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.DISCOVERY_SERVICE_URL
        if not self.base_url:
            # Default to localhost for development
            self.base_url = "http://localhost:8001"
        
        logger.info(f"Discovery service client initialized with URL: {self.base_url}")
    
    async def discover_sources(self, raw_query: str) -> list[str]:
        """
        Call the discovery service to find monitorable URLs.
        
        Args:
            raw_query: The user's natural language query
            
        Returns:
            List of monitorable URLs
            
        Raises:
            ConnectionError: If unable to reach the discovery service
            ValueError: If the service returns an invalid response
        """
        url = f"{self.base_url}/api/v1/discover"
        payload = {"raw_query": raw_query}
        
        async with aiohttp.ClientSession() as session:
            try:
                logger.debug(f"Calling discovery service: {url}")
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Discovery service error: {response.status} - {error_text}"
                        )
                        raise ConnectionError(
                            f"Discovery service returned status {response.status}"
                        )
                    
                    data = await response.json()
                    urls = data.get("monitorable_urls", [])
                    logger.info(f"Discovery service returned {len(urls)} URLs")
                    return urls
                    
            except aiohttp.ClientError as e:
                logger.error(f"Failed to connect to discovery service: {e}")
                raise ConnectionError(
                    f"Unable to connect to discovery service at {self.base_url}"
                ) from e
            except Exception as e:
                logger.error(f"Unexpected error calling discovery service: {e}")
                raise