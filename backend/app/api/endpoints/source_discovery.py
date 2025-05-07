from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
import logging # Import logging

from app.services.ai_integrations.interface import AIModelInterface
from app.services.source_discovery_service import SourceDiscoveryService
from app.schemas.source_discovery_schemas import RawQueryInput, MonitoredURLOutput
from app.core.config import get_settings, Settings
from app.api.dependencies import get_source_discovery_ai_model

router = APIRouter()
logger = logging.getLogger(__name__) # Get logger instance
# settings = get_settings() # Settings instance available via Depends(get_settings)

# --- Dependency Injection for AI Models (Now largely handled by common dependencies.py) ---

# Dependency to get SourceDiscoveryService, using the common AI model provider
def get_source_discovery_service(
    ai_model: AIModelInterface = Depends(get_source_discovery_ai_model) # Use the centralized DI
) -> SourceDiscoveryService:
    return SourceDiscoveryService(ai_model=ai_model)

# --- API Endpoints ---
@router.post("/discover-sources/", response_model=MonitoredURLOutput)
async def discover_sources_endpoint(
    query_input: RawQueryInput,
    service: SourceDiscoveryService = Depends(get_source_discovery_service),
    # s: Settings = Depends(get_settings) # Can still inject settings if directly needed for other logic
):
    logger.info(f"Received request to discover sources for query: '{query_input.raw_query[:50]}...'")
    """
    Accepts a raw user query, refines it, and identifies monitorable source URLs.
    """
    try:
        refine_api_params = {}
        identify_api_params = {}
        # Example of how you might use settings to pass model choices to the client, if desired:
        # settings_val = get_settings() # or inject s: Settings = Depends(get_settings)
        # if settings_val.PERPLEXITY_REFINE_QUERY_MODEL: 
        #     refine_api_params["model"] = settings_val.PERPLEXITY_REFINE_QUERY_MODEL
        # if settings_val.PERPLEXITY_IDENTIFY_SOURCES_MODEL:
        #     identify_api_params["model"] = settings_val.PERPLEXITY_IDENTIFY_SOURCES_MODEL

        monitorable_urls = await service.discover_sources(
            raw_query=query_input.raw_query,
            refine_kwargs={"api_params": refine_api_params},
            identify_kwargs={"api_params": identify_api_params}
        )
        logger.info(f"Successfully discovered {len(monitorable_urls)} sources for query '{query_input.raw_query[:50]}...'")
        return MonitoredURLOutput(monitorable_urls=monitorable_urls)
    except ConnectionError as e:
        logger.error(f"Connection error during source discovery API call: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Could not connect to AI provider: {e}")
    except ValueError as e:
        logger.error(f"Value error during source discovery API call: {e}", exc_info=True)
        if "API key" in str(e) or "Invalid response structure" in str(e) or "service is not configured" in str(e):
             raise HTTPException(status_code=500, detail=f"AI provider error: {e}")
        else:
             raise HTTPException(status_code=400, detail=f"Invalid input or parameters: {e}")
    except NotImplementedError as e:
        logger.error(f"AI functionality not implemented during source discovery API call: {e}", exc_info=True)
        raise HTTPException(status_code=501, detail=f"AI functionality not implemented: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error in discover_sources_endpoint for query '{query_input.raw_query[:50]}...'") # Use logger.exception to include stack trace
        raise HTTPException(status_code=500, detail="Internal server error during source discovery.") 