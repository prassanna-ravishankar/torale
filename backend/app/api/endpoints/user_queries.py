from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_source_discovery_ai_model,
)  # Need the AI model getter
from app.core.db import get_db
from app.models import user_query_model
from app.schemas import user_query_schemas
from app.services.ai_integrations.interface import AIModelInterface  # For type hinting
from app.services.source_discovery_service import (
    SourceDiscoveryService,
)  # Keep this import

# Import the processing service and the AI model dependency getter
from app.services.user_query_processing_service import UserQueryProcessingService

router = APIRouter()


@router.post(
    "/",
    response_model=user_query_schemas.UserQueryInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_query(
    query_in: user_query_schemas.UserQueryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # Remove discovery_service dependency from endpoint signature
    ai_model_for_discovery: AIModelInterface = Depends(
        get_source_discovery_ai_model
    ),  # Get the AI model needed for discovery
) -> Any:
    """
    Create a new user query and schedule background processing.

    - **raw_query**: The user's query string.
    - **config_hints_json**: Optional JSON object for configuration.
    """
    db_query = user_query_model.UserQuery(
        raw_query=query_in.raw_query,
        config_hints_json=query_in.config_hints_json,
        status="pending_discovery",
    )
    db.add(db_query)
    await db.flush()  # Flush to get the ID for the background task

    query_id = db_query.id  # Get ID after flush

    # Instantiate services needed for the background task
    processing_service = UserQueryProcessingService()
    # Instantiate the discovery service directly, passing the already resolved AI model
    discovery_service_instance = SourceDiscoveryService(ai_model=ai_model_for_discovery)

    background_tasks.add_task(
        processing_service.process_query,
        query_id=query_id,
        db=db,
        discovery_service=discovery_service_instance,  # Pass the instantiated service
    )

    # Return object state post-flush, pre-commit for the request
    # Rely on the ORM instance state after flush for the response
    return db_query
