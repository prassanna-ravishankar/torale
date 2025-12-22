from abc import ABC, abstractmethod


class SearchProvider(ABC):
    """
    Performs grounded search with temporal context awareness.

    The search provider executes web searches and returns structured results
    with grounding sources. It supports temporal filtering to prioritize
    recent information and changes since last execution.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        temporal_context: dict | None = None,
        model: str = "gemini-2.5-flash",
    ) -> dict:
        """
        Perform grounded search with optional temporal context.

        Args:
            query: Search query string
            temporal_context: Optional dict with last_execution_datetime for temporal filtering
            model: Model identifier to use for search

        Returns:
            Dict with:
                - answer: Search result answer text
                - sources: List of grounding sources (url, title)
                - temporal_note: Optional note about temporal filtering

        Example:
            result = await provider.search(
                query="iPhone 16 release date",
                temporal_context={"last_execution_datetime": datetime(2024, 11, 1)},
                model="gemini-2.5-flash"
            )
            # Returns: {
            #   "answer": "Apple announced iPhone 16 will release September 20, 2024",
            #   "sources": [{"url": "...", "title": "Apple Newsroom"}],
            #   "temporal_note": None
            # }
        """
        pass
