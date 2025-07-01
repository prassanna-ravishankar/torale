import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the notification service."""

    PROJECT_NAME: str = "Torale Notification Service"
    API_V1_STR: str = "/api/v1"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    RELOAD: bool = False

    # NotificationAPI settings
    NOTIFICATIONAPI_CLIENT_ID: Optional[str] = None
    NOTIFICATIONAPI_CLIENT_SECRET: Optional[str] = None

    # Logging settings
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()