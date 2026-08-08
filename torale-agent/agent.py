"""webwhen watch agent factory."""

import os

from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models.google import GoogleModelSettings

from models import DEFAULT_MODEL, MonitoringDeps, MonitoringResponse
from prompts import instructions
from tools import register_tools

_NATIVE_OUTPUT_MAAS_MODELS = {
    "google/gemma-4-26b-a4b-it-maas",
    "openai/gpt-oss-120b-maas",
}
_MINIMAL_THINKING_MODELS = {"gemini-3.5-flash-lite"}


def create_monitoring_agent(
    model_id: str = DEFAULT_MODEL,
    thinking_level: str | None = None,
) -> Agent[MonitoringDeps, MonitoringResponse]:
    """Create a monitoring agent with the specified model and all tools registered."""
    # Enable thinking for supported Gemini models (gemini-3-*, gemini-2.5-pro).
    # String matching may need updates for new models.
    model_settings = None
    model_lower = model_id.lower()
    model_name = model_lower.partition(":")[2]
    if "gemini" in model_lower or "google" in model_lower:
        supports_thinking = "gemini-3" in model_lower or "gemini-2.5-pro" in model_lower
        if supports_thinking:
            default_level = (
                "minimal" if model_name in _MINIMAL_THINKING_MODELS else "high"
            )
            level = thinking_level or os.getenv("MODEL_THINKING_LEVEL") or default_level
            allowed_levels = {"low", "medium", "high"}
            if model_name in _MINIMAL_THINKING_MODELS:
                allowed_levels.add("minimal")
            if level not in allowed_levels:
                raise ValueError(
                    f"Thinking level {level!r} is not supported by {model_name}; "
                    f"choose one of {', '.join(sorted(allowed_levels))}"
                )
            model_settings = GoogleModelSettings(
                google_thinking_config={
                    "thinking_level": level,
                    "include_thoughts": True,
                },
            )

    # Agent Platform open models support function calling but may reject the
    # forced tool call Pydantic uses for its default structured-output mode.
    # Keep tools available during the run and use native JSON Schema for the
    # final response instead.
    output_type = (
        NativeOutput(MonitoringResponse)
        if model_name in _NATIVE_OUTPUT_MAAS_MODELS
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
