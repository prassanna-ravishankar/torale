from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root directory (used for locating static files, templates, etc.)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    The .env file is loaded by justfile/docker-compose, so we just
    read from the environment. This works in all environments.
    """

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = "postgresql://torale:torale@localhost:5432/torale"

    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""

    agent_url: str = "http://localhost:8001"

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Novu Cloud configuration
    novu_secret_key: str | None = None
    novu_workflow_id: str = "torale-condition-met"
    novu_verification_workflow_id: str = "torale-email-verification"
    novu_welcome_workflow_id: str = "torale-task-welcome"
    novu_api_url: str = "https://eu.api.novu.co"

    gcp_project_id: str | None = None
    gcp_region: str = "us-central1"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Frontend URL for SEO (sitemap, OpenGraph, etc.)
    frontend_url: str = "https://torale.ai"

    # Development/testing mode - disable authentication
    torale_noauth: bool = False
    torale_noauth_email: str = "test@example.com"

    # Platform capacity limit for beta
    max_users: int = 100


settings = Settings()
