from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AIModelInterface(ABC):
    @abstractmethod
    async def refine_query(self, raw_query: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def identify_sources(self, refined_query: str, **kwargs) -> List[str]:
        pass

    @abstractmethod
    async def generate_embeddings(
        self, texts: List[str], **kwargs
    ) -> List[List[float]]:
        pass

    @abstractmethod
    async def analyze_diff(
        self, old_representation: Any, new_representation: Any, **kwargs
    ) -> Dict:
        pass
