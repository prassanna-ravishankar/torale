import logging
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from fastapi import Depends # Need Depends for dependencies in methods
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_query_model import UserQuery
from app.models.monitored_source_model import MonitoredSource
from app.services.source_discovery_service import SourceDiscoveryService
from app.core.db import get_db # Assuming async session needed, adjust if sync

logger = logging.getLogger(__name__)

class UserQueryProcessingService:

    # Note: Dependencies like db session and other services might need to be 
    # passed to the method if the service instance itself is created elsewhere,
    # or injected into __init__ if the service is managed by FastAPI DI.
    # Since this will be called by a BackgroundTask, passing deps to the method is safer.

    async def process_query(
        self,
        query_id: int,
        db: AsyncSession,
        discovery_service: SourceDiscoveryService
    ):
        logger.info(f"Starting background processing for UserQuery ID: {query_id}")
        query = None # Initialize query to None
        try:
            # Begin a transaction for this background task
            async with db.begin():
                # Fetch the query object within the transaction
                stmt = select(UserQuery).where(UserQuery.id == query_id)
                result = await db.execute(stmt) # Await the execution
                query = result.scalar_one_or_none()

                if not query:
                    logger.warning(f"UserQuery ID {query_id} not found for background processing.")
                    return

                # Ensure status is correct before processing
                if query.status != "pending_discovery":
                    logger.warning(f"UserQuery ID {query_id} is not in 'pending_discovery' state (state: {query.status}), skipping discovery.")
                    return

                logger.info(f"Performing source discovery for UserQuery ID: {query_id}, Query: '{query.raw_query}'")
                discovered_urls = await discovery_service.discover_sources(query.raw_query)
                logger.info(f"Discovered {len(discovered_urls)} potential sources for UserQuery ID: {query_id}")

                # Create MonitoredSource records
                created_sources = 0
                for url in discovered_urls:
                    # Simple check for existing URL for this query to avoid duplicates
                    exists_stmt = select(MonitoredSource).where(
                        MonitoredSource.user_query_id == query_id,
                        MonitoredSource.url == url
                    )
                    existing_result = await db.execute(exists_stmt)
                    if existing_result.scalar_one_or_none() is None:
                        # TODO: Extract name/title if possible, refine default interval
                        new_source = MonitoredSource(
                            user_query_id=query_id,
                            url=url,
                            check_interval_seconds=3600, # Default: 1 hour
                            status="active" # Default status
                            # name can be added later or derived
                        )
                        db.add(new_source)
                        created_sources += 1
                    else:
                         logger.debug(f"Source URL '{url}' already exists for UserQuery ID {query_id}, skipping.")

                # Update query status to 'processed'
                query.status = "processed"
                db.add(query) # Add updated query back to session
                logger.info(f"Created {created_sources} new MonitoredSource records for UserQuery ID: {query_id}. Status set to 'processed'.")
                # Commit happens automatically when `async with db.begin():` exits without error

        except Exception as e:
            logger.error(f"Error processing UserQuery ID {query_id} in background task: {e}", exc_info=True)
            # Attempt to rollback and set error status (best effort)
            try:
                # Check if query object was fetched before the error
                if query:
                    async with db.begin_nested(): # Use nested transaction for safety
                        query.status = "error"
                        db.add(query)
                        logger.info(f"Set status to 'error' for UserQuery ID: {query_id}")
                else:
                    # If query wasn't fetched, try fetching again to set status
                     async with db.begin_nested(): # Use nested transaction
                        stmt_err = select(UserQuery).where(UserQuery.id == query_id)
                        result_err = await db.execute(stmt_err)
                        query_err = result_err.scalar_one_or_none()
                        if query_err:
                            query_err.status = "error"
                            db.add(query_err)
                            logger.info(f"Set status to 'error' for UserQuery ID: {query_id} (fetched after error)")
                 # Commit nested transaction if possible
            except Exception as inner_e:
                # Log if updating status fails
                logger.error(f"Failed to rollback and set error status for UserQuery {query_id}: {inner_e}")
        finally:
            # Ensure session is closed if manually managed, though Depends(get_db) usually handles this.
            pass # db session scope is managed by FastAPI for the request that spawned the task 