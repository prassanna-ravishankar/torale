import logging
from typing import Any, Optional

import aiohttp
import openai
from openai import AsyncOpenAI

from clients.ai_interface import AIModelInterface
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class OpenAIClient(AIModelInterface):
    """OpenAI client for generating embeddings and analyzing diffs."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self._model_name = "openai"
        logger.info("OpenAI client initialized")
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    async def generate_embeddings(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Generate embeddings using OpenAI's embedding model."""
        model = kwargs.get("model", "text-embedding-3-small")
        
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=model
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(f"Generated {len(embeddings)} embeddings using {model}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def analyze_diff(self, old_representation: Any, new_representation: Any, **kwargs) -> dict:
        """Analyze differences between old and new content using OpenAI."""
        model = kwargs.get("model", "gpt-3.5-turbo")
        
        system_prompt = kwargs.get(
            "system_prompt",
            "You are a content analysis assistant. Compare the old and new content "
            "and provide a brief summary of the key changes."
        )
        
        user_prompt = (
            f"Old content:\n```\n{old_representation}\n```\n\n"
            f"New content:\n```\n{new_representation}\n```\n\n"
            f"What are the key changes between these two versions?"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            analysis_summary = response.choices[0].message.content.strip()
            logger.info("Successfully analyzed content differences with OpenAI")
            
            return {
                "summary": analysis_summary,
                "details": {
                    "model_used": model,
                    "analysis_type": "ai_generated"
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing diff with OpenAI: {e}")
            raise