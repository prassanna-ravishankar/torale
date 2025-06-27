from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration settings for Content Monitoring Service."""
    
    # Project info
    PROJECT_NAME: str = "Torale Content Monitoring Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Supabase configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service role key")
    
    # AI provider configuration
    OPENAI_API_KEY: Optional[str] = Field(None, description="OpenAI API key")
    PERPLEXITY_API_KEY: Optional[str] = Field(None, description="Perplexity API key")
    
    # Content processing settings
    DEFAULT_SIMILARITY_THRESHOLD: float = Field(0.85, description="Similarity threshold for change detection")
    DEFAULT_REQUEST_TIMEOUT_SECONDS: int = Field(15, description="HTTP request timeout")
    SCRAPE_DELAY_SECONDS: float = Field(0.1, description="Delay between scrape requests")
    
    # Monitoring settings
    BATCH_SIZE: int = Field(10, description="Batch size for processing sources")
    MAX_CONTENT_LENGTH: int = Field(50000, description="Maximum content length to process")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()