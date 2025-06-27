import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the Notification Service."""
    
    # Service Configuration
    SERVICE_NAME: str = "notification-service"
    SERVICE_VERSION: str = "0.1.0"
    
    # SendGrid Configuration
    SENDGRID_API_KEY: Optional[str] = None
    DEFAULT_FROM_EMAIL: str = "noreply@torale.com"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get the settings instance."""
    return Settings()