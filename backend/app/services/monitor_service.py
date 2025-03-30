from typing import Optional

import aiohttp
from bs4 import BeautifulSoup

# HTTP Status Codes
HTTP_OK = 200


class MonitorService:
    async def get_content(self, url: str, target_type: str) -> Optional[str]:
        """Get content from a URL based on target type."""
        if target_type == "website":
            return await self._get_website_content(url)
        elif target_type == "rss":
            return await self._get_rss_content(url)
        elif target_type == "youtube":
            return await self._get_youtube_content(url)
        return None

    async def _get_website_content(self, url: str) -> Optional[str]:
        """Get content from a website."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != HTTP_OK:
                        return None
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    return soup.get_text()
            except Exception as e:
                print(f"Error fetching website content: {e}")
                return None

    async def _get_rss_content(self, url: str) -> Optional[str]:
        """Get content from an RSS feed."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status != HTTP_OK:
                        return None
                    return await response.text()
            except Exception as e:
                print(f"Error fetching RSS content: {e}")
                return None

    async def _get_youtube_content(self, url: str) -> Optional[str]:
        """Get content from a YouTube channel."""
        # TODO: Implement YouTube API integration
        return None
