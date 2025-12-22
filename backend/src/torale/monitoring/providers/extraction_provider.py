from abc import ABC, abstractmethod


class ExtractionProvider(ABC):
    """
    Extracts structured data from search results using a schema.

    Uses LLM to parse unstructured search results into structured data
    matching a predefined schema. This separates parsing (LLM) from
    comparison (deterministic).
    """

    @abstractmethod
    async def extract(self, search_result: dict, schema: dict) -> dict:
        """
        Extract structured data from search result according to schema.

        Args:
            search_result: Dict with 'answer' and 'sources' from search
            schema: Schema defining fields to extract

        Returns:
            Extracted data matching schema structure, e.g.:
            {
                "release_date": "2024-09-12",
                "confirmed": True,
                "price": None
            }

        Example:
            Search result: "Apple announced iPhone 16 for Sept 12, 2024"
            Schema: {"release_date": {"type": "date"}, "confirmed": {"type": "bool"}}
            Returns: {"release_date": "2024-09-12", "confirmed": True}
        """
        pass
