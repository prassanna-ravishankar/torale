# Import all models here to ensure they are registered with Base metadata

# Remove old import if it exists
# from app.models.alert import Alert, Base

from app.core.db import (
    Base,
)  # Import Base correctly if needed elsewhere, though usually not needed here

from .change_alert_model import ChangeAlert
from .content_embedding_model import ContentEmbedding
from .monitored_source_model import MonitoredSource
from .scraped_content_model import ScrapedContent
from .user_query_model import UserQuery

__all__ = [
    "Base",  # Export Base if imported
    "ChangeAlert",
    "ContentEmbedding",
    "MonitoredSource",
    "ScrapedContent",
    "UserQuery",
    # Add other models here if created
]
