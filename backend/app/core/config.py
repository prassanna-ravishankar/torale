from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AmbiAlert"

    # Database Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./ambi_alert.db"

    # Email Settings
    SENDGRID_API_KEY: str
    ALERT_FROM_EMAIL: str = "alerts@ambialert.com"

    # Monitoring Settings
    DEFAULT_CHECK_FREQUENCY_MINUTES: int = 30
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.9

    # Security Settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
