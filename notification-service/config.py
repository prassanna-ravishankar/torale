import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for the notification service."""
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8003
    reload: bool = False
    
    # Supabase settings
    supabase_url: str
    supabase_key: str
    
    # SendGrid settings
    sendgrid_api_key: Optional[str] = None
    
    # Logging settings
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()