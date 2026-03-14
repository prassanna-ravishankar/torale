"""Torale monitoring agent factory."""

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModelSettings

from models import DEFAULT_MODEL, MonitoringDeps, MonitoringResponse
from prompts import instructions
from tools import register_tools


def create_monitoring_agent(
    model_id: str = DEFAULT_MODEL,
) -> Agent[MonitoringDeps, MonitoringResponse]:
    """Create a monitoring agent with the specified model and all tools registered."""
    # Enable thinking for supported Gemini models (gemini-3-*, gemini-2.5-pro).
    # String matching may need updates for new models.
    model_settings = None
    model_lower = model_id.lower()
    if "gemini" in model_lower or "google" in model_lower:
        supports_thinking = "gemini-3" in model_lower or "gemini-2.5-pro" in model_lower
        if supports_thinking:
            model_settings = GoogleModelSettings(
                google_thinking_config={
                    "thinking_level": "high",
                    "include_thoughts": True,
                },
            )

    agent = Agent[MonitoringDeps, MonitoringResponse](
        model_id,
        deps_type=MonitoringDeps,
        output_type=MonitoringResponse,
        instructions=instructions,
        retries=3,
        model_settings=model_settings,
    )

    register_tools(agent)

    return agent
