# Placeholder for content_ingestion_service.py

import asyncio
import logging  # Import logging
import re  # For basic text cleaning
from datetime import datetime
from enum import Enum
from typing import ClassVar, Optional, Union  # Added Enum, Tuple, Union types
from urllib.parse import urljoin, urlparse  # For robots.txt

import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

# Attempt to import a robots.txt parser, if available. This is an optional enhancement.
try:
    import robotexclusionrulesparser
except ImportError:
    robotexclusionrulesparser = None
    logging.getLogger(__name__).info(
        "robotexclusionrulesparser not installed. Robots.txt checking will be skipped."
    )

from app.core.config import get_settings
from app.models.content_embedding_model import ContentEmbedding
from app.models.scraped_content_model import ScrapedContent
from app.services.ai_integrations.interface import AIModelInterface

settings = get_settings()
logger = logging.getLogger(__name__)  # Get logger instance

HTTP_STATUS_OK = 200  # Defined constant for status code 200


class IngestionResult(Enum):
    """Enum to represent different ingestion outcomes for better error handling."""

    SUCCESS = "success"
    ROBOTS_DISALLOWED = "robots_disallowed"
    SCRAPE_FAILED = "scrape_failed"
    EMPTY_CONTENT = "empty_content"
    EMBEDDING_FAILED = "embedding_failed"
    DB_ERROR = "db_error"


class ContentIngestionService:
    _robot_parsers_cache: ClassVar[dict] = {}  # RUF012: Cache for robot_parsers
    _USER_AGENT = settings.PROJECT_NAME + " Bot/0.1"  # Define a user agent

    def __init__(self, ai_model: AIModelInterface, db: Session):
        self.ai_model = ai_model
        self.db = db
        model_name = getattr(ai_model, "model_name", type(ai_model).__name__)
        logger.info(f"ContentIngestionService initialized with AI model: {model_name}")
        if not robotexclusionrulesparser:
            logger.info(
                "robotexclusionrulesparser not installed. "
                "Robots.txt checking will be skipped for this service instance."
            )

    async def _get_robots_parser(self, target_url: str) -> Optional[any]:
        if not robotexclusionrulesparser:
            return None  # Library not installed

        parsed_url = urlparse(target_url)
        robots_url = urljoin(
            f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt"
        )

        if robots_url in self._robot_parsers_cache:
            # TODO: Add cache expiry logic if needed
            return self._robot_parsers_cache[robots_url]

        try:
            logger.debug(f"Fetching robots.txt from: {robots_url}")
            async with aiohttp.ClientSession(
                headers={"User-Agent": self._USER_AGENT}
            ) as session:
                async with session.get(robots_url, timeout=5) as response:
                    if response.status == HTTP_STATUS_OK:  # Used constant
                        robots_txt_content = await response.text()
                        parser = robotexclusionrulesparser.RobotExclusionRulesParser()
                        parser.parse(robots_txt_content)
                        self._robot_parsers_cache[robots_url] = parser
                        logger.info(
                            f"Successfully fetched and parsed robots.txt for "
                            f"{parsed_url.netloc}"
                        )
                        return parser
                    else:
                        # No robots.txt or not accessible, assume allow
                        # (or cache a specific "allow all" state)
                        logger.warning(
                            f"robots.txt not found or not accessible "
                            f"(status: {response.status}) for {parsed_url.netloc}. "
                            f"Assuming allow."
                        )
                        self._robot_parsers_cache[robots_url] = None  # Mark as tried
                        return None
        except Exception as e:
            logger.error(
                f"Error fetching or parsing robots.txt for {robots_url}: {e}",
                exc_info=True,
            )
            self._robot_parsers_cache[robots_url] = None  # Mark as tried
            return None

    async def _is_allowed_by_robots(self, target_url: str) -> bool:
        if not robotexclusionrulesparser:  # If library isn't installed, assume allowed
            print("robotexclusionrulesparser not installed, assuming URL is allowed.")
            return True

        parser = await self._get_robots_parser(target_url)
        if parser:
            is_allowed = parser.is_allowed(self._USER_AGENT, target_url)
            logger.debug(
                f"robots.txt check for {target_url}: "
                f"{'Allowed' if is_allowed else 'Disallowed'}"
            )
            return is_allowed
        return True  # Default to allowed if robots.txt is missing or parsing fails

    def _preprocess_text(self, text: str) -> str:
        """Basic text preprocessing: normalize whitespace, remove extra newlines."""
        text = BeautifulSoup(text, "html.parser").get_text(
            separator="\n", strip=False
        )  # Ensure text is clean from HTML entities if any residual
        text = re.sub(
            r"[\t ]+", " ", text
        )  # Replace multiple spaces/tabs with a single space
        text = re.sub(
            r"\n[\n\s]*\n", "\n\n", text
        )  # Replace multiple newlines with double newlines
        text = text.strip()  # Remove leading/trailing whitespace
        return text

    async def _scrape_website_content(self, url: str) -> Optional[str]:
        """Enhanced web scraping with error handling and basic robots.txt respect."""
        if not await self._is_allowed_by_robots(url):
            logger.warning(f"Scraping disallowed by robots.txt for URL: {url}")
            # Consider raising a specific error or returning a specific status
            return "ROBOTS_DISALLOWED"

        # General politeness: add a small delay if configured
        # await asyncio.sleep(settings.SCRAPE_DELAY_SECONDS or 0.1)

        async with aiohttp.ClientSession(
            headers={"User-Agent": self._USER_AGENT}
        ) as session:
            try:
                # Add a timeout to prevent hanging indefinitely
                async with session.get(
                    url, timeout=settings.DEFAULT_REQUEST_TIMEOUT_SECONDS or 15
                ) as response:
                    # Raise an exception for HTTP errors (4xx or 5xx)
                    response.raise_for_status()
                    html_content = await response.text()

                    # Basic HTML parsing to extract text content
                    soup = BeautifulSoup(html_content, "html.parser")
                    for script_or_style in soup(
                        ["script", "style", "header", "footer", "nav", "aside"]
                    ):
                        # Remove common non-main content elements
                        script_or_style.decompose()

                    # Get text and then preprocess it
                    raw_extracted_text = soup.get_text(separator="\n", strip=False)
                    processed_text = self._preprocess_text(raw_extracted_text)
                    logger.info(
                        f"Successfully scraped and preprocessed content from {url} "
                        f"(length: {len(processed_text)} chars)."
                    )
                    return processed_text
            except aiohttp.ClientResponseError as e:
                logger.error(
                    f"HTTP error while scraping {url}: {e.status} {e.message}",
                    exc_info=False,
                )
                return None
            except asyncio.TimeoutError:
                logger.warning(f"Timeout error while scraping {url}")
                return None
            except (
                aiohttp.ClientError
            ) as e:  # Catch other aiohttp client errors (e.g., connection issues)
                logger.error(f"Client error while scraping {url}: {e}", exc_info=True)
                return None
            except Exception as e:
                logger.error(
                    f"Unexpected error scraping {url}: {type(e).__name__} {e}",
                    exc_info=True,
                )
                return None

    async def ingest_content_from_url(
        self, monitored_source_id: int, url: str
    ) -> Optional[tuple[ScrapedContent, ContentEmbedding]]:
        """
        Scrapes content from a single URL, generates embeddings, and stores them.
        Returns the ScrapedContent and ContentEmbedding objects or None if failed.
        """
        logger.info(
            f"Starting ingestion process for URL ID {monitored_source_id}: {url}"
        )

        # Record result type to reduce number of return statements
        result: Union[tuple[ScrapedContent, ContentEmbedding], IngestionResult] = (
            IngestionResult.SCRAPE_FAILED
        )

        # 1. Scrape content
        scraped_text = await self._scrape_website_content(url)

        if scraped_text is None:
            logger.warning(
                f"Failed to scrape content from {url} (or timed out/error). "
                f"Skipping ingestion."
            )
            result = IngestionResult.SCRAPE_FAILED
        elif scraped_text == "ROBOTS_DISALLOWED":
            logger.info(f"Skipping ingestion for {url} due to robots.txt exclusion.")
            result = IngestionResult.ROBOTS_DISALLOWED
        elif not scraped_text.strip():
            # Check if scraped text is empty after preprocessing
            logger.info(
                f"Scraped content from {url} is empty after preprocessing. "
                f"Skipping ingestion."
            )
            result = IngestionResult.EMPTY_CONTENT
        else:
            # For this iteration, raw_content and processed_text will be the same
            # (the preprocessed text). A more advanced setup might store the full HTML
            # as raw_content.
            processed_text_for_embedding = scraped_text

            # 2. Generate embeddings
            # generate_embeddings expects a list of texts
            try:
                logger.debug(
                    f"Generating embeddings for content from {url} "
                    f"(length: {len(processed_text_for_embedding)} chars)."
                )
                embeddings_list = await self.ai_model.generate_embeddings(
                    [processed_text_for_embedding]
                )
                if not embeddings_list or not embeddings_list[0]:
                    logger.error(
                        f"Failed to generate embeddings for {url}. "
                        f"AI model returned no/empty embeddings."
                    )
                    result = IngestionResult.EMBEDDING_FAILED
                else:
                    embedding_vector = embeddings_list[0]
                    logger.info(f"Successfully generated embeddings for {url}.")

                    # 3. Store scraped content and embeddings
                    try:
                        db_scraped_content = ScrapedContent(
                            monitored_source_id=monitored_source_id,
                            # Use UTC for server-side datetimes
                            scraped_at=datetime.utcnow(),
                            # Store preprocessed text
                            raw_content=processed_text_for_embedding,
                            processed_text=processed_text_for_embedding,
                        )
                        self.db.add(db_scraped_content)
                        self.db.flush()  # To get the ID for db_scraped_content

                        db_content_embedding = ContentEmbedding(
                            scraped_content_id=db_scraped_content.id,
                            embedding_vector=embedding_vector,
                            # TODO: Get model_name from AIModelInterface or config
                            model_name=getattr(self.ai_model, "model_name", "unknown"),
                        )
                        self.db.add(db_content_embedding)
                        self.db.commit()  # Commit transaction
                        self.db.refresh(db_scraped_content)
                        self.db.refresh(db_content_embedding)
                        logger.info(
                            f"Stored scraped content (ID: {db_scraped_content.id}) and "
                            f"embedding (ID: {db_content_embedding.id}) for {url}"
                        )
                        result = (db_scraped_content, db_content_embedding)
                    except Exception as e:  # Catch broader exceptions for DB operations
                        self.db.rollback()
                        logger.error(
                            f"Database error storing content/embeddings for {url}: "
                            f"{type(e).__name__} {e}",
                            exc_info=True,
                        )
                        result = IngestionResult.DB_ERROR
            except NotImplementedError:
                model_name = getattr(
                    self.ai_model, "model_name", type(self.ai_model).__name__
                )
                logger.error(
                    f"generate_embeddings not implemented by the AI model: "
                    f"{model_name} for {url}"
                )
                result = IngestionResult.EMBEDDING_FAILED
            except Exception as e:
                logger.error(
                    f"Error generating embeddings for {url}: {type(e).__name__} {e}",
                    exc_info=True,
                )
                result = IngestionResult.EMBEDDING_FAILED

        # Return the result based on the outcome
        if isinstance(result, tuple):
            return result
        else:
            return None

    async def ingest_batch(
        self, sources: list[tuple[int, str]]
    ) -> list[Optional[tuple[ScrapedContent, ContentEmbedding]]]:
        """Ingests content from a batch of (monitored_source_id, url) tuples."""
        logger.info(f"Starting batch ingestion for {len(sources)} sources.")
        tasks = [
            self.ingest_content_from_url(source_id, url) for source_id, url in sources
        ]
        results = await asyncio.gather(
            *tasks, return_exceptions=True
        )  # Handle exceptions from individual tasks

        # Process results, log errors if any tasks failed
        processed_results = []
        success_count = 0
        for i, res in enumerate(results):
            source_id, url = sources[i]
            if isinstance(res, Exception):
                logger.error(
                    f"Task for ingesting {url} (ID: {source_id}) failed in batch: "
                    f"{type(res).__name__} {res}",
                    exc_info=False,  # exc_info logged by individual task
                )
                processed_results.append(None)
            elif res is None:
                # ingest_content_from_url returned None (e.g. scrape failed,
                # robots, no embedding)
                logger.warning(
                    f"Task for ingesting {url} (ID: {source_id}) "
                    f"returned None in batch."
                )
                processed_results.append(None)
            else:
                success_count += 1
                processed_results.append(res)
        success_count = sum(1 for r in processed_results if r is not None)
        logger.info(
            f"Batch ingestion completed. {success_count}/{len(sources)} sources "
            f"successfully ingested."
        )
        return processed_results
