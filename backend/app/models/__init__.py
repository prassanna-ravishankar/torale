# Import all models here to ensure they are registered with Base metadata

# Remove old import if it exists
# from app.models.alert import Alert, Base

from app.core.db import (
    Base,
)  # Import Base correctly if needed elsewhere, though usually not needed in models/__init__ itself

from .user_query_model import UserQuery
from .monitored_source_model import MonitoredSource
from .scraped_content_model import ScrapedContent
from .content_embedding_model import ContentEmbedding
from .change_alert_model import ChangeAlert

__all__ = [
    "Base",  # Export Base if imported
    "UserQuery",
    "MonitoredSource",
    "ScrapedContent",
    "ContentEmbedding",
    "ChangeAlert",
    # Add other models here if created
]
