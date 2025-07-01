import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api.deps import get_current_user, get_supabase_with_auth, User
from app.core.constants import (
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_NOT_FOUND,
)
from app.schemas.monitoring_schemas import (
    MonitoredSourceCreate,
    MonitoredSourceUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Monitored Sources CRUD Endpoints (converted to Supabase) ---


@router.post(
    "/monitored-sources/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitored_source(
    source_in: MonitoredSourceCreate,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Create a new monitored source for the authenticated user using Supabase client.
    
    Each user can monitor the same URL independently - sources are user-scoped.
    """
    logger.info(
        f"User {current_user.id} creating monitored source: "
        f"{source_in.model_dump(exclude_none=True)}"
    )
    
    try:
        # Check if user already monitors this URL
        existing = supabase.table("monitored_sources").select("id").eq("user_id", current_user.id).eq("url", str(source_in.url)).eq("is_deleted", False).execute()
        
        if existing.data:
            logger.warning(
                f"User {current_user.id} attempted to create duplicate source: {source_in.url}"
            )
            raise HTTPException(
                status_code=HTTP_STATUS_BAD_REQUEST,
                detail=f"You are already monitoring URL '{source_in.url}'.",
            )

        # Create the new monitored source
        new_source = {
            "user_id": current_user.id,
            "user_query_id": source_in.user_query_id,  # Optional link to original query
            "url": str(source_in.url),
            "name": source_in.name,
            "source_type": source_in.source_type or "website",
            "check_interval_seconds": source_in.check_interval_seconds or 3600,
            "keywords_json": json.dumps(source_in.keywords) if source_in.keywords else None,
            "config_json": json.dumps(source_in.config) if source_in.config else None,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_deleted": False,
        }
        
        result = supabase.table("monitored_sources").insert(new_source).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to create monitored source.",
            )
        
        logger.info(
            f"User {current_user.id} successfully created monitored source "
            f"ID {result.data[0]['id']} for URL: {result.data[0]['url']}"
        )
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Error creating monitored source for user {current_user.id}, "
            f"URL {source_in.url}: {e}"
        )
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to create monitored source.",
        ) from e


@router.get("/monitored-sources/", response_model=list[dict])
async def list_monitored_sources(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    List all monitored sources for the authenticated user using Supabase client.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    logger.info(
        f"User {current_user.id} listing monitored sources (skip={skip}, limit={limit})"
    )
    
    try:
        result = supabase.table("monitored_sources").select("*").eq("user_id", current_user.id).eq("is_deleted", False).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        logger.info(f"User {current_user.id} has {len(result.data)} monitored sources.")
        return result.data
        
    except Exception as e:
        logger.exception(f"Error listing sources for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to list monitored sources.",
        ) from e


@router.get("/monitored-sources/{source_id}", response_model=dict)
async def get_monitored_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Get a specific monitored source by ID using Supabase client.
    
    Only returns sources that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} requesting monitored source ID: {source_id}")
    
    try:
        result = supabase.table("monitored_sources").select("*").eq("id", source_id).eq("user_id", current_user.id).eq("is_deleted", False).execute()
        
        if not result.data:
            logger.warning(
                f"User {current_user.id} requested non-existent source ID {source_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Monitored source not found"
            )
        
        logger.info(f"Returning source ID {source_id} to user {current_user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitored source.",
        ) from e


@router.put("/monitored-sources/{source_id}", response_model=dict)
async def update_monitored_source(
    source_id: str,
    source_in: MonitoredSourceUpdate,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Update a monitored source using Supabase client.
    
    Only allows updates to sources that belong to the authenticated user.
    """
    logger.info(
        f"User {current_user.id} updating source ID {source_id} with: "
        f"{source_in.model_dump(exclude_unset=True)}"
    )
    
    try:
        # First check if the source exists and belongs to the user
        existing = supabase.table("monitored_sources").select("id").eq("id", source_id).eq("user_id", current_user.id).eq("is_deleted", False).execute()
        
        if not existing.data:
            logger.warning(
                f"User {current_user.id} tried to update non-existent source ID {source_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitored source not found"
            )
        
        # Build update data from the provided fields
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        
        if source_in.name is not None:
            update_data["name"] = source_in.name
        if source_in.source_type is not None:
            update_data["source_type"] = source_in.source_type
        if source_in.check_interval_seconds is not None:
            update_data["check_interval_seconds"] = source_in.check_interval_seconds
        if source_in.keywords is not None:
            update_data["keywords_json"] = json.dumps(source_in.keywords) if source_in.keywords else None
        if source_in.config is not None:
            update_data["config_json"] = json.dumps(source_in.config) if source_in.config else None
        if source_in.status is not None:
            update_data["status"] = source_in.status
        
        # Update the source
        result = supabase.table("monitored_sources").update(update_data).eq("id", source_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to update monitored source"
            )
        
        logger.info(f"User {current_user.id} successfully updated source ID {source_id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to update monitored source.",
        ) from e


@router.delete("/monitored-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitored_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Delete (soft delete) a monitored source using Supabase client.
    
    Only allows deletion of sources that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} deleting source ID: {source_id}")
    
    try:
        # First check if the source exists and belongs to the user
        existing = supabase.table("monitored_sources").select("id").eq("id", source_id).eq("user_id", current_user.id).eq("is_deleted", False).execute()
        
        if not existing.data:
            logger.warning(
                f"User {current_user.id} tried to delete non-existent source ID {source_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitored source not found"
            )
        
        # Soft delete the source
        result = supabase.table("monitored_sources").update({
            "is_deleted": True,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", source_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to delete monitored source"
            )
        
        logger.info(f"User {current_user.id} successfully deleted source ID {source_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to delete monitored source.",
        ) from e


# --- Alerts Endpoints (converted to Supabase) ---


@router.get("/alerts/", response_model=list[dict])
async def list_change_alerts(
    skip: int = 0,
    limit: int = 100,
    monitored_source_id: Optional[str] = None,
    is_acknowledged: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    List change alerts for the authenticated user using Supabase client.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **monitored_source_id**: Filter by specific monitored source
    - **is_acknowledged**: Filter by acknowledgment status
    """
    logger.info(
        f"User {current_user.id} listing change alerts (skip={skip}, limit={limit})"
    )
    
    try:
        # Build query using Supabase client
        query = supabase.table("change_alerts").select("*").eq("user_id", current_user.id)
        
        # Add filters if provided
        if monitored_source_id:
            query = query.eq("monitored_source_id", monitored_source_id)
        if is_acknowledged is not None:
            query = query.eq("is_acknowledged", is_acknowledged)
        
        # Add pagination and ordering
        result = query.order("detected_at", desc=True).range(skip, skip + limit - 1).execute()
        
        logger.info(f"User {current_user.id} has {len(result.data)} change alerts.")
        return result.data
        
    except Exception as e:
        logger.exception(f"Error listing alerts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to list change alerts.",
        ) from e


@router.get("/alerts/{alert_id}", response_model=dict)
async def get_change_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Get a specific change alert by ID using Supabase client.
    
    Only returns alerts that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} requesting change alert ID: {alert_id}")
    
    try:
        result = supabase.table("change_alerts").select("*").eq("id", alert_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            logger.warning(
                f"User {current_user.id} requested non-existent alert ID {alert_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Change alert not found"
            )
        
        logger.info(f"Returning alert ID {alert_id} to user {current_user.id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting alert {alert_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to get change alert.",
        ) from e


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_change_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Acknowledge a change alert using Supabase client.
    
    Only allows acknowledging alerts that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} acknowledging alert ID: {alert_id}")
    
    try:
        # First check if the alert exists and belongs to the user
        existing = supabase.table("change_alerts").select("id").eq("id", alert_id).eq("user_id", current_user.id).execute()
        
        if not existing.data:
            logger.warning(
                f"User {current_user.id} tried to acknowledge non-existent alert ID {alert_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Change alert not found"
            )
        
        # Update the alert
        result = supabase.table("change_alerts").update({
            "is_acknowledged": True,
            "acknowledged_at": datetime.utcnow().isoformat()
        }).eq("id", alert_id).eq("user_id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
                detail="Failed to acknowledge alert"
            )
        
        logger.info(f"User {current_user.id} successfully acknowledged alert ID {alert_id}")
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error acknowledging alert {alert_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge change alert.",
        ) from e


# --- Content Processing Endpoints (calls Content Monitoring Service) ---

@router.post("/process-source/{source_id}", response_model=dict)
async def process_monitored_source(
    source_id: str,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Trigger content processing for a monitored source via Content Monitoring Service.
    
    This will:
    1. Scrape content from the source URL
    2. Generate embeddings
    3. Detect changes compared to previous content
    4. Create alerts if significant changes are found
    """
    logger.info(f"User {current_user.id} requesting processing for source {source_id}")
    
    try:
        # Verify the source belongs to the user
        source_query = supabase.table("monitored_sources").select("*").eq("id", source_id).eq("user_id", current_user.id).eq("is_deleted", False).execute()
        
        if not source_query.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitored source not found"
            )
        
        # Call Content Monitoring Service
        import aiohttp
        import os
        
        monitoring_service_url = os.getenv("CONTENT_MONITORING_SERVICE_URL", "http://localhost:8002")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{monitoring_service_url}/api/v1/process-source/{source_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Content processing completed for source {source_id}: {result['status']}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Content Monitoring Service error for source {source_id}: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Content processing service error: {response.status}"
                    )
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing source {source_id} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to process monitored source.",
        ) from e


@router.post("/process-batch", response_model=dict)
async def process_multiple_sources(
    source_ids: list[str],
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
):
    """
    Trigger batch processing for multiple monitored sources via Content Monitoring Service.
    
    Only processes sources that belong to the authenticated user.
    """
    logger.info(f"User {current_user.id} requesting batch processing for {len(source_ids)} sources")
    
    if len(source_ids) > 10:  # Reasonable batch limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch size cannot exceed 10 sources"
        )
    
    try:
        # Verify all sources belong to the user
        sources_query = supabase.table("monitored_sources").select("id").eq("user_id", current_user.id).eq("is_deleted", False).in_("id", source_ids).execute()
        
        verified_ids = [s["id"] for s in sources_query.data]
        invalid_ids = set(source_ids) - set(verified_ids)
        
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or unauthorized source IDs: {list(invalid_ids)}"
            )
        
        # Call Content Monitoring Service
        import aiohttp
        import os
        
        monitoring_service_url = os.getenv("CONTENT_MONITORING_SERVICE_URL", "http://localhost:8002")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{monitoring_service_url}/api/v1/process-batch",
                json=verified_ids
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Batch processing completed for user {current_user.id}: {result['summary']}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Content Monitoring Service batch error: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Content processing service error: {response.status}"
                    )
                    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error processing batch for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to process sources batch.",
        ) from e