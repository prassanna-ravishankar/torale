from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_email: Mapped[str] = mapped_column(String(255))
    query: Mapped[str] = mapped_column(Text)
    target_url: Mapped[str] = mapped_column(String(2048))
    target_type: Mapped[str] = mapped_column(String(50))  # website, youtube, rss
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    check_frequency_minutes: Mapped[int] = mapped_column(default=30)
    last_checked: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.9)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, query={self.query[:30]}...)>"
