from typing import Any, Dict, List, Optional
import aiohttp
import json
import logging

from app.services.ai_integrations.interface import AIModelInterface
from app.core.config import get_settings

# Potentially import perplexity library here if you install or create one
# from perplexity import Perplexity // Assuming a hypothetical library

settings = get_settings()
logger = logging.getLogger(__name__)

# Constants from the example script
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# System prompts from the example script - can be moved to a config or constants file later
SYSTEM_PROMPT_REFINE_QUERY = """You are an AI assistant that refines a user's general interest into a focused search query.
The user wants to monitor a topic, entity, or type of information online for any significant changes or new updates.
Your task is to transform their initial interest into a concise search query string. This refined query should be designed to help another AI find one or more stable, central webpages (e.g., official news sections, main product/service pages, primary blog URLs, key community hubs, or official announcement channels) that are most likely to be updated when new, relevant information appears.
Output *only* the refined search query string. No explanations or labels.

Example User Interest: "latest from OpenAI"
Example Refined Query Output: "OpenAI official announcements or blog"

Example User Interest: "Sony camera rumors"
Example Refined Query Output: "Sony camera news and rumor hubs"

Example User Interest: "discounts in tkmaxx"
Example Refined Query Output: "TK Maxx official offers and deals page"""

SYSTEM_PROMPT_IDENTIFY_SOURCES = """Based on the user's search query, which expresses an interest in monitoring a topic for updates:
1. Identify one or more primary, stable URLs that are central to the user's interest and likely to be updated when relevant new information, products, services, news, or offers appear.
2. Prioritize official pages (e.g., news sections, main product/service category homepages, primary blog URLs, official offer/announcement channels) or highly reputable and comprehensive community hubs/forums if appropriate for the topic (e.g., for discussions, rumors, or community-driven updates).
3. The goal is to find pages that serve as ongoing, canonical sources of information or updates for the given query, suitable for long-term monitoring.
4. Avoid linking to specific, transient articles or individual forum posts unless they are explicitly designed as continuously updated 'live blogs' or master threads.
5. Output a list of these relevant URLs, each on a new line.
6. Output *only* the list of URLs. No extra text, explanations, or numbering.

Example User Query: "OpenAI official announcements or blog"
Example Expected Output:
openai.com/blog
openai.com/news

Example User Query: "Sony camera news and rumor hubs"
Example Expected Output:
sonyalpharumors.com
dpreview.com/news/sony

Example User Query: "TK Maxx official offers and deals page"
Example Expected Output:
tkmaxx.com/uk/en/offers
"""

class PerplexityClient(AIModelInterface):
    def __init__(self, api_key: Optional[str] = None, model: str = "sonar-medium-online"):
        self.api_key = api_key or settings.PERPLEXITY_API_KEY
        if not self.api_key:
            logger.critical("Perplexity API key is required but not found. Set PERPLEXITY_API_KEY.")
            raise ValueError("Perplexity API key is required. Set PERPLEXITY_API_KEY in environment.")
        self.model = model
        self.model_name = f"perplexity/{self.model}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        logger.info(f"PerplexityClient initialized with model: {self.model_name}")

    async def _make_perplexity_request(self, payload: Dict) -> Dict:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                logger.debug(f"Sending request to Perplexity API: {PERPLEXITY_API_URL} with payload: {json.dumps(payload)[:200]}...")
                response = await session.post(PERPLEXITY_API_URL, json=payload)
                response.raise_for_status()
                return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"AIOHTTP client error with Perplexity API ({PERPLEXITY_API_URL}): {e}", exc_info=True)
                raise ConnectionError(f"Failed to connect to Perplexity API: {e}") from e
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error from Perplexity API ({PERPLEXITY_API_URL}): {e}. Status: {response.status if 'response' in locals() else 'N/A'}", exc_info=True)
                raise ValueError(f"Failed to parse JSON response from Perplexity API: {e}") from e

    async def refine_query(self, raw_query: str, **kwargs) -> str:
        logger.info(f"Refining query with Perplexity: '{raw_query[:50]}...'")
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_REFINE_QUERY},
                {"role": "user", "content": raw_query}
            ],
            **kwargs.get("api_params", {})
        }
        
        response_data = await self._make_perplexity_request(payload)
        
        try:
            refined_query = response_data["choices"][0]["message"]["content"].strip()
            if not refined_query:
                logger.error("Perplexity API returned an empty refined query.")
                raise ValueError("Perplexity API returned an empty refined query.")
            logger.info(f"Perplexity refined query to: '{refined_query[:50]}...'")
            return refined_query
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing refined query from Perplexity response. Response: {response_data}", exc_info=True)
            raise ValueError("Invalid response structure from Perplexity API for refine_query.") from e

    async def identify_sources(self, refined_query: str, **kwargs) -> List[str]:
        logger.info(f"Identifying sources with Perplexity for: '{refined_query[:50]}...'")
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_IDENTIFY_SOURCES},
                {"role": "user", "content": refined_query}
            ],
            **kwargs.get("api_params", {})
        }

        response_data = await self._make_perplexity_request(payload)

        try:
            content = response_data["choices"][0]["message"]["content"].strip()
            if not content:
                logger.info(f"Perplexity found no URLs for query: '{refined_query[:50]}...'")
                return [] 
            
            identified_urls = [url.strip() for url in content.split('\n') if url.strip() and (url.startswith("http://") or url.startswith("https://"))]
            logger.info(f"Perplexity identified {len(identified_urls)} sources for '{refined_query[:50]}...'. First few: {identified_urls[:3]}")
            return identified_urls
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing sources from Perplexity response. Response: {response_data}", exc_info=True)
            raise ValueError("Invalid response structure from Perplexity API for identify_sources.") from e

    async def generate_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        logger.warning(f"PerplexityClient.generate_embeddings called for {len(texts)} texts but is not implemented. kwargs: {kwargs}")
        raise NotImplementedError("PerplexityClient does not support generate_embeddings.")

    async def analyze_diff(self, old_representation: Any, new_representation: Any, **kwargs) -> Dict:
        logger.warning(f"PerplexityClient.analyze_diff called but is not implemented. kwargs: {kwargs}")
        raise NotImplementedError("PerplexityClient.analyze_diff is not implemented for now.") 