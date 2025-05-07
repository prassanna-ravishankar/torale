from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class ScrapedContentSchema(BaseModel):
    id: Optional[int] = None
    source_url: HttpUrl
    scraped_at: datetime
    raw_content: str
    processed_text: Optional[str] = None

    class Config:
        orm_mode = True # For SQLAlchemy compatibility if needed later

class ContentEmbeddingSchema(BaseModel):
    id: Optional[int] = None
    scraped_content_id: int
    embedding_vector: List[float]
    model_name: str # To track which embedding model was used

    class Config:
        orm_mode = True 