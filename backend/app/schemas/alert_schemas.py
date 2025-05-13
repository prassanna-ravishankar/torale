from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, HttpUrl


class ChangeAlertSchema(BaseModel):
    id: Optional[int] = None
    monitored_source_url: HttpUrl
    detected_at: datetime
    # Details about the change, could be a summary string or structured data
    change_summary: Optional[str] = None
    # Could include things like old vs new snippet, confidence score, etc.
    change_details: Optional[dict[str, Any]] = None
    is_acknowledged: bool = False

    class Config:
        orm_mode = True
