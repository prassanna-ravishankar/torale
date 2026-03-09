"""Input and metadata models for pydantic-evals cases."""

from pydantic import BaseModel


class MonitoringCaseInput(BaseModel):
    """Input for a monitoring evaluation case."""

    search_query: str
    condition_description: str
    category: str
    notify_behavior: str  # "once" | "always"
    passes: int = 1  # sequential runs for multi-pass simulation


class MonitoringCaseMetadata(BaseModel):
    """Metadata attached to each evaluation case."""

    category: str
    source: str = "static"  # "static" | "dynamic"
    generated_at: str | None = None
