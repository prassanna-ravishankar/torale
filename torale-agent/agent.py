"""Torale monitoring agent service."""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastharness import CostTracker, ConsoleStepLogger, FastHarness
from fastharness.client import HarnessClient
from fastharness.core.context import AgentContext
from fastharness.core.skill import Skill
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MonitoringResponse(BaseModel):
    """Response from monitoring check."""

    evidence: str = Field(description="Internal reasoning and audit trail (not user-facing)")
    sources: list[str] = Field(description="URLs backing the evidence")
    confidence: int = Field(ge=0, le=100, description="Confidence level 0-100")
    next_run: Optional[str] = Field(description="ISO timestamp for next check, or null if monitoring is complete")
    notification: Optional[str] = Field(description="Markdown message for the user, or null if nothing to report")


harness = FastHarness(
    name="torale-agent",
    description="Torale search monitoring agent",
    version="0.1.0",
    url=os.getenv("AGENT_URL", "http://localhost:8000"),
)

cost_tracker = CostTracker(warn_threshold_usd=0.50, error_threshold_usd=2.00)

SYSTEM_PROMPT = """You are a search monitoring agent for Torale. You run as a scheduled API service - called periodically to check if a monitoring condition is met.

Each run is a single iteration in an ongoing monitoring loop:
- You receive a task description
- You search and analyze current information
- You return a structured decision
- The orchestrator schedules the next check based on your recommendation

This is not an interactive conversation. You are called, you execute, you return results. Never ask the user questions."""


@harness.agentloop(
    name="monitoring-agent",
    description="Monitors conditions via search and returns structured reports",
    skills=[Skill(id="monitor", name="Monitor", description="Search monitoring agent")],
    system_prompt=SYSTEM_PROMPT,
    model="claude-haiku-4-5-20251001",
    output_format={
        "type": "json_schema",
        "schema": MonitoringResponse.model_json_schema(),
    },
)
async def monitor(prompt: str, ctx: AgentContext, client: HarnessClient):
    client.step_logger = ConsoleStepLogger()
    client.telemetry_callbacks = [cost_tracker]
    result = await client.run(prompt)
    return result


app = harness.app
