# Placeholder for monitoring.py in API endpoints 

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from backend.app.core.db import get_db
from backend.app.models.monitored_source_model import MonitoredSource
from backend.app.models.change_alert_model import ChangeAlert
from backend.app.schemas.monitoring_schemas import (
    MonitoredSourceCreate, MonitoredSourceUpdate, MonitoredSourceInDB
)
from backend.app.schemas.alert_schemas import ChangeAlertSchema # Assuming this is the main schema for response
# Import alert schemas and models later when adding alert endpoints

router = APIRouter()

# --- Monitored Sources CRUD Endpoints ---

@router.post("/monitored-sources/", response_model=MonitoredSourceInDB, status_code=status.HTTP_201_CREATED)
def create_monitored_source(
    source_in: MonitoredSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new monitored source."""
    db_source = MonitoredSource(**source_in.model_dump())
    # Check if URL already exists - MonitoredSource model has unique constraint on url
    existing_source = db.query(MonitoredSource).filter(MonitoredSource.url == source_in.url).first()
    if existing_source:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"URL '{source_in.url}' is already being monitored."
        )
    try:
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source
    except Exception as e: # Catch potential DB errors
        db.rollback()
        # Log error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create monitored source."
        )

@router.get("/monitored-sources/", response_model=List[MonitoredSourceInDB])
def list_monitored_sources(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all active monitored sources with pagination."""
    sources = db.query(MonitoredSource).filter(MonitoredSource.is_deleted == False).offset(skip).limit(limit).all()
    return sources

@router.get("/monitored-sources/{source_id}", response_model=MonitoredSourceInDB)
def get_monitored_source(
    source_id: int, 
    db: Session = Depends(get_db)
):
    """Get details of a specific monitored source."""
    db_source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id, MonitoredSource.is_deleted == False).first()
    if db_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found")
    return db_source

@router.put("/monitored-sources/{source_id}", response_model=MonitoredSourceInDB)
def update_monitored_source(
    source_id: int, 
    source_in: MonitoredSourceUpdate, 
    db: Session = Depends(get_db)
):
    """Update a monitored source."""
    db_source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id, MonitoredSource.is_deleted == False).first()
    if db_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found")
    
    update_data = source_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_source, key, value)
    
    try:
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        return db_source
    except Exception as e: # Catch potential DB errors during update (e.g. unique constraint on URL if changed)
        db.rollback()
        # Log error e
        if "UNIQUE constraint failed" in str(e): # Basic check, can be more specific by DB type
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"URL '{source_in.url}' is already being monitored by another source."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update monitored source."
        )

@router.delete("/monitored-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitored_source(
    source_id: int, 
    db: Session = Depends(get_db)
):
    """Deactivate (soft delete) a monitored source."""
    db_source = db.query(MonitoredSource).filter(MonitoredSource.id == source_id, MonitoredSource.is_deleted == False).first()
    if db_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitored source not found")
    
    db_source.is_deleted = True
    db_source.status = "deleted"
    try:
        db.add(db_source)
        db.commit()
        return # No content to return
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete monitored source."
        )

# --- Change Alerts Endpoints ---

@router.get("/alerts/", response_model=List[ChangeAlertSchema])
def list_change_alerts(
    skip: int = 0, 
    limit: int = 100, 
    monitored_source_id: Optional[int] = None,
    is_acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all change alerts, with optional filters."""
    query = db.query(ChangeAlert)
    if monitored_source_id is not None:
        query = query.filter(ChangeAlert.monitored_source_id == monitored_source_id)
    if is_acknowledged is not None:
        query = query.filter(ChangeAlert.is_acknowledged == is_acknowledged)
    
    alerts = query.order_by(desc(ChangeAlert.detected_at)).offset(skip).limit(limit).all()
    return alerts

@router.get("/alerts/{alert_id}", response_model=ChangeAlertSchema)
def get_change_alert(
    alert_id: int, 
    db: Session = Depends(get_db)
):
    """Get details of a specific change alert."""
    db_alert = db.query(ChangeAlert).filter(ChangeAlert.id == alert_id).first()
    if db_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change alert not found")
    return db_alert

@router.post("/alerts/{alert_id}/acknowledge", response_model=ChangeAlertSchema)
def acknowledge_change_alert(
    alert_id: int, 
    db: Session = Depends(get_db)
):
    """Mark a change alert as acknowledged."""
    db_alert = db.query(ChangeAlert).filter(ChangeAlert.id == alert_id).first()
    if db_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change alert not found")
    
    if db_alert.is_acknowledged:
        # Optionally, prevent re-acknowledging or just return current state
        # For now, we'll allow it, it will just update acknowledged_at
        pass 

    db_alert.is_acknowledged = True
    db_alert.acknowledged_at = datetime.utcnow()
    try:
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        return db_alert
    except Exception as e:
        db.rollback()
        # Log error e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge change alert."
        )

# Endpoints for ChangeAlerts will be added below this 