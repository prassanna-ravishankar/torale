from abc import ABC, abstractmethod
from typing import Any


class AIModelInterface(ABC):
    @abstractmethod
    async def refine_query(self, raw_query: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def identify_sources(self, refined_query: str, **kwargs) -> list[str]:
        pass

    @abstractmethod
    async def generate_embeddings(
        self, texts: list[str], **kwargs
    ) -> list[list[float]]:
        pass

    @abstractmethod
    async def analyze_diff(
        self, old_representation: Any, new_representation: Any, **kwargs
    ) -> dict:
        pass
