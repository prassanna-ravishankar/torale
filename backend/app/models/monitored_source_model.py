from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base # Corrected import

class MonitoredSource(Base):
    __tablename__ = "monitored_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_query_id = Column(Integer, ForeignKey("user_queries.id"), nullable=True) # Link to the original query
    url = Column(String, nullable=False, unique=True, index=True)
    # status: e.g., active, paused, error
    status = Column(String, default="active") 
    # How often to check, in seconds or a cron string. For simplicity, let's assume seconds for now.
    check_interval_seconds = Column(Integer, default=3600) # Default to 1 hour
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False) # Soft delete

    user_query = relationship("UserQuery")
    # Relationship to scraped content (one-to-many)
    scraped_contents = relationship("ScrapedContent", back_populates="monitored_source")
    # Relationship to alerts (one-to-many)
    alerts = relationship("ChangeAlert", back_populates="monitored_source") 