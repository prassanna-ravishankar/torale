from typing import Optional, Tuple, Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import numpy as np
from datetime import datetime
import logging # Import logging
import json # For logging dicts

from app.services.ai_integrations.interface import AIModelInterface
from app.models.monitored_source_model import MonitoredSource
from app.models.content_embedding_model import ContentEmbedding
from app.models.change_alert_model import ChangeAlert
from app.core.config import get_settings # For similarity threshold
from app.models.scraped_content_model import ScrapedContent

settings = get_settings()
logger = logging.getLogger(__name__) # Get logger instance

class ChangeDetectionService:
    def __init__(self, db: Session, ai_model: Optional[AIModelInterface] = None):
        self.db = db
        self.ai_model = ai_model # Optional: only needed for analyze_diff
        ai_model_name = getattr(ai_model, 'model_name', type(ai_model).__name__) if ai_model else "None"
        logger.info(f"ChangeDetectionService initialized with AI model: {ai_model_name}")

    def _calculate_similarity(self, emb1: List[float], emb2: List[float]) -> float:
        """Calculates cosine similarity between two embedding vectors."""
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)

    async def detect_changes_for_source(self, monitored_source_id: int, monitored_source_url: str) -> Optional[ChangeAlert]:
        """
        Detects changes for a single monitored source by comparing the latest two embeddings.
        Creates a ChangeAlert if a significant change is detected.
        """
        logger.info(f"Starting change detection for source ID {monitored_source_id} ({monitored_source_url})")
        try:
            latest_embeddings = (
                self.db.query(ContentEmbedding)
                .join(ContentEmbedding.scraped_content)
                .filter(ScrapedContent.monitored_source_id == monitored_source_id)
                .order_by(desc(ScrapedContent.scraped_at))
                .limit(2)
                .all()
            )
        except Exception as e:
            logger.error(f"Database error fetching embeddings for source ID {monitored_source_id}: {e}", exc_info=True)
            return None

        if len(latest_embeddings) < 2:
            logger.info(f"Not enough embeddings ({len(latest_embeddings)}) to compare for source ID {monitored_source_id}")
            return None

        current_embedding = latest_embeddings[0]
        previous_embedding = latest_embeddings[1]
        logger.debug(f"Comparing embeddings: current ID {current_embedding.id} (scraped: {current_embedding.scraped_content.scraped_at}) vs previous ID {previous_embedding.id} (scraped: {previous_embedding.scraped_content.scraped_at})")

        try:
            similarity = self._calculate_similarity(current_embedding.embedding_vector, previous_embedding.embedding_vector)
        except Exception as e:
            logger.error(f"Error calculating similarity for source ID {monitored_source_id} between embeddings {current_embedding.id} and {previous_embedding.id}: {e}", exc_info=True)
            return None
        
        similarity_threshold = settings.DEFAULT_SIMILARITY_THRESHOLD
        logger.info(f"Similarity for source ID {monitored_source_id}: {similarity:.4f} (Threshold: {similarity_threshold})")

        if similarity < similarity_threshold:
            logger.info(f"Significant change detected for source ID {monitored_source_id} ({monitored_source_url}). Similarity {similarity:.4f} < {similarity_threshold}")
            change_summary = f"Content similarity dropped to {similarity:.2f} (below threshold of {similarity_threshold})"
            change_details = {
                "current_embedding_id": current_embedding.id,
                "previous_embedding_id": previous_embedding.id,
                "current_scraped_at": current_embedding.scraped_content.scraped_at.isoformat(),
                "previous_scraped_at": previous_embedding.scraped_content.scraped_at.isoformat(),
                "similarity_score": similarity
            }

            if self.ai_model and hasattr(self.ai_model, 'analyze_diff'):
                logger.info(f"Attempting AI diff analysis for source ID {monitored_source_id}")
                try:
                    old_text = previous_embedding.scraped_content.processed_text or previous_embedding.scraped_content.raw_content
                    new_text = current_embedding.scraped_content.processed_text or current_embedding.scraped_content.raw_content
                    
                    diff_analysis = await self.ai_model.analyze_diff(
                        old_representation=old_text,
                        new_representation=new_text
                    )
                    change_summary = diff_analysis.get("summary", change_summary)
                    change_details.update(diff_analysis.get("details", {}))
                    logger.info(f"AI diff analysis successful for source ID {monitored_source_id}. Summary: '{change_summary[:100]}...'")
                except NotImplementedError:
                    logger.warning(f"analyze_diff not implemented by AI model {getattr(self.ai_model, 'model_name', type(self.ai_model).__name__)}. Using basic similarity summary.")
                except Exception as e:
                    logger.error(f"Error during AI diff analysis for source ID {monitored_source_id}: {e}", exc_info=True)
            else:
                 logger.info("AI model not configured or does not support analyze_diff. Skipping AI analysis.")
            
            try:
                db_alert = ChangeAlert(
                    monitored_source_id=monitored_source_id,
                    detected_at=datetime.utcnow(),
                    change_summary=change_summary,
                    change_details=change_details,
                )
                self.db.add(db_alert)
                self.db.commit()
                self.db.refresh(db_alert)
                logger.info(f"ChangeAlert {db_alert.id} created for source ID {monitored_source_id}")
                return db_alert
            except Exception as e:
                self.db.rollback()
                logger.error(f"Database error creating ChangeAlert for source ID {monitored_source_id}: {e}", exc_info=True)
                return None
        else:
            logger.info(f"No significant change detected for source ID {monitored_source_id}")
            return None 