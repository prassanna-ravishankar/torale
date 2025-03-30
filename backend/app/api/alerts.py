from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.alert import Alert as AlertSchema
from app.schemas.alert import AlertCreate
from app.services.alert_service import AlertService
from app.services.embedding_service import EmbeddingService
from app.services.monitor_service import MonitorService
from app.services.notification_service import NotificationService

router = APIRouter()


@router.post("/alerts", response_model=AlertSchema)
async def create_alert(
    alert: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert."""
    alert_service = AlertService(
        db=db,
        embedding_service=EmbeddingService(),
        monitor_service=MonitorService(),
        notification_service=NotificationService(),
    )

    db_alert = await alert_service.create_alert(**alert.model_dump())
    return db_alert


@router.get("/alerts/{alert_id}", response_model=AlertSchema)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get an alert by ID."""
    alert_service = AlertService(
        db=db,
        embedding_service=EmbeddingService(),
        monitor_service=MonitorService(),
        notification_service=NotificationService(),
    )

    alert = await alert_service.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("/alerts", response_model=list[AlertSchema])
async def list_alerts(
    user_email: str,
    db: AsyncSession = Depends(get_db),
):
    """List all alerts for a user."""
    alert_service = AlertService(
        db=db,
        embedding_service=EmbeddingService(),
        monitor_service=MonitorService(),
        notification_service=NotificationService(),
    )

    alerts = await alert_service.list_alerts(user_email)
    return alerts


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    user_email: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    alert_service = AlertService(
        db=db,
        embedding_service=EmbeddingService(),
        monitor_service=MonitorService(),
        notification_service=NotificationService(),
    )

    success = await alert_service.delete_alert(alert_id, user_email)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert deleted successfully"}


@router.post("/alerts/check")
async def check_alerts(
    db: AsyncSession = Depends(get_db),
):
    """Check all active alerts for changes."""
    alert_service = AlertService(
        db=db,
        embedding_service=EmbeddingService(),
        monitor_service=MonitorService(),
        notification_service=NotificationService(),
    )

    results = await alert_service.check_all_alerts()
    return results
