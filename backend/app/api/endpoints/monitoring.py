# Placeholder for monitoring.py in API endpoints

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging  # Import logging
import json  # Import json for keywords and config

from app.core.db import get_db
from app.models.monitored_source_model import MonitoredSource
from app.models.change_alert_model import ChangeAlert
from app.schemas.monitoring_schemas import (
    MonitoredSourceCreate,
    MonitoredSourceUpdate,
    MonitoredSourceInDB,
)
from app.schemas.alert_schemas import (
    ChangeAlertSchema,
)  # Assuming this is the main schema for response
# Import alert schemas and models later when adding alert endpoints

router = APIRouter()
logger = logging.getLogger(__name__)  # Get logger instance

# --- Monitored Sources CRUD Endpoints ---


@router.post(
    "/monitored-sources/",
    response_model=MonitoredSourceInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitored_source(
    source_in: MonitoredSourceCreate, db: AsyncSession = Depends(get_db)
):
    logger.info(
        f"Received request to create monitored source: {source_in.model_dump(exclude_none=True)}"
    )
    result = await db.execute(
        select(MonitoredSource).filter(MonitoredSource.url == str(source_in.url))
    )
    existing_source = result.scalars().first()
    if existing_source and not existing_source.is_deleted:
        logger.warning(
            f"Attempted to create monitored source for existing active URL: {source_in.url}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL '{source_in.url}' is already being actively monitored.",
        )

    db_source = MonitoredSource(
        url=str(source_in.url),  # Ensure URL is a string for the DB model
        name=source_in.name,
        check_interval_seconds=source_in.check_interval_seconds
        if source_in.check_interval_seconds is not None
        else 3600,
        source_type=source_in.source_type,
        keywords_json=json.dumps(source_in.keywords)
        if source_in.keywords is not None
        else None,
        config_json=json.dumps(source_in.config)
        if source_in.config is not None
        else None,
        status="active",  # Default status for new sources
    )
    try:
        db.add(db_source)
        await db.commit()
        await db.refresh(db_source)
        logger.info(
            f"Successfully created monitored source ID {db_source.id} for URL: {db_source.url}"
        )
        return db_source
    except Exception as e:
        await db.rollback()
        logger.exception(
            f"Database error creating monitored source for URL {source_in.url}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create monitored source.",
        )


@router.get("/monitored-sources/", response_model=List[MonitoredSourceInDB])
async def list_monitored_sources(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    logger.info(
        f"Received request to list monitored sources (skip={skip}, limit={limit})"
    )
    try:
        result = await db.execute(
            select(MonitoredSource)
            .filter(MonitoredSource.is_deleted == False)
            .offset(skip)
            .limit(limit)
        )
        sources = result.scalars().all()
        logger.info(f"Returning {len(sources)} monitored sources.")
        return sources
    except Exception as e:
        logger.exception(f"Database error listing monitored sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list monitored sources.",
        )


@router.get("/monitored-sources/{source_id}", response_model=MonitoredSourceInDB)
async def get_monitored_source(source_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request to get monitored source ID: {source_id}")
    result = await db.execute(
        select(MonitoredSource).filter(
            MonitoredSource.id == source_id, MonitoredSource.is_deleted == False
        )
    )
    db_source = result.scalars().first()
    if db_source is None:
        logger.warning(f"Monitored source ID {source_id} not found or deleted.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found"
        )
    logger.info(f"Returning details for monitored source ID: {source_id}")
    return db_source


@router.put("/monitored-sources/{source_id}", response_model=MonitoredSourceInDB)
async def update_monitored_source(
    source_id: int, source_in: MonitoredSourceUpdate, db: AsyncSession = Depends(get_db)
):
    logger.info(
        f"Received request to update monitored source ID: {source_id} with data: {source_in.model_dump(exclude_unset=True)}"
    )
    result = await db.execute(
        select(MonitoredSource).filter(
            MonitoredSource.id == source_id, MonitoredSource.is_deleted == False
        )
    )
    db_source = result.scalars().first()
    if db_source is None:
        logger.warning(
            f"Attempted to update non-existent or deleted monitored source ID: {source_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found"
        )

    update_data = source_in.model_dump(exclude_unset=True, mode="python")
    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(
            update_data["url"]
        )  # Ensure HttpUrl is string if present

    updated_fields = list(update_data.keys())
    for key, value in update_data.items():
        setattr(db_source, key, value)

    try:
        db.add(db_source)
        await db.commit()
        await db.refresh(db_source)
        logger.info(
            f"Successfully updated monitored source ID: {source_id}. Fields updated: {updated_fields}"
        )
        return db_source
    except Exception as e:
        await db.rollback()
        if "UNIQUE constraint failed" in str(e):
            logger.warning(
                f"Update failed for source ID {source_id} due to UNIQUE constraint (likely URL): {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Update failed. URL '{source_in.url}' may already be monitored.",
            )
        logger.exception(
            f"Database error updating monitored source ID {source_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update monitored source.",
        )


@router.delete("/monitored-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitored_source(source_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request to delete monitored source ID: {source_id}")
    result = await db.execute(
        select(MonitoredSource).filter(
            MonitoredSource.id == source_id, MonitoredSource.is_deleted == False
        )
    )
    db_source = result.scalars().first()
    if db_source is None:
        logger.warning(
            f"Attempted to delete non-existent or already deleted monitored source ID: {source_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found"
        )

    db_source.is_deleted = True
    db_source.status = "deleted"
    try:
        db.add(db_source)
        await db.commit()
        logger.info(f"Successfully marked monitored source ID {source_id} as deleted.")
        return  # No content to return
    except Exception as e:
        await db.rollback()
        logger.exception(
            f"Database error deleting monitored source ID {source_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete monitored source.",
        )


# --- Change Alerts Endpoints ---


@router.get("/alerts/", response_model=List[ChangeAlertSchema])
async def list_change_alerts(
    skip: int = 0,
    limit: int = 100,
    monitored_source_id: Optional[int] = None,
    is_acknowledged: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    filters = {
        "skip": skip,
        "limit": limit,
        "monitored_source_id": monitored_source_id,
        "is_acknowledged": is_acknowledged,
    }
    logger.info(f"Received request to list alerts with filters: {filters}")
    try:
        stmt = select(ChangeAlert)
        if monitored_source_id is not None:
            stmt = stmt.filter(ChangeAlert.monitored_source_id == monitored_source_id)
        if is_acknowledged is not None:
            stmt = stmt.filter(ChangeAlert.is_acknowledged == is_acknowledged)

        result = await db.execute(
            stmt.order_by(desc(ChangeAlert.detected_at)).offset(skip).limit(limit)
        )
        alerts = result.scalars().all()
        logger.info(f"Returning {len(alerts)} alerts.")
        return alerts
    except Exception as e:
        logger.exception(f"Database error listing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts.",
        )


@router.get("/alerts/{alert_id}", response_model=ChangeAlertSchema)
async def get_change_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request to get alert ID: {alert_id}")
    result = await db.execute(select(ChangeAlert).filter(ChangeAlert.id == alert_id))
    db_alert = result.scalars().first()
    if db_alert is None:
        logger.warning(f"Alert ID {alert_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Change alert not found"
        )
    logger.info(f"Returning details for alert ID: {alert_id}")
    return db_alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=ChangeAlertSchema)
async def acknowledge_change_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    logger.info(f"Received request to acknowledge alert ID: {alert_id}")
    result = await db.execute(select(ChangeAlert).filter(ChangeAlert.id == alert_id))
    db_alert = result.scalars().first()
    if db_alert is None:
        logger.warning(f"Attempted to acknowledge non-existent alert ID: {alert_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Change alert not found"
        )
    if db_alert.is_acknowledged:
        logger.info(f"Alert ID {alert_id} is already acknowledged. Updating timestamp.")
    db_alert.is_acknowledged = True
    db_alert.acknowledged_at = datetime.utcnow()
    try:
        db.add(db_alert)
        await db.commit()
        await db.refresh(db_alert)
        logger.info(f"Successfully acknowledged alert ID: {alert_id}")
        return db_alert
    except Exception as e:
        await db.rollback()
        logger.exception(f"Database error acknowledging alert ID {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge change alert.",
        )


# Endpoints for ChangeAlerts will be added below this
