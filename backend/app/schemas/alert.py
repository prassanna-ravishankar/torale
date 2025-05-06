from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict


class AlertBase(BaseModel):
    user_email: EmailStr
    query: str
    target_url: HttpUrl
    target_type: str  # website, youtube, rss
    keywords: Optional[str] = None
    check_frequency_minutes: int = 30
    similarity_threshold: float = 0.9


class AlertCreate(AlertBase):
    pass


class AlertUpdate(AlertBase):
    is_active: Optional[bool] = None


class Alert(AlertBase):
    id: int
    last_checked: Optional[datetime] = None
    last_embedding: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # For SQLAlchemy model compatibility
    )
