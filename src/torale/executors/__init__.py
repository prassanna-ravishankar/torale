from abc import ABC, abstractmethod


class TaskExecutor(ABC):
    @abstractmethod
    async def execute(self, config: dict) -> dict:
        pass

    @abstractmethod
    def validate_config(self, config: dict) -> bool:
        pass