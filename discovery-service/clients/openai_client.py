import structlog
from openai import AsyncOpenAI
from typing import Optional

from clients.ai_interface import AIModelInterface

logger = structlog.get_logger()


class OpenAIClient(AIModelInterface):
    """OpenAI client for discovery operations - currently a fallback option"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info("openai_client_initialized", model=model)

    async def refine_query(self, raw_query: str, **kwargs) -> str:
        logger.info("refining_query_openai", query_length=len(raw_query))
        
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that refines user queries into focused search queries for monitoring websites. Output only the refined query, no explanations."
                    },
                    {
                        "role": "user",
                        "content": f"Refine this monitoring query into a search query: {raw_query}"
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            refined_query = response.choices[0].message.content.strip()
            logger.info("query_refined_openai", refined_length=len(refined_query))
            return refined_query
            
        except Exception as e:
            logger.error("openai_refine_error", error=str(e))
            raise

    async def identify_sources(self, refined_query: str, **kwargs) -> list[str]:
        logger.info("identifying_sources_openai", query_length=len(refined_query))
        
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that identifies stable, monitorable URLs based on search queries. Output only URLs, one per line, no explanations or numbering."
                    },
                    {
                        "role": "user",
                        "content": f"Find monitorable URLs for: {refined_query}"
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content.strip()
            urls = []
            for line in content.split("\n"):
                url = line.strip()
                if url:
                    if not url.startswith(("http://", "https://")):
                        url = f"https://{url}"
                    urls.append(url)
            
            logger.info("sources_identified_openai", count=len(urls))
            return urls
            
        except Exception as e:
            logger.error("openai_identify_error", error=str(e))
            raise