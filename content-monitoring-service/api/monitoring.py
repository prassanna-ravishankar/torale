import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from supabase import Client, create_client

from clients.openai_client import OpenAIClient
from config import get_settings
from services.change_detection_service import ChangeDetectionService
from services.content_ingestion_service import ContentIngestionService

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize services
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
openai_client = OpenAIClient()
content_service = ContentIngestionService(openai_client, supabase)
change_service = ChangeDetectionService(supabase, openai_client)


@router.get("/health")
async def health_check():
    """Health check endpoint for the monitoring service."""
    return {"status": "healthy", "service": "content-monitoring-service", "version": settings.VERSION}


@router.post("/process-source/{source_id}")
async def process_source(source_id: str):
    """
    Process a single monitored source - scrape content and check for changes.
    
    This endpoint performs:
    1. Content ingestion (scraping + embedding generation)
    2. Change detection (compare with previous content)
    3. Alert generation if changes detected
    """
    logger.info(f"Processing source: {source_id}")
    
    try:
        # Get source details from database
        source_query = supabase.table("monitored_sources").select("*").eq("id", source_id).eq("status", "active").execute()
        
        if not source_query.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active monitored source {source_id} not found"
            )
        
        source = source_query.data[0]
        url = source["url"]
        
        logger.info(f"Processing URL: {url} for source {source_id}")
        
        # Step 1: Ingest content
        ingestion_result = await content_service.ingest_content_from_url(source_id, url)
        
        if not ingestion_result:
            logger.warning(f"Content ingestion failed for source {source_id}")
            return {
                "source_id": source_id,
                "status": "ingestion_failed",
                "message": "Failed to scrape or process content"
            }
        
        logger.info(f"Content ingested successfully for source {source_id}")
        
        # Step 2: Check for changes
        change_result = await change_service.detect_changes_for_source(source_id, url)
        
        if change_result:
            logger.info(f"Changes detected for source {source_id}: {change_result['summary']}")
            return {
                "source_id": source_id,
                "status": "changes_detected",
                "alert_id": change_result["alert_id"],
                "summary": change_result["summary"],
                "similarity": change_result["similarity"]
            }
        else:
            logger.info(f"No significant changes detected for source {source_id}")
            return {
                "source_id": source_id,
                "status": "no_changes",
                "message": "Content processed successfully, no significant changes detected"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process source: {str(e)}"
        )


@router.post("/process-batch")
async def process_batch(source_ids: list[str]):
    """
    Process multiple monitored sources in batch.
    
    Returns a summary of processing results for each source.
    """
    logger.info(f"Processing batch of {len(source_ids)} sources")
    
    if len(source_ids) > settings.BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size exceeds maximum of {settings.BATCH_SIZE}"
        )
    
    results = []
    
    for source_id in source_ids:
        try:
            # Process each source individually
            result = await process_source(source_id)
            results.append(result)
        except HTTPException as e:
            results.append({
                "source_id": source_id,
                "status": "error",
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "source_id": source_id,
                "status": "error",
                "error": str(e)
            })
    
    # Summary statistics
    statuses = [r["status"] for r in results]
    summary = {
        "total_processed": len(results),
        "changes_detected": len([s for s in statuses if s == "changes_detected"]),
        "no_changes": len([s for s in statuses if s == "no_changes"]),
        "errors": len([s for s in statuses if s == "error"]),
        "ingestion_failed": len([s for s in statuses if s == "ingestion_failed"])
    }
    
    logger.info(f"Batch processing completed: {summary}")
    
    return {
        "summary": summary,
        "results": results
    }


@router.get("/sources/{source_id}/status")
async def get_source_status(source_id: str):
    """
    Get processing status and recent activity for a monitored source.
    """
    try:
        # Get source details
        source_query = supabase.table("monitored_sources").select("*").eq("id", source_id).execute()
        
        if not source_query.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitored source {source_id} not found"
            )
        
        source = source_query.data[0]
        
        # Get recent content ingestions
        content_query = (
            supabase.table("scraped_contents")
            .select("id, scraped_at, raw_content")
            .eq("monitored_source_id", source_id)
            .order("scraped_at", desc=True)
            .limit(5)
            .execute()
        )
        
        # Get recent alerts
        alerts_query = (
            supabase.table("change_alerts")
            .select("id, detected_at, change_summary, is_acknowledged")
            .eq("monitored_source_id", source_id)
            .order("detected_at", desc=True)
            .limit(5)
            .execute()
        )
        
        return {
            "source": source,
            "recent_content": content_query.data,
            "recent_alerts": alerts_query.data,
            "last_processed": content_query.data[0]["scraped_at"] if content_query.data else None,
            "alert_count": len(alerts_query.data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting status for source {source_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get source status: {str(e)}"
        )


@router.get("/queue/status")
async def get_queue_status():
    """
    Get overall monitoring queue status and statistics.
    """
    try:
        # Get active sources count
        active_sources = supabase.table("monitored_sources").select("id", count="exact").eq("status", "active").eq("is_deleted", False).execute()
        
        # Get recent processing stats
        recent_content = (
            supabase.table("scraped_contents")
            .select("id", count="exact")
            .gte("scraped_at", "now() - interval '24 hours'")
            .execute()
        )
        
        recent_alerts = (
            supabase.table("change_alerts")
            .select("id", count="exact")
            .gte("detected_at", "now() - interval '24 hours'")
            .execute()
        )
        
        pending_alerts = (
            supabase.table("change_alerts")
            .select("id", count="exact")
            .eq("is_acknowledged", False)
            .execute()
        )
        
        return {
            "active_sources": active_sources.count,
            "content_processed_24h": recent_content.count,
            "alerts_generated_24h": recent_alerts.count,
            "pending_alerts": pending_alerts.count,
            "service_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue status: {str(e)}"
        )