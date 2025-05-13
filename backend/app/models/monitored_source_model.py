from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.core.db import Base  # Corrected import


class MonitoredSource(Base):
    __tablename__ = "monitored_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_query_id = Column(
        Integer, ForeignKey("user_queries.id"), nullable=True
    )  # Link to the original query
    url = Column(String, nullable=False, unique=True, index=True)
    name = Column(
        String, nullable=True, index=True
    )  # User-defined name or query description
    # status: e.g., active, paused, error
    status = Column(String, default="active", index=True)
    # How often to check, in seconds or a cron string. For simplicity, let's assume seconds for now.
    check_interval_seconds = Column(Integer, default=3600, nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_content_hash = Column(String, nullable=True)  # Hash of the last seen content
    last_significant_change_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When last sig. change was detected
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    is_deleted = Column(Boolean, default=False, index=True)  # Soft delete

    user_query = relationship("UserQuery")
    # Relationship to scraped content (one-to-many)
    scraped_contents = relationship("ScrapedContent", back_populates="monitored_source")
    # Relationship to alerts (one-to-many)
    alerts = relationship("ChangeAlert", back_populates="monitored_source")

    def __repr__(self):
        return f"<MonitoredSource(id={self.id}, name='{self.name}', url='{self.url}', status='{self.status}')>"

    # New fields based on schema changes
    source_type = Column(String, nullable=True)  # E.g., 'website', 'rss', 'youtube'
    keywords_json = Column(
        Text, nullable=True
    )  # Storing keywords as a JSON string list
    config_json = Column(
        Text, nullable=True
    )  # Storing other config like similarity_threshold as JSON string
