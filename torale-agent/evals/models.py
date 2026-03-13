"""Input and metadata models for pydantic-evals cases."""

from pydantic import BaseModel
from pydantic_evals import Case, Dataset
from pydantic_evals.reporting import EvaluationReport

from models import MonitoringResponse


class MonitoringCaseInput(BaseModel):
    """Input for a monitoring evaluation case."""

    search_query: str
    condition_description: str
    category: str
    passes: int = 1  # sequential runs for multi-pass simulation


class MonitoringCaseMetadata(BaseModel):
    """Metadata attached to each evaluation case."""

    category: str
    source: Literal["static", "dynamic"] = "static"
    generated_at: str | None = None


MonitoringCase = Case[MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata]
MonitoringDataset = Dataset[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]
MonitoringReport = EvaluationReport[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]
