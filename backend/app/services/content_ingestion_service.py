# Placeholder for content_ingestion_service.py 

import asyncio
from typing import List, Optional, Tuple
import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.services.ai_integrations.interface import AIModelInterface
from backend.app.models.monitored_source_model import MonitoredSource # Assuming you have this
from backend.app.models.scraped_content_model import ScrapedContent
from backend.app.models.content_embedding_model import ContentEmbedding
from backend.app.schemas.content_schemas import ScrapedContentSchema, ContentEmbeddingSchema # For data validation if needed

class ContentIngestionService:
    def __init__(self, ai_model: AIModelInterface, db: Session):
        self.ai_model = ai_model
        self.db = db

    async def _scrape_website_content(self, url: str) -> Optional[str]:
        """Basic web scraping for a given URL."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status() # Raise an exception for HTTP errors
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    for script_or_style in soup(["script", "style"]):
                        script_or_style.decompose()
                    return soup.get_text(separator='\n', strip=True)
            except Exception as e:
                print(f"Error scraping {url}: {e}") # Replace with proper logging
                return None

    async def ingest_content_from_url(self, monitored_source_id: int, url: str) -> Optional[Tuple[ScrapedContent, ContentEmbedding]]:
        """
        Scrapes content from a single URL, generates embeddings, and stores them.
        Returns the ScrapedContent and ContentEmbedding objects or None if failed.
        """
        print(f"Ingesting content for URL ID {monitored_source_id}: {url}") # Replace with logging
        # 1. Scrape content
        raw_text = await self._scrape_website_content(url)
        if not raw_text:
            print(f"Failed to scrape content from {url}") # Replace with logging
            return None

        # 2. Generate embeddings
        # generate_embeddings expects a list of texts
        try:
            embeddings_list = await self.ai_model.generate_embeddings([raw_text])
            if not embeddings_list or not embeddings_list[0]:
                print(f"Failed to generate embeddings for {url}") # Replace with logging
                return None
            embedding_vector = embeddings_list[0]
        except NotImplementedError:
            print(f"generate_embeddings not implemented by the configured AI model for {url}") # Replace with logging
            return None
        except Exception as e:
            print(f"Error generating embeddings for {url}: {e}") # Replace with logging
            return None

        # 3. Store scraped content and embeddings
        try:
            db_scraped_content = ScrapedContent(
                monitored_source_id=monitored_source_id,
                scraped_at=datetime.utcnow(), # Use UTC for server-side datetimes
                raw_content=raw_text, # Store the initially scraped full text
                processed_text=raw_text # For now, processed_text is same as raw_text
            )
            self.db.add(db_scraped_content)
            self.db.flush() # To get the ID for db_scraped_content

            db_content_embedding = ContentEmbedding(
                scraped_content_id=db_scraped_content.id,
                embedding_vector=embedding_vector,
                # TODO: Get model_name from AIModelInterface or config
                model_name=getattr(self.ai_model, 'model_name', 'unknown') 
            )
            self.db.add(db_content_embedding)
            self.db.commit()
            self.db.refresh(db_scraped_content)
            self.db.refresh(db_content_embedding)
            print(f"Successfully ingested and stored content for {url}") # Replace with logging
            return db_scraped_content, db_content_embedding
        except Exception as e:
            self.db.rollback()
            print(f"Error storing content/embeddings for {url}: {e}") # Replace with logging
            return None

    async def ingest_batch(self, sources: List[Tuple[int, str]]) -> List[Optional[Tuple[ScrapedContent, ContentEmbedding]]]:
        """Ingests content from a batch of (monitored_source_id, url) tuples."""
        tasks = [self.ingest_content_from_url(source_id, url) for source_id, url in sources]
        results = await asyncio.gather(*tasks)
        return results 