"""Test that agent and backend MonitoringResponse schemas stay in sync."""

from pathlib import Path

import pytest
from pydantic import BaseModel


def extract_monitoring_response_model(agent_file: Path) -> type[BaseModel]:
    """Extract MonitoringResponse model definition from agent.py without importing it."""
    content = agent_file.read_text()
    lines = content.split("\n")

    # Find the start of the class
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("class MonitoringResponse(BaseModel):"):
            start_idx = i
            break

    if start_idx is None:
        raise RuntimeError("Could not find MonitoringResponse class in agent.py")

    # Find the end of the class (first line that's not indented and not blank after the class starts)
    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        # Skip blank lines and lines that are indented
        if line and not line.startswith(" ") and not line.startswith("\t"):
            end_idx = i
            break

    if end_idx is None:
        end_idx = len(lines)

    class_def = "\n".join(lines[start_idx:end_idx])

    # Extract imports we need
    imports = """
from typing import Optional
from pydantic import BaseModel, Field
"""

    # Execute the code to create the model class
    namespace = {}
    exec(imports + "\n" + class_def, namespace)

    return namespace["MonitoringResponse"]


def test_agent_and_backend_schemas_match():
    """Agent and backend MonitoringResponse models must have identical schemas."""
    from torale.scheduler.models import MonitoringResponse as BackendModel

    agent_file = Path(__file__).parent.parent.parent / "torale-agent" / "agent.py"

    if not agent_file.exists():
        pytest.skip("torale-agent not available in this test environment")

    # Extract agent model without importing the entire module
    AgentModel = extract_monitoring_response_model(agent_file)

    backend_schema = BackendModel.model_json_schema()
    agent_schema = AgentModel.model_json_schema()

    # Compare field definitions
    assert backend_schema["properties"] == agent_schema["properties"], (
        "Schema mismatch between agent and backend MonitoringResponse models. "
        "Both models must define identical fields with identical constraints."
    )

    # Compare required fields
    assert backend_schema.get("required", []) == agent_schema.get("required", []), (
        "Required fields mismatch between agent and backend MonitoringResponse models."
    )


def test_monitoring_response_schema_has_all_expected_fields():
    """MonitoringResponse schema includes all expected fields."""
    from torale.scheduler.models import MonitoringResponse

    schema = MonitoringResponse.model_json_schema()
    properties = schema["properties"]

    # Required fields
    assert "evidence" in properties
    assert "sources" in properties
    assert "confidence" in properties

    # Optional fields
    assert "next_run" in properties
    assert "notification" in properties
    assert "topic" in properties

    # Confidence constraints
    assert properties["confidence"]["minimum"] == 0
    assert properties["confidence"]["maximum"] == 100
