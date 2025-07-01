import logging
from datetime import datetime
from typing import Optional

import numpy as np
from supabase import Client

from clients.ai_interface import AIModelInterface
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MIN_EMBEDDINGS_FOR_COMPARISON = 2


class ChangeDetectionService:
    def __init__(self, supabase: Client, ai_model: Optional[AIModelInterface] = None):
        self.supabase = supabase
        self.ai_model = ai_model
        ai_model_name = (
            getattr(ai_model, "model_name", type(ai_model).__name__)
            if ai_model
            else "None"
        )
        logger.info(f"ChangeDetectionService initialized with AI model: {ai_model_name}")

    def _calculate_similarity(self, emb1: list[float], emb2: list[float]) -> float:
        """Calculates cosine similarity between two embedding vectors."""
        vec1 = np.array(emb1)
        vec2 = np.array(emb2)
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)

    async def detect_changes_for_source(self, monitored_source_id: str, monitored_source_url: str) -> Optional[dict]:
        """
        Detects changes by comparing the latest two embeddings.
        Creates a ChangeAlert if a significant change is detected.
        """
        logger.info(f"Starting change detection for source {monitored_source_id} ({monitored_source_url})")
        
        try:
            # Get latest embeddings with their content
            embeddings_query = (
                self.supabase.table("content_embeddings")
                .select("*, scraped_contents!inner(*)")
                .eq("scraped_contents.monitored_source_id", monitored_source_id)
                .order("scraped_contents.scraped_at", desc=True)
                .limit(2)
                .execute()
            )
            
            latest_embeddings = embeddings_query.data
            
        except Exception as e:
            logger.error(f"Database error fetching embeddings for source {monitored_source_id}: {e}")
            return None

        if len(latest_embeddings) < MIN_EMBEDDINGS_FOR_COMPARISON:
            logger.info(f"Not enough embeddings ({len(latest_embeddings)}) for source {monitored_source_id}")
            return None

        current_embedding = latest_embeddings[0]
        previous_embedding = latest_embeddings[1]
        
        logger.debug(f"Comparing embeddings: current vs previous for source {monitored_source_id}")

        try:
            similarity = self._calculate_similarity(
                current_embedding["embedding_vector"], 
                previous_embedding["embedding_vector"]
            )
        except Exception as e:
            logger.error(f"Error calculating similarity for source {monitored_source_id}: {e}")
            return None

        similarity_threshold = getattr(settings, 'DEFAULT_SIMILARITY_THRESHOLD', 0.85)
        logger.info(f"Similarity for source {monitored_source_id}: {similarity:.4f} (Threshold: {similarity_threshold})")

        if similarity < similarity_threshold:
            logger.info(f"Significant change detected for source {monitored_source_id}")
            
            change_summary = f"Content similarity dropped to {similarity:.2f} (below threshold of {similarity_threshold})"
            change_details = {
                "current_embedding_id": current_embedding["id"],
                "previous_embedding_id": previous_embedding["id"],
                "current_scraped_at": current_embedding["scraped_contents"]["scraped_at"],
                "previous_scraped_at": previous_embedding["scraped_contents"]["scraped_at"],
                "similarity_score": similarity,
            }

            # AI analysis if available
            if self.ai_model and hasattr(self.ai_model, "analyze_diff"):
                logger.info(f"Attempting AI diff analysis for source {monitored_source_id}")
                try:
                    old_text = (
                        previous_embedding["scraped_contents"]["processed_text"] 
                        or previous_embedding["scraped_contents"]["raw_content"]
                    )
                    new_text = (
                        current_embedding["scraped_contents"]["processed_text"] 
                        or current_embedding["scraped_contents"]["raw_content"]
                    )

                    diff_analysis = await self.ai_model.analyze_diff(
                        old_representation=old_text, 
                        new_representation=new_text
                    )
                    change_summary = diff_analysis.get("summary", change_summary)
                    change_details.update(diff_analysis.get("details", {}))
                    logger.info(f"AI diff analysis successful for source {monitored_source_id}")
                    
                except Exception as e:
                    logger.error(f"Error during AI diff analysis for source {monitored_source_id}: {e}")

            # Get user_id from monitored_sources table
            try:
                source_query = (
                    self.supabase.table("monitored_sources")
                    .select("user_id")
                    .eq("id", monitored_source_id)
                    .execute()
                )
                
                if not source_query.data:
                    logger.error(f"Could not find monitored source {monitored_source_id}")
                    return None
                    
                user_id = source_query.data[0]["user_id"]

                # Create change alert
                alert_data = {
                    "user_id": user_id,
                    "monitored_source_id": monitored_source_id,
                    "detected_at": datetime.utcnow().isoformat(),
                    "change_summary": change_summary,
                    "change_details": change_details,
                    "notification_sent": False,
                    "notification_retry_count": 0
                }
                
                alert_result = self.supabase.table("change_alerts").insert(alert_data).execute()
                alert_id = alert_result.data[0]["id"]
                
                logger.info(f"ChangeAlert {alert_id} created for source {monitored_source_id}")
                return {
                    "alert_id": alert_id,
                    "summary": change_summary,
                    "similarity": similarity,
                    "threshold": similarity_threshold
                }
                
            except Exception as e:
                logger.error(f"Database error creating ChangeAlert for source {monitored_source_id}: {e}")
                return None
        else:
            logger.info(f"No significant change detected for source {monitored_source_id}")
            return None