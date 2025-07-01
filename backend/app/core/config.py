from functools import lru_cache
from typing import Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Torale"

    # Database Settings
    DATABASE_URL: str
    
    # Supabase Settings
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Email Settings
    SENDGRID_API_KEY: str
    ALERT_FROM_EMAIL: str = "alerts@torale.com"
    
    # Microservices URLs
    DISCOVERY_SERVICE_URL: Optional[str] = None

    # AI Provider API Keys - these should be loaded from .env
    OPENAI_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None
    # Add other AI provider keys as needed

    # AI Model Selection (examples)
    # Specifies which AI client to use for specific tasks defined in AIModelInterface
    # Values could be e.g., "openai", "perplexity", "claude" etc.
    AI_PROVIDER_FOR_REFINE_QUERY: Optional[str] = (
        "perplexity"  # Default to perplexity as per plan for source discovery
    )
    AI_PROVIDER_FOR_IDENTIFY_SOURCES: Optional[str] = (
        "perplexity"  # Default to perplexity
    )
    AI_PROVIDER_FOR_GENERATE_EMBEDDINGS: Optional[str] = (
        "openai"  # Default to openai as per plan
    )
    AI_PROVIDER_FOR_ANALYZE_DIFF: Optional[str] = "openai"  # Default to openai

    # Network/Scraping Settings
    DEFAULT_REQUEST_TIMEOUT_SECONDS: int = 15
    # SCRAPE_DELAY_SECONDS: float = 0.1 # Example if you want to add a delay

    # Logging Settings
    LOG_LEVEL: str = "INFO"

    # Monitoring Settings
    DEFAULT_CHECK_FREQUENCY_MINUTES: int = 30
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.9

    # Security Settings - can be string or list, will be converted to list
    CORS_ORIGINS: Union[str, list[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    @field_validator('CORS_ORIGINS')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    # Microservices URLs
    DISCOVERY_SERVICE_URL: Optional[str] = None  # e.g., "http://discovery-service:8001"
    NOTIFICATION_SERVICE_URL: Optional[str] = None  # e.g., "http://notification-service:8003"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()