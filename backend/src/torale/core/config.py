from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql://torale:torale@localhost:5432/torale"

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_api_key: str | None = None
    temporal_ui_url: str = "http://localhost:8080"  # Temporal UI base URL

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None

    # Novu Cloud configuration
    novu_secret_key: str | None = None
    novu_workflow_id: str = "torale-condition-met"
    novu_verification_workflow_id: str = "torale-email-verification"

    gcp_project_id: str | None = None
    gcp_region: str = "us-central1"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Development/testing mode - disable authentication
    torale_noauth: bool = False

    # Platform capacity limit for beta
    max_users: int = 100


settings = Settings()
