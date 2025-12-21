from abc import ABC, abstractmethod


class ComparisonProvider(ABC):
    """
    Compares states semantically to detect meaningful changes.

    Uses LLM for semantic understanding ("Sept" == "September")
    while working with structured data from extraction.
    """

    @abstractmethod
    async def compare(
        self,
        previous_state: dict | None,
        current_state: dict,
        schema: dict,
    ) -> dict:
        """
        Compare previous and current states semantically.

        Args:
            previous_state: Previous extracted state (None if first execution)
            current_state: Current extracted state
            schema: Schema context for understanding fields

        Returns:
            StateChange dict with keys:
                - changed: bool indicating if meaningful change occurred
                - explanation: Human-readable explanation of what changed

        Example:
            previous: {"release_date": None, "confirmed": False}
            current: {"release_date": "2024-09-12", "confirmed": True}
            Returns: {
                "changed": True,
                "explanation": "Release date announced: Sept 12, 2024. Now officially confirmed."
            }
        """
        pass
