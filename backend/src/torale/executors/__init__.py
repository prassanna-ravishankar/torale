from abc import ABC, abstractmethod


class TaskExecutor(ABC):
    @abstractmethod
    async def execute(self, config: dict) -> dict:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass


# Import after class definition to avoid circular import
from torale.executors.grounded_search import GroundedSearchExecutor  # noqa: E402

__all__ = ["TaskExecutor", "GroundedSearchExecutor"]
