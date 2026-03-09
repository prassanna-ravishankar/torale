"""Evaluation runner: thin wrapper around pydantic-evals Dataset.evaluate()."""

import logging
from pathlib import Path

import logfire
from pydantic_evals import Dataset
from pydantic_evals.reporting import EvaluationReport

from evals.evaluators import (
    FetchUrlUsed,
    MultiPassProgression,
    ReasonableNextRun,
    SearchToolUsed,
    SourcesWhenNotifying,
)
from evals.models import MonitoringCaseInput, MonitoringCaseMetadata
from evals.task import run_monitoring_task, set_eval_model
from models import MonitoringResponse

logger = logging.getLogger(__name__)

CUSTOM_EVALUATORS = [
    SourcesWhenNotifying,
    ReasonableNextRun,
    SearchToolUsed,
    FetchUrlUsed,
    MultiPassProgression,
]

MonitoringDataset = Dataset[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]
MonitoringReport = EvaluationReport[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]


def load_dataset(path: Path) -> MonitoringDataset:
    """Load a dataset from a YAML file with custom evaluator support."""
    return Dataset[
        MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
    ].from_file(path, custom_evaluator_types=CUSTOM_EVALUATORS)


def merge_datasets(
    static_path: Path, dynamic_path: Path | None = None
) -> MonitoringDataset:
    """Load static cases and optionally merge with dynamic cases."""
    static = load_dataset(static_path)

    if dynamic_path is None or not dynamic_path.exists():
        return static

    dynamic = load_dataset(dynamic_path)
    return Dataset(
        cases=list(static.cases) + list(dynamic.cases),
        evaluators=list(static.evaluators),
    )


async def run_eval(
    dataset: MonitoringDataset,
    model: str,
    max_concurrency: int = 1,
    name: str | None = None,
) -> MonitoringReport:
    """Configure model, run evaluation, return report."""
    set_eval_model(model)

    # Pre-import agent so its logfire.configure() runs BEFORE pydantic-evals
    # sets up its in-memory span exporter. Without this, agent.py's module-level
    # logfire.configure() would run inside evaluate() and reset the exporter.
    import agent as _agent  # noqa: F401

    logfire.configure(send_to_logfire="if-token-present")

    return await dataset.evaluate(
        run_monitoring_task,
        name=name or f"monitoring-{model}",
        max_concurrency=max_concurrency,
    )
