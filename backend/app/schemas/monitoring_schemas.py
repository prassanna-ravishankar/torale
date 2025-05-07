from typing import Optional, List
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class MonitoredSourceBase(BaseModel):
    url: HttpUrl
    check_interval_seconds: Optional[int] = 3600
    # status: Optional[str] = "active"
    # user_query_id: Optional[int] = None # If linking to an original discovery query

class MonitoredSourceCreate(MonitoredSourceBase):
    pass

class MonitoredSourceUpdate(MonitoredSourceBase):
    url: Optional[HttpUrl] = None # All fields optional for update
    check_interval_seconds: Optional[int] = None
    status: Optional[str] = None

class MonitoredSourceInDB(MonitoredSourceBase):
    id: int
    status: str
    user_query_id: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True} 