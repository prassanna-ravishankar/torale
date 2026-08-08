"""Regression tests for the monitoring evaluation harness."""

from pathlib import Path
from typing import cast

import httpx
import pytest

from evals.dynamic import generate_webpage_cases
from evals.evaluators import FetchUrlUsed, NotificationDecision, SearchToolUsed
from evals.models import MonitoringCaseInput, MonitoringCaseMetadata
from evals.runner import load_dataset
from agent import create_monitoring_agent
from models import ActivityStep, MonitoringResponse
from pydantic_ai.models.google import GoogleModelSettings
from pydantic_evals.evaluators import EvaluatorContext
from pydantic_evals.otel._errors import SpanTreeRecordingError


def _response(*, notification: str | None, tools: list[str] | None = None):
    return MonitoringResponse(
        evidence="Reviewed evidence",
        sources=["https://example.com/source"],
        confidence=90,
        next_run="2026-08-09T12:00:00Z",
        notification=notification,
        activity=[ActivityStep(tool=tool, detail="query") for tool in (tools or [])],
    )


def _context(
    *, output: MonitoringResponse, metadata: MonitoringCaseMetadata
) -> EvaluatorContext[MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata]:
    return EvaluatorContext(
        name="test",
        inputs=MonitoringCaseInput(
            search_query="test query",
            condition_description="test condition",
            category="Tech",
        ),
        metadata=metadata,
        expected_output=None,
        output=output,
        duration=0.1,
        _span_tree=SpanTreeRecordingError("not recorded"),
        attributes={},
        metrics={},
    )


def test_search_tool_evaluator_uses_production_activity():
    ctx = _context(
        output=_response(
            notification=None, tools=["perplexity_search", "final_result"]
        ),
        metadata=MonitoringCaseMetadata(category="Tech"),
    )

    assert SearchToolUsed().evaluate(ctx) == {"used_search": True, "search_count": 1}


def test_notification_decision_matches_reviewed_ground_truth():
    ctx = _context(
        output=_response(notification="Condition met"),
        metadata=MonitoringCaseMetadata(
            category="Tech",
            expected_notification=True,
            ground_truth="The release is official.",
        ),
    )

    result = NotificationDecision().evaluate(ctx)

    assert result.value is True
    assert "expected notification=True" in (result.reason or "")


def test_notification_decision_catches_false_positive():
    ctx = _context(
        output=_response(notification="Incorrect trigger"),
        metadata=MonitoringCaseMetadata(
            category="Tech",
            expected_notification=False,
            ground_truth="The release does not exist.",
        ),
    )

    assert NotificationDecision().evaluate(ctx).value is False


def test_empty_notification_matches_production_no_trigger_semantics():
    ctx = _context(
        output=_response(notification=""),
        metadata=MonitoringCaseMetadata(
            category="Tech",
            expected_notification=False,
        ),
    )

    assert NotificationDecision().evaluate(ctx).value is True


def test_static_dataset_loads_decision_regressions():
    dataset = load_dataset(Path(__file__).parents[1] / "evals" / "cases.yaml")
    decision_cases = [
        case
        for case in dataset.cases
        if case.metadata is not None and case.metadata.expected_notification is not None
    ]

    assert len(decision_cases) == 4
    assert all(
        any(isinstance(e, NotificationDecision) for e in c.evaluators)
        for c in decision_cases
    )


def test_agent_can_override_gemini_thinking_level():
    agent = create_monitoring_agent(
        "google:gemini-3.5-flash-lite", thinking_level="medium"
    )

    settings = cast(GoogleModelSettings, agent.model_settings)
    thinking = settings.get("google_thinking_config")
    assert thinking is not None
    assert thinking["thinking_level"] == "medium"


def test_agent_reads_gemini_thinking_level_from_environment(monkeypatch):
    monkeypatch.setenv("MODEL_THINKING_LEVEL", "low")

    agent = create_monitoring_agent("google:gemini-3.5-flash-lite")

    settings = cast(GoogleModelSettings, agent.model_settings)
    thinking = settings.get("google_thinking_config")
    assert thinking is not None
    assert thinking["thinking_level"] == "low"


def test_agent_defaults_to_minimal_gemini_thinking(monkeypatch):
    monkeypatch.delenv("MODEL_THINKING_LEVEL", raising=False)

    agent = create_monitoring_agent("google:gemini-3.5-flash-lite")

    settings = cast(GoogleModelSettings, agent.model_settings)
    thinking = settings.get("google_thinking_config")
    assert thinking is not None
    assert thinking["thinking_level"] == "minimal"


def test_openai_compatible_models_use_native_structured_output():
    agent = create_monitoring_agent("openai-chat:openai/gpt-oss-120b-maas")

    assert type(agent._output_schema).__name__ == "NativeOutputSchema"


def test_other_openai_chat_models_keep_tool_structured_output():
    agent = create_monitoring_agent("openai-chat:gpt-4o-mini")

    assert type(agent._output_schema).__name__ == "AutoOutputSchema"


@pytest.mark.asyncio
async def test_fetch_assertion_is_scoped_to_webpage_cases():
    async with httpx.AsyncClient() as client:
        cases = await generate_webpage_cases(client)

    assert cases
    assert all(any(isinstance(e, FetchUrlUsed) for e in c.evaluators) for c in cases)
