from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base  # Corrected import


class ScrapedContent(Base):
    __tablename__ = "scraped_contents"

    id = Column(Integer, primary_key=True, index=True)
    monitored_source_id = Column(
        Integer, ForeignKey("monitored_sources.id"), nullable=False
    )
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    raw_content = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=True)  # For cleaned/extracted text
    # Could add a content hash to quickly check for exact duplicates
    # content_hash = Column(String, nullable=True, index=True)

    monitored_source = relationship(
        "MonitoredSource", back_populates="scraped_contents"
    )
    # Relationship to embeddings (one-to-one or one-to-many)
    # Assuming one embedding per scraped content for now
    embedding = relationship(
        "ContentEmbedding", uselist=False, back_populates="scraped_content"
    )
