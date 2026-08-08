"""webwhen watch agent factory."""

import os
from typing import Literal, cast

from pydantic_ai import Agent, NativeOutput, ToolOutput
from pydantic_ai.models.google import GoogleModelSettings
from pydantic_ai.profiles.google import google_model_profile
from pydantic_ai.profiles.openai import openai_model_profile
from pydantic_ai.settings import ThinkingLevel

from models import DEFAULT_MODEL, MonitoringDeps, MonitoringResponse
from prompts import instructions
from tools import register_tools

OutputMode = Literal["tool", "native"]


def create_monitoring_agent(
    model_id: str = DEFAULT_MODEL,
    thinking_level: str | None = None,
    output_mode: OutputMode | None = None,
) -> Agent[MonitoringDeps, MonitoringResponse]:
    """Create a monitoring agent with the specified model and all tools registered."""
    model_settings = None
    model_lower = model_id.lower()
    model_name = model_lower.partition(":")[2]
    model_profile = None
    if model_lower.startswith("google:"):
        model_profile = google_model_profile(model_name) or {}
        if model_profile.get("supports_thinking", False):
            default_level = (
                "minimal" if model_name == DEFAULT_MODEL.partition(":")[2] else "high"
            )
            level = thinking_level or os.getenv("MODEL_THINKING_LEVEL") or default_level
            if level not in {"minimal", "low", "medium", "high"}:
                raise ValueError(f"Unsupported thinking level: {level}")
            if (
                level == "minimal"
                and model_profile.get("thinking_always_enabled", False)
                and model_profile.get("google_supports_thinking_level", False)
            ):
                raise ValueError(
                    f"Thinking level minimal is not supported by {model_name}"
                )
            # Pydantic AI translates unified thinking effort into each Gemini
            # model's native thinking level or token budget.
            model_settings = GoogleModelSettings(thinking=cast(ThinkingLevel, level))
        elif thinking_level is not None:
            raise ValueError(f"Thinking is not supported by {model_name}")
    elif model_lower.startswith("openai-chat:"):
        model_profile = openai_model_profile(model_name)

    selected_output_mode = output_mode or os.getenv("MODEL_OUTPUT_MODE") or "tool"
    if selected_output_mode not in {"tool", "native"}:
        raise ValueError(f"Unsupported output mode: {selected_output_mode}")
    if selected_output_mode == "native" and not (
        model_profile and model_profile.get("supports_json_schema_output", False)
    ):
        raise ValueError(f"Native structured output is not supported by {model_id}")
    output_type = (
        NativeOutput(MonitoringResponse)
        if selected_output_mode == "native"
        else ToolOutput(MonitoringResponse)
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
