from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Service info
    service_name: str = "discovery-service"
    service_port: int = 8001
    
    # AI Provider Keys
    perplexity_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # AI Provider Selection
    ai_provider: str = "perplexity"  # "perplexity" or "openai"
    ai_model: Optional[str] = None  # Use default for each provider if not specified
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: str = "http://localhost:8000,http://localhost:3000"
    
    # Cache (for future implementation)
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 1000
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def get_settings() -> Settings:
    return Settings()