"""Website monitoring module."""

import hashlib
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from smolagents import HfApiModel, VisitWebpageTool


class WebsiteMonitor:
    """Monitors websites for changes and determines relevance."""

    def __init__(self, model: Optional[HfApiModel] = None):
        """Initialize the website monitor.

        Args:
            model: Optional HfApiModel instance for relevance checking
        """
        self.model = model or HfApiModel()
        self.webpage_tool = VisitWebpageTool()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def get_content_hash_from_content(self, content: str) -> str:
        """Get a hash of the relevant content from HTML content.

        Args:
            content: The HTML content to hash

        Returns:
            A hash of the page's main content
        """
        if not content:
            return ""

        try:
            # Parse with BeautifulSoup to get main content
            soup = BeautifulSoup(content, "html.parser")

            # Remove scripts, styles, and navigation elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get the main text content
            text = soup.get_text()
            return hashlib.sha256(text.encode()).hexdigest()
        except Exception as e:
            print(f"Error hashing content: {e}")
            return ""

    async def get_content_hash(self, url: str) -> str:
        """Get a hash of the relevant content from a URL.

        Args:
            url: The URL to check

        Returns:
            A hash of the page's main content
        """
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self.get_content_hash_from_content(content)
                print(f"Error fetching {url}: HTTP {response.status}")
                return ""
        except Exception as e:
            print(f"Error getting content from {url}: {e}")
            return ""

    async def check_relevance(self, content: str, query: str) -> tuple[bool, str]:
        """Check if content changes are relevant to the original query.

        Args:
            content: The content to check
            query: The original search query

        Returns:
            Tuple of (is_relevant, explanation)
        """
        prompt = f"""Analyze if the following content is relevant to the query "{query}".
        Content: {content[:1000]}...

        Answer with YES or NO, followed by a brief explanation."""

        # Note: Using synchronous model.generate for now as smolagents doesn't support async yet
        response = self.model.generate(prompt)
        lines = response.strip().split("\n")
        is_relevant = lines[0].strip().upper().startswith("YES")
        explanation = "\n".join(lines[1:]).strip()
        return is_relevant, explanation

    async def get_content_summary(self, content: str) -> str:
        """Generate a summary of the changed content.

        Args:
            content: The content to summarize

        Returns:
            A brief summary of the content
        """
        prompt = "Summarize the following content in 2-3 sentences:\n\n" + content[:2000]
        # Note: Using synchronous model.generate for now as smolagents doesn't support async yet
        return self.model.generate(prompt).strip()

    async def fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from a URL asynchronously.

        Args:
            url: The URL to fetch

        Returns:
            The page content if successful, None otherwise
        """
        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                print(f"Error fetching {url}: HTTP {response.status}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
