"""Website monitoring module."""

import hashlib
from typing import Optional

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

    def get_content_hash_from_content(self, content: str) -> str:
        """Get a hash of the relevant content from HTML content.

        Args:
            content: The HTML content to hash

        Returns:
            A hash of the page's main content
        """
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

    def get_content_hash(self, url: str) -> str:
        """Get a hash of the relevant content from a URL.

        Args:
            url: The URL to check

        Returns:
            A hash of the page's main content
        """
        try:
            # Use the webpage tool to get content safely
            content = self.webpage_tool.visit(url)  # Use visit instead of run
            return self.get_content_hash_from_content(content) if content else ""
        except Exception as e:
            print(f"Error getting content from {url}: {e}")
            return ""

    def check_relevance(self, content: str, query: str) -> tuple[bool, str]:
        """Check if content changes are relevant to the original query."""
        prompt = f"""Analyze if the following content is relevant to the query "{query}".
        Content: {content[:1000]}...

        Answer with YES or NO, followed by a brief explanation."""

        response = self.model.generate(prompt)
        is_relevant = response.strip().upper().startswith("YES")
        return is_relevant, response.strip()

    def get_content_summary(self, content: str) -> str:
        """Generate a summary of the changed content.

        Args:
            content: The content to summarize

        Returns:
            A brief summary of the content
        """
        prompt = "Summarize the following content in 2-3 sentences:\n\n" + content[:2000]
        return self.model.generate(prompt).strip()
