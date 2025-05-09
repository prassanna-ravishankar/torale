from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class MonitoredSourceBase(BaseModel):
    url: HttpUrl
    name: Optional[str] = None # User-defined name or query description
    check_interval_seconds: Optional[int] = 3600
    source_type: Optional[str] = None # E.g., 'website', 'rss', 'youtube'
    keywords: Optional[List[str]] = None # List of keywords to monitor for
    config: Optional[Dict[str, Any]] = None # For other configs like similarity_threshold
    # status: Optional[str] = "active"
    # user_query_id: Optional[int] = None # If linking to an original discovery query

class MonitoredSourceCreate(MonitoredSourceBase):
    pass

class MonitoredSourceUpdate(MonitoredSourceBase):
    url: Optional[HttpUrl] = None # All fields optional for update
    name: Optional[str] = None
    check_interval_seconds: Optional[int] = None
    source_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class MonitoredSourceInDB(MonitoredSourceBase):
    id: int
    status: str # This should reflect the actual status from the DB
    user_query_id: Optional[int] = None # If we implement a separate UserQuery table
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True} 