"""Domain-specific evaluators for monitoring agent evals."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.otel._errors import SpanTreeRecordingError

from evals.models import MonitoringCaseInput, MonitoringCaseMetadata
from models import MonitoringResponse

EvalCtx = EvaluatorContext[
    MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata
]
EvalBase = Evaluator[MonitoringCaseInput, MonitoringResponse, MonitoringCaseMetadata]


def _get_span_tree(ctx: EvalCtx):
    """Safely get span tree, returning None if not available."""
    try:
        return ctx.span_tree
    except SpanTreeRecordingError:
        return None


@dataclass
class SourcesWhenNotifying(EvalBase):
    """When a notification is sent, sources must be non-empty."""

    def evaluate(self, ctx: EvalCtx) -> bool:
        if ctx.output.notification is None:
            return True
        return len(ctx.output.sources) > 0


@dataclass
class ReasonableNextRun(EvalBase):
    """next_run should be in the future and within 30 days."""

    max_days: int = 30

    def evaluate(self, ctx: EvalCtx) -> dict[str, bool | float]:
        if ctx.output.next_run is None:
            return {
                "valid_iso": True,
                "in_future": True,
                "within_limit": True,
                "hours_from_now": 0.0,
            }

        try:
            next_run = datetime.fromisoformat(ctx.output.next_run)
        except ValueError:
            return {
                "valid_iso": False,
                "in_future": False,
                "within_limit": False,
                "hours_from_now": 0.0,
            }

        now = datetime.now(UTC)
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=UTC)

        in_future = next_run > now
        within_limit = next_run < now + timedelta(days=self.max_days)
        hours_from_now = (next_run - now).total_seconds() / 3600

        return {
            "valid_iso": True,
            "in_future": in_future,
            "within_limit": within_limit,
            "hours_from_now": round(hours_from_now, 1),
        }


@dataclass
class SearchToolUsed(EvalBase):
    """Span-based: verify that search tools were called during agent execution."""

    def evaluate(self, ctx: EvalCtx) -> dict[str, bool | int]:
        tree = _get_span_tree(ctx)
        if tree is None:
            return {"used_search": False, "search_count": 0}

        # Tool name lives in gen_ai.tool.name attribute, not the span name
        search_spans = tree.find(
            lambda node: (
                node.attributes.get("gen_ai.tool.name", "")
                in ("perplexity_search", "parallel_search")
            )
        )

        return {
            "used_search": len(search_spans) > 0,
            "search_count": len(search_spans),
        }


@dataclass
class FetchUrlUsed(EvalBase):
    """Span-based: check if fetch_url tool was called during agent execution."""

    def evaluate(self, ctx: EvalCtx) -> dict[str, bool | int]:
        tree = _get_span_tree(ctx)
        if tree is None:
            return {"used_fetch": False, "fetch_count": 0}

        fetch_spans = tree.find(
            lambda node: node.attributes.get("gen_ai.tool.name", "") == "fetch_url"
        )

        return {
            "used_fetch": len(fetch_spans) > 0,
            "fetch_count": len(fetch_spans),
        }


@dataclass
class MultiPassProgression(EvalBase):
    """Span-based: verify multiple agent runs occurred for multi-pass cases."""

    def evaluate(self, ctx: EvalCtx) -> dict[str, bool | int]:
        expected_passes = ctx.inputs.passes
        if expected_passes <= 1:
            return {"multi_pass_ok": True, "agent_runs": 1, "expected_passes": 1}

        tree = _get_span_tree(ctx)
        if tree is None:
            return {
                "multi_pass_ok": False,
                "agent_runs": 0,
                "expected_passes": expected_passes,
            }

        agent_spans = tree.find({"name_contains": "agent run"})

        return {
            "multi_pass_ok": len(agent_spans) >= expected_passes,
            "agent_runs": len(agent_spans),
            "expected_passes": expected_passes,
        }


CUSTOM_EVALUATORS = [
    SourcesWhenNotifying,
    ReasonableNextRun,
    SearchToolUsed,
    FetchUrlUsed,
    MultiPassProgression,
]
