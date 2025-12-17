from abc import ABC, abstractmethod


class SchemaProvider(ABC):
    """
    Generates task-specific extraction schemas.

    The schema defines what structured data to extract from search results
    for a given monitoring task. This enables deterministic comparison while
    allowing semantic extraction.
    """

    @abstractmethod
    async def generate_schema(self, task: dict) -> dict:
        """
        Generate a new extraction schema for a task.

        Args:
            task: Task configuration with search_query, condition_description

        Returns:
            Schema dict defining fields to extract, e.g.:
            {
                "release_date": {"type": "date", "description": "Product release date"},
                "confirmed": {"type": "bool", "description": "Official confirmation"},
                "price": {"type": "number", "description": "Price in USD"}
            }

        Example:
            Task: "Monitor iPhone 16 release date"
            Schema: {
                "release_date": {"type": "date", "description": "Announced release date"},
                "product_name": {"type": "string", "description": "Product name"},
                "source_confidence": {"type": "enum", "values": ["high", "medium", "low"]}
            }
        """
        pass

    @abstractmethod
    async def get_or_create_schema(self, task: dict) -> dict:
        """
        Get cached schema for task or generate if not exists.

        Args:
            task: Task configuration

        Returns:
            Cached or newly generated schema
        """
        pass
