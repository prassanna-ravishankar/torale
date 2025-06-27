from abc import ABC, abstractmethod
from typing import Any, Optional


class AIModelInterface(ABC):
    """Abstract interface for AI model implementations."""
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of the AI model."""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to generate embeddings for
            **kwargs: Additional parameters for the embedding model
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        pass
    
    async def analyze_diff(self, old_representation: Any, new_representation: Any, **kwargs) -> dict:
        """
        Analyze differences between old and new content representations.
        
        Args:
            old_representation: Previous content (text, embeddings, etc.)
            new_representation: New content (text, embeddings, etc.)
            **kwargs: Additional parameters for analysis
            
        Returns:
            Dictionary containing analysis results with keys:
            - 'summary': Brief description of changes
            - 'details': More detailed analysis (optional)
        """
        raise NotImplementedError("analyze_diff method not implemented by this AI model")