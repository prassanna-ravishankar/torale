from abc import ABC, abstractmethod


class AIModelInterface(ABC):
    """Interface for discovery-specific AI operations"""
    
    @abstractmethod
    async def refine_query(self, raw_query: str, **kwargs) -> str:
        """Refine a raw user query into a focused search query"""
        pass

    @abstractmethod
    async def identify_sources(self, refined_query: str, **kwargs) -> list[str]:
        """Identify monitorable URLs from a refined query"""
        pass