from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from services.discovery_service import DiscoveryService
from dependencies import get_discovery_service

logger = structlog.get_logger()
router = APIRouter()


class DiscoveryRequest(BaseModel):
    raw_query: str = Field(..., min_length=1, max_length=500)


class DiscoveryResponse(BaseModel):
    monitorable_urls: list[str]


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_sources(
    request: DiscoveryRequest,
    discovery_service: DiscoveryService = Depends(get_discovery_service)
):
    """
    Discover monitorable sources from a natural language query.
    
    This endpoint takes a user's natural language query (e.g., "latest from OpenAI")
    and returns a list of stable, monitorable URLs that are likely to be updated
    when new relevant information appears.
    """
    logger.info("discovery_request", query=request.raw_query)
    
    try:
        sources = await discovery_service.discover_sources(request.raw_query)
        
        if not sources:
            logger.warning("no_sources_found", query=request.raw_query)
            # Return empty list instead of error for better UX
            return DiscoveryResponse(monitorable_urls=[])
        
        return DiscoveryResponse(monitorable_urls=sources)
        
    except Exception as e:
        logger.error("discovery_endpoint_error", error=str(e), query=request.raw_query, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while discovering sources: {str(e)}"
        )