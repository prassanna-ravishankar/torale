"""Cross-service protocol contract tests.

The agent and backend are deployed independently, so they deliberately keep
their Pydantic models local. This test makes structural drift a CI failure.
"""

import importlib.util
from pathlib import Path
from typing import Any

from models import MonitoringResponse as AgentMonitoringResponse

BACKEND_MODELS = (
    Path(__file__).resolve().parents[2]
    / "backend"
    / "src"
    / "webwhen"
    / "scheduler"
    / "models.py"
)


def _load_backend_monitoring_response():
    spec = importlib.util.spec_from_file_location(
        "backend_scheduler_models", BACKEND_MODELS
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.MonitoringResponse


def _wire_schema(value: Any) -> Any:
    """Remove documentation-only fields while preserving the wire contract."""
    if isinstance(value, dict):
        return {
            key: _wire_schema(child)
            for key, child in sorted(value.items())
            if key not in {"description", "title"}
        }
    if isinstance(value, list):
        return [_wire_schema(child) for child in value]
    return value


def test_monitoring_response_matches_backend_wire_contract() -> None:
    backend_monitoring_response = _load_backend_monitoring_response()
    assert _wire_schema(AgentMonitoringResponse.model_json_schema()) == _wire_schema(
        backend_monitoring_response.model_json_schema()
    )
