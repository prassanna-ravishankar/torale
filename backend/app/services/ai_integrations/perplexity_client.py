import json
import logging
import re
from typing import Optional

import aiohttp
import structlog

from .interface import AIModelInterface

logger = structlog.get_logger()

# Constants
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# System prompts
SYSTEM_PROMPT_REFINE_QUERY = """You are an AI assistant that refines a user's general interest into a focused search query.
The user wants to monitor a topic, entity, or type of information online for any significant changes or new updates.
Your task is to transform their initial interest into a concise search query string.
This refined query should be designed to help another AI find one or more stable, central webpages (e.g., official news sections, main product/service pages, primary blog URLs, key community hubs, or official announcement channels) that are most likely to be updated when new, relevant information appears.
Output *only* the refined search query string. No explanations or labels.

Example User Interest: "latest from OpenAI"
Example Refined Query Output: "OpenAI official announcements or blog"

Example User Interest: "Sony camera rumors"
Example Refined Query Output: "Sony camera news and rumor hubs"

Example User Interest: "discounts in tkmaxx"
Example Refined Query Output: "TK Maxx official offers and deals page"
"""

SYSTEM_PROMPT_IDENTIFY_SOURCES = """Find stable URLs for monitoring updates on this topic.

You must respond with ONLY a list of URLs, nothing else.
Format: One URL per line, with https:// prefix.
Maximum: 5 URLs.

Good URLs are:
- Official company blogs/news pages
- Documentation changelogs  
- News sites with dedicated sections
- Developer/API documentation

Bad URLs are:
- Specific articles or posts
- Social media posts
- Personal blogs

RESPOND ONLY WITH URLs, NO OTHER TEXT."""


class PerplexityClient(AIModelInterface):
    def __init__(
        self, api_key: str, model: str = "sonar"
    ):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        logger.info("perplexity_client_initialized", model=model)

    async def _make_request(self, payload: dict) -> dict:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                logger.debug("perplexity_request", payload_size=len(str(payload)))
                async with session.post(PERPLEXITY_API_URL, json=payload) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error("perplexity_client_error", error=str(e))
                raise ConnectionError(f"Failed to connect to Perplexity API: {e}") from e
            except json.JSONDecodeError as e:
                logger.error("perplexity_json_error", error=str(e))
                raise ValueError(f"Failed to parse JSON response from Perplexity API: {e}") from e

    async def refine_query(self, raw_query: str, **kwargs) -> str:
        logger.info("refining_query", query_length=len(raw_query))
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_REFINE_QUERY},
                {"role": "user", "content": raw_query},
            ],
        }

        response_data = await self._make_request(payload)

        try:
            refined_query = response_data["choices"][0]["message"]["content"].strip()
            if not refined_query:
                raise ValueError("Perplexity API returned an empty refined query")
            
            logger.info("query_refined", refined_length=len(refined_query))
            return refined_query
        except (KeyError, IndexError) as e:
            logger.error("perplexity_response_parse_error", error=str(e))
            raise ValueError("Invalid response structure from Perplexity API") from e

    async def identify_sources(self, refined_query: str, **kwargs) -> list[str]:
        logger.info("identifying_sources", query_length=len(refined_query))
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_IDENTIFY_SOURCES},
                {"role": "user", "content": refined_query},
            ],
        }

        response_data = await self._make_request(payload)

        try:
            content = response_data["choices"][0]["message"]["content"].strip()
            if not content:
                logger.info("no_sources_found")
                return []

            # Extract URLs using regex pattern
            url_pattern = r'https?://[^\s\[\]<>"]+'
            found_urls = re.findall(url_pattern, content)
            
            # Also check for domain-only URLs on separate lines
            identified_urls = []
            
            # Add regex-found URLs
            for url in found_urls:
                if len(url) > 10 and "." in url:  # Basic validation
                    identified_urls.append(url)
            
            # If no regex URLs found, try line-by-line parsing
            if not identified_urls:
                for line in content.split("\n"):
                    url = line.strip()
                    if url and ("." in url or url.startswith("http")):
                        # Clean up URL
                        if url.startswith("- "):
                            url = url[2:]
                        if not url.startswith(("http://", "https://")):
                            url = f"https://{url}"
                        # Basic URL validation
                        if "." in url and len(url) > 7:  # Minimum valid URL length
                            identified_urls.append(url)
            
            # Limit to 5 URLs and remove duplicates
            unique_urls = []
            seen = set()
            for url in identified_urls[:5]:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            logger.info("sources_identified", count=len(unique_urls))
            return unique_urls
        except (KeyError, IndexError) as e:
            logger.error("perplexity_response_parse_error", error=str(e))
            raise ValueError("Invalid response structure from Perplexity API") from e