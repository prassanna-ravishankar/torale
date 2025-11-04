from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://torale:torale@localhost:5432/torale"

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    notification_api_key: str | None = None

    gcp_project_id: str | None = None
    cloud_run_region: str = "us-central1"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False


settings = Settings()