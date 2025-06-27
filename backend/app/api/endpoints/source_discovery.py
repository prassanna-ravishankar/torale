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
from app.schemas.source_discovery_schemas import (
    RawQueryInput,
    MonitoredURLOutput,
)
from app.services.source_discovery_service import SourceDiscoveryService
from app.api.deps import get_source_discovery_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/discover-sources/", response_model=MonitoredURLOutput)
async def discover_sources(
    request: RawQueryInput,
    current_user: User = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_with_auth),
    discovery_service: SourceDiscoveryService = Depends(get_source_discovery_service),
):
    """
    Discover sources based on a user query.
    
    This endpoint analyzes the user's natural language query and suggests
    relevant sources to monitor. It can use either a microservice or
    the legacy AI model approach depending on configuration.
    """
    logger.info(
        f"User {current_user.id} requesting source discovery for query: {request.raw_query}"
    )
    
    try:
        # Use the discovery service to find sources
        discovered_urls = await discovery_service.discover_sources(request.raw_query)
        
        # Store the discovery request for future reference
        discovery_record = {
            "user_id": current_user.id,
            "query_text": request.raw_query,
            "discovered_urls_json": json.dumps(discovered_urls),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # TODO: Store this in a source_discovery_requests table
        # For now, we'll just log it
        logger.info(
            f"User {current_user.id} discovered {len(discovered_urls)} sources: {discovered_urls}"
        )
        
        return MonitoredURLOutput(monitorable_urls=discovered_urls)
        
    except ConnectionError as e:
        logger.exception(f"Failed to connect to discovery service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Discovery service is temporarily unavailable. Please try again later.",
        ) from e
    except Exception as e:
        logger.exception(f"Error discovering sources for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            detail="Failed to discover sources.",
        ) from e