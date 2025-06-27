import asyncio
import logging
import re
from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional, Union
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from supabase import Client

try:
    import robotexclusionrulesparser
except ImportError:
    robotexclusionrulesparser = None
    logging.getLogger(__name__).info(
        "robotexclusionrulesparser not installed. Robots.txt checking will be skipped."
    )

from clients.ai_interface import AIModelInterface
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

HTTP_STATUS_OK = 200


class IngestionResult(Enum):
    """Enum to represent different ingestion outcomes for better error handling."""
    SUCCESS = "success"
    ROBOTS_DISALLOWED = "robots_disallowed"
    SCRAPE_FAILED = "scrape_failed"
    EMPTY_CONTENT = "empty_content"
    EMBEDDING_FAILED = "embedding_failed"
    DB_ERROR = "db_error"


class ContentIngestionService:
    _robot_parsers_cache: ClassVar[dict] = {}
    _USER_AGENT = "Torale Content Monitor/1.0"

    def __init__(self, ai_model: AIModelInterface, supabase: Client):
        self.ai_model = ai_model
        self.supabase = supabase
        model_name = getattr(ai_model, "model_name", type(ai_model).__name__)
        logger.info(f"ContentIngestionService initialized with AI model: {model_name}")

    async def _get_robots_parser(self, target_url: str) -> Optional[any]:
        if not robotexclusionrulesparser:
            return None

        parsed_url = urlparse(target_url)
        robots_url = urljoin(
            f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt"
        )

        if robots_url in self._robot_parsers_cache:
            return self._robot_parsers_cache[robots_url]

        try:
            logger.debug(f"Fetching robots.txt from: {robots_url}")
            async with aiohttp.ClientSession(
                headers={"User-Agent": self._USER_AGENT}
            ) as session:
                async with session.get(robots_url, timeout=5) as response:
                    if response.status == HTTP_STATUS_OK:
                        robots_txt_content = await response.text()
                        parser = robotexclusionrulesparser.RobotExclusionRulesParser()
                        parser.parse(robots_txt_content)
                        self._robot_parsers_cache[robots_url] = parser
                        logger.info(f"Successfully fetched robots.txt for {parsed_url.netloc}")
                        return parser
                    else:
                        logger.warning(f"robots.txt not found for {parsed_url.netloc}")
                        self._robot_parsers_cache[robots_url] = None
                        return None
        except Exception as e:
            logger.error(f"Error fetching robots.txt for {robots_url}: {e}")
            self._robot_parsers_cache[robots_url] = None
            return None

    async def _is_allowed_by_robots(self, target_url: str) -> bool:
        if not robotexclusionrulesparser:
            return True

        parser = await self._get_robots_parser(target_url)
        if parser:
            is_allowed = parser.is_allowed(self._USER_AGENT, target_url)
            logger.debug(f"robots.txt check for {target_url}: {'Allowed' if is_allowed else 'Disallowed'}")
            return is_allowed
        return True

    def _preprocess_text(self, text: str) -> str:
        """Basic text preprocessing: normalize whitespace, remove extra newlines."""
        text = BeautifulSoup(text, "html.parser").get_text(separator="\n", strip=False)
        text = re.sub(r"[\t ]+", " ", text)
        text = re.sub(r"\n[\n\s]*\n", "\n\n", text)
        text = text.strip()
        return text

    async def _scrape_website_content(self, url: str) -> Optional[str]:
        """Enhanced web scraping with error handling and basic robots.txt respect."""
        if not await self._is_allowed_by_robots(url):
            logger.warning(f"Scraping disallowed by robots.txt for URL: {url}")
            return "ROBOTS_DISALLOWED"

        async with aiohttp.ClientSession(
            headers={"User-Agent": self._USER_AGENT}
        ) as session:
            try:
                async with session.get(url, timeout=15) as response:
                    response.raise_for_status()
                    html_content = await response.text()

                    soup = BeautifulSoup(html_content, "html.parser")
                    for script_or_style in soup(
                        ["script", "style", "header", "footer", "nav", "aside"]
                    ):
                        script_or_style.decompose()

                    raw_extracted_text = soup.get_text(separator="\n", strip=False)
                    processed_text = self._preprocess_text(raw_extracted_text)
                    logger.info(f"Successfully scraped content from {url} (length: {len(processed_text)} chars)")
                    return processed_text
                    
            except aiohttp.ClientResponseError as e:
                logger.error(f"HTTP error while scraping {url}: {e.status} {e.message}")
                return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout error while scraping {url}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error scraping {url}: {type(e).__name__} {e}")
                return None

    async def ingest_content_from_url(self, monitored_source_id: str, url: str) -> Optional[dict]:
        """
        Scrapes content from a single URL, generates embeddings, and stores them.
        Returns the content data or None if failed.
        """
        logger.info(f"Starting ingestion for source {monitored_source_id}: {url}")

        # 1. Scrape content
        scraped_text = await self._scrape_website_content(url)

        if scraped_text is None:
            logger.warning(f"Failed to scrape content from {url}")
            return None
        elif scraped_text == "ROBOTS_DISALLOWED":
            logger.info(f"Skipping ingestion for {url} due to robots.txt exclusion")
            return None
        elif not scraped_text.strip():
            logger.info(f"Scraped content from {url} is empty after preprocessing")
            return None

        try:
            # 2. Generate embeddings
            logger.debug(f"Generating embeddings for content from {url}")
            embeddings_list = await self.ai_model.generate_embeddings([scraped_text])
            
            if not embeddings_list or not embeddings_list[0]:
                logger.error(f"Failed to generate embeddings for {url}")
                return None

            embedding_vector = embeddings_list[0]
            logger.info(f"Successfully generated embeddings for {url}")

            # 3. Store scraped content
            scraped_content_data = {
                "monitored_source_id": monitored_source_id,
                "scraped_at": datetime.utcnow().isoformat(),
                "raw_content": scraped_text,
                "processed_text": scraped_text,
            }
            
            content_result = self.supabase.table("scraped_contents").insert(scraped_content_data).execute()
            content_id = content_result.data[0]["id"]

            # 4. Store embedding
            embedding_data = {
                "scraped_content_id": content_id,
                "embedding_vector": embedding_vector,
                "model_name": getattr(self.ai_model, "model_name", "unknown"),
            }
            
            embedding_result = self.supabase.table("content_embeddings").insert(embedding_data).execute()
            
            logger.info(f"Stored content and embedding for {url}")
            return {
                "content_id": content_id,
                "embedding_id": embedding_result.data[0]["id"],
                "processed_text_length": len(scraped_text)
            }

        except Exception as e:
            logger.error(f"Error storing content/embeddings for {url}: {e}")
            return None

    async def ingest_batch(self, sources: list[tuple[str, str]]) -> list[Optional[dict]]:
        """Ingests content from a batch of (monitored_source_id, url) tuples."""
        logger.info(f"Starting batch ingestion for {len(sources)} sources")
        
        tasks = [
            self.ingest_content_from_url(source_id, url) for source_id, url in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        success_count = 0
        
        for i, res in enumerate(results):
            source_id, url = sources[i]
            if isinstance(res, Exception):
                logger.error(f"Task for {url} failed: {type(res).__name__} {res}")
                processed_results.append(None)
            elif res is None:
                logger.warning(f"Task for {url} returned None")
                processed_results.append(None)
            else:
                success_count += 1
                processed_results.append(res)

        logger.info(f"Batch ingestion completed: {success_count}/{len(sources)} successful")
        return processed_results