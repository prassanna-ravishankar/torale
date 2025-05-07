from typing import Optional, Tuple, Any, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
import numpy as np
from datetime import datetime

from backend.app.services.ai_integrations.interface import AIModelInterface
from backend.app.models.monitored_source_model import MonitoredSource
from backend.app.models.content_embedding_model import ContentEmbedding
from backend.app.models.change_alert_model import ChangeAlert
from backend.app.core.config import get_settings # For similarity threshold
from backend.app.models.scraped_content_model import ScrapedContent

settings = get_settings()

class ChangeDetectionService:
    def __init__(self, db: Session, ai_model: Optional[AIModelInterface] = None):
        self.db = db
        self.ai_model = ai_model # Optional: only needed for analyze_diff

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
        # 1. Get the latest two embeddings for the source
        latest_embeddings = (
            self.db.query(ContentEmbedding)
            .join(ContentEmbedding.scraped_content)
            .filter(ScrapedContent.monitored_source_id == monitored_source_id)
            .order_by(desc(ScrapedContent.scraped_at))
            .limit(2)
            .all()
        )

        if len(latest_embeddings) < 2:
            print(f"Not enough embeddings to compare for source ID {monitored_source_id}") # Logging
            return None

        current_embedding = latest_embeddings[0]
        previous_embedding = latest_embeddings[1]

        # 2. Compare embeddings
        # Assuming embedding_vector is a list of floats (JSON in DB)
        similarity = self._calculate_similarity(current_embedding.embedding_vector, previous_embedding.embedding_vector)
        
        print(f"Similarity for source ID {monitored_source_id}: {similarity}") # Logging

        # 3. Determine if change is significant
        # Threshold from config, e.g., if similarity < 0.9, it's a significant change
        similarity_threshold = settings.DEFAULT_SIMILARITY_THRESHOLD
        if similarity < similarity_threshold:
            print(f"Significant change detected for source ID {monitored_source_id} ({monitored_source_url})") # Logging
            change_summary = f"Content similarity dropped to {similarity:.2f} (below threshold of {similarity_threshold})"
            change_details = {
                "current_embedding_id": current_embedding.id,
                "previous_embedding_id": previous_embedding.id,
                "current_scraped_at": current_embedding.scraped_content.scraped_at.isoformat(),
                "previous_scraped_at": previous_embedding.scraped_content.scraped_at.isoformat(),
                "similarity_score": similarity
            }

            # 4. Optional: Use LLM to analyze/summarize diff
            if self.ai_model and hasattr(self.ai_model, 'analyze_diff'):
                try:
                    # We need representations of old/new content. 
                    # For now, let's assume we might pass raw texts or some other representation.
                    # This part needs careful design based on what analyze_diff expects.
                    # Let's assume it might take the raw texts of the associated ScrapedContent.
                    old_text = previous_embedding.scraped_content.processed_text or previous_embedding.scraped_content.raw_content
                    new_text = current_embedding.scraped_content.processed_text or current_embedding.scraped_content.raw_content
                    
                    diff_analysis = await self.ai_model.analyze_diff(
                        old_representation=old_text, 
                        new_representation=new_text
                    )
                    change_summary = diff_analysis.get("summary", change_summary)
                    change_details.update(diff_analysis.get("details", {}))
                except NotImplementedError:
                    print(f"analyze_diff not implemented by AI model. Using basic summary.") # Logging
                except Exception as e:
                    print(f"Error during AI diff analysis: {e}") # Logging
            
            # 5. Create and store ChangeAlert
            try:
                db_alert = ChangeAlert(
                    monitored_source_id=monitored_source_id,
                    detected_at=datetime.utcnow(),
                    change_summary=change_summary,
                    change_details=change_details,
                    # old_scraped_content_id=previous_embedding.scraped_content_id,
                    # new_scraped_content_id=current_embedding.scraped_content_id,
                )
                self.db.add(db_alert)
                self.db.commit()
                self.db.refresh(db_alert)
                print(f"ChangeAlert {db_alert.id} created for source ID {monitored_source_id}") # Logging
                return db_alert
            except Exception as e:
                self.db.rollback()
                print(f"Error creating ChangeAlert for source ID {monitored_source_id}: {e}") # Logging
                return None
        else:
            print(f"No significant change detected for source ID {monitored_source_id}") # Logging
            return None 