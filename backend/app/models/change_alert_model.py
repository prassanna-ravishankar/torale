from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base # Corrected import

class ChangeAlert(Base):
    __tablename__ = "change_alerts"

    id = Column(Integer, primary_key=True, index=True)
    monitored_source_id = Column(Integer, ForeignKey("monitored_sources.id"), nullable=False)
    # Potentially link to the specific ScrapedContent entries that triggered the alert
    # old_scraped_content_id = Column(Integer, ForeignKey("scraped_contents.id"), nullable=True)
    # new_scraped_content_id = Column(Integer, ForeignKey("scraped_contents.id"), nullable=True)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    change_summary = Column(Text, nullable=True)
    change_details = Column(JSON, nullable=True) # Store structured diff or other details
    # severity = Column(String, nullable=True) # e.g., low, medium, high
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    # acknowledged_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    monitored_source = relationship("MonitoredSource", back_populates="alerts")
    # old_content = relationship("ScrapedContent", foreign_keys=[old_scraped_content_id])
    # new_content = relationship("ScrapedContent", foreign_keys=[new_scraped_content_id]) 