from abc import ABC, abstractmethod


class MonitoringProvider(ABC):
    """
    Base provider for monitoring execution.

    Implementations can range from structured (schema-based extraction)
    to fully autonomous (agent with tool access).

    The interface is intentionally minimal to support different levels of agency:
    - Structured: Provider uses schema, extracts data, compares semantically
    - Autonomous: Provider is a single agent with tools (search, notify, compare)
    """

    @abstractmethod
    async def execute_monitoring(self, task: dict, context: dict) -> dict:
        """
        Execute monitoring for a task.

        Args:
            task: Task configuration including search_query, condition_description
            context: Execution context including previous_state, last_execution_datetime

        Returns:
            MonitoringResult as dict with keys:
                - summary: Natural language summary for user
                - sources: List of grounding sources
                - actions: List of actions taken (e.g., ["searched", "compared"])
                - metadata: Optional dict with provider-specific data

        Raises:
            Exception: If monitoring execution fails
        """
        pass
