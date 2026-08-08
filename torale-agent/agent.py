"""webwhen watch agent factory."""

import os
from typing import cast

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.google import GoogleModelSettings
from pydantic_ai.profiles.google import google_model_profile
from pydantic_ai.profiles.openai import openai_model_profile
from pydantic_ai.settings import ThinkingLevel

from models import DEFAULT_MODEL, MonitoringDeps, MonitoringResponse
from prompts import instructions
from tools import register_tools


def create_monitoring_agent(
    model_id: str = DEFAULT_MODEL,
    thinking_level: str | None = None,
) -> Agent[MonitoringDeps, MonitoringResponse]:
    """Create a monitoring agent with the specified model and all tools registered."""
    model_settings = None
    model_lower = model_id.lower()
    model_name = model_lower.partition(":")[2]
    if model_lower.startswith("google:"):
        profile = google_model_profile(model_name) or {}
        if profile.get("supports_thinking", False):
            default_level = (
                "minimal" if model_name == DEFAULT_MODEL.partition(":")[2] else "high"
            )
            level = thinking_level or os.getenv("MODEL_THINKING_LEVEL") or default_level
            if level not in {"minimal", "low", "medium", "high"}:
                raise ValueError(f"Unsupported thinking level: {level}")
            # Pydantic AI translates unified thinking effort into each Gemini
            # model's native thinking level or token budget.
            model_settings = GoogleModelSettings(thinking=cast(ThinkingLevel, level))
        elif thinking_level is not None:
            raise ValueError(f"Thinking is not supported by {model_name}")

    supports_native_output = model_lower.startswith(
        "openai-chat:"
    ) and openai_model_profile(model_name).get("supports_json_schema_output", False)
    output_type = (
        NativeOutput(MonitoringResponse)
        if supports_native_output
        else MonitoringResponse
    )

    agent = Agent[MonitoringDeps, MonitoringResponse](
        model_id,
        deps_type=MonitoringDeps,
        output_type=output_type,
        instructions=instructions,
        retries=3,
        model_settings=model_settings,
        # Resolve provider credentials at run time, not module import. This
        # keeps health checks, tests, and clean CI imports credential-free.
        defer_model_check=True,
        # Pydantic AI 2 defaults to `graceful`, which can execute more queued
        # tool calls after final output. Keep the v1 monitoring semantics.
        end_strategy="early",
    )

    register_tools(agent)

    return agent
