from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)  # Or other type for vector

# If using a vector DB extension like pgvector, the column type would be different.
# For now, using JSON to store a list of floats.
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base  # Corrected import


class ContentEmbedding(Base):
    __tablename__ = "content_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    scraped_content_id = Column(
        Integer, ForeignKey("scraped_contents.id"), nullable=False, unique=True
    )
    # Storing embeddings as JSON array of floats.
    # For dedicated vector dbs or extensions like pgvector, use e.g. Vector(dim)
    embedding_vector = Column(JSON, nullable=False)
    # Alternatively, for PostgreSQL specifically:
    # embedding_vector_pg = Column(ARRAY(FLOAT), nullable=False)
    model_name = Column(
        String, nullable=False
    )  # e.g., "text-embedding-ada-002", "all-MiniLM-L6-v2"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    scraped_content = relationship("ScrapedContent", back_populates="embedding")
