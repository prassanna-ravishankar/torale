from datetime import datetime
from typing import Optional, Union

from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.services.embedding_service import EmbeddingService
from app.services.monitor_service import MonitorService
from app.services.notification_service import NotificationService


class AlertService:
    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
        monitor_service: MonitorService,
        notification_service: NotificationService,
    ):
        self.db = db
        self.embedding_service = embedding_service
        self.monitor_service = monitor_service
        self.notification_service = notification_service

    async def create_alert(  # noqa: PLR0913
        self,
        user_email: str,
        query: str,
        target_url: Union[str, HttpUrl],
        target_type: str,
        keywords: Optional[str] = None,
        check_frequency_minutes: int = 30,
        similarity_threshold: float = 0.9,
    ) -> Alert:
        # Convert HttpUrl to string if needed
        if isinstance(target_url, HttpUrl):
            target_url = str(target_url)

        alert = Alert(
            user_email=user_email,
            query=query,
            target_url=target_url,
            target_type=target_type,
            keywords=keywords,
            check_frequency_minutes=check_frequency_minutes,
            similarity_threshold=similarity_threshold,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_alert(self, alert_id: int) -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_alerts(self, user_email: str) -> list[Alert]:
        result = await self.db.execute(
            select(Alert).where(Alert.user_email == user_email)
        )
        return list(result.scalars().all())

    async def delete_alert(self, alert_id: int, user_email: str) -> bool:
        result = await self.db.execute(
            select(Alert).where(
                Alert.id == alert_id,
                Alert.user_email == user_email,
            )
        )
        alert = result.scalar_one_or_none()
        if alert:
            await self.db.delete(alert)
            await self.db.commit()
            return True
        return False

    async def check_alert(self, alert: Alert) -> bool:
        # Get current content
        content = await self.monitor_service.get_content(
            alert.target_url, alert.target_type
        )
        if not content:
            return False

        # Generate embedding for current content
        current_embedding = await self.embedding_service.generate_embedding(content)

        # Compare with last embedding if exists
        if alert.last_embedding:
            similarity = await self.embedding_service.compare_embeddings(
                alert.last_embedding,
                current_embedding,
            )
            if similarity < alert.similarity_threshold:
                # Content has changed significantly
                await self.notification_service.send_alert(
                    alert.user_email,
                    alert.query,
                    alert.target_url,
                    content,
                )
                alert.last_embedding = current_embedding
                alert.last_checked = datetime.utcnow()
                alert.updated_at = datetime.utcnow()
                await self.db.commit()
                return True

        # Update last embedding and timestamp
        alert.last_embedding = current_embedding
        alert.last_checked = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        await self.db.commit()
        return False

    async def check_all_alerts(self) -> list[dict]:
        """Check all active alerts that are due for checking."""
        result = await self.db.execute(select(Alert).where(Alert.is_active))
        alerts = result.scalars().all()

        results = []
        for alert in alerts:
            if (
                not alert.last_checked
                or (datetime.utcnow() - alert.last_checked).total_seconds()
                >= alert.check_frequency_minutes * 60
            ):
                changed = await self.check_alert(alert)
                results.append(
                    {
                        "alert_id": alert.id,
                        "target_url": alert.target_url,
                        "changed": changed,
                        "checked_at": datetime.utcnow().isoformat(),
                    }
                )
        return results
