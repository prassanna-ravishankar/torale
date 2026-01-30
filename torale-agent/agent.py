"""Torale monitoring agent service."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage, AssistantMessage
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MonitoringRequest(BaseModel):
    """Request to monitor a condition."""

    task_description: str
    user_id: Optional[str] = None
    task_id: Optional[str] = None


class MonitoringResponse(BaseModel):
    """Response from monitoring check."""

    condition_met: bool = Field(description="Whether the monitoring condition is met")
    evidence: str = Field(description="Clear explanation with sources of what was found")
    confidence: int = Field(ge=0, le=100, description="Confidence level 0-100")
    next_check_at: Optional[str] = Field(description="ISO timestamp for next check, or null if complete")
    sources: list[str] = Field(description="List of source URLs used")


app = FastAPI(title="Torale Monitoring Agent")


@app.post("/monitor", response_model=MonitoringResponse)
async def monitor(request: MonitoringRequest) -> MonitoringResponse:
    """Execute monitoring task using Claude Agent SDK."""

    logger.info(f"Starting monitoring task: {request.task_description}")
    logger.info(f"User ID: {request.user_id}, Task ID: {request.task_id}")

    # Set cwd to project directory
    project_dir = Path(__file__).parent

    # Identity and persona (override Claude Code preset)
    system_prompt = """You are a search monitoring agent for Torale. You run as a scheduled API service - called periodically to check if a monitoring condition is met.

Each run is a single iteration in an ongoing monitoring loop:
- You receive a task description
- You search and analyze current information
- You return a structured decision
- The orchestrator schedules the next check based on your recommendation

This is not an interactive conversation. You are called, you execute, you return results. Never ask the user questions."""

    # Agent SDK options with structured output
    # setting_sources=["project"] loads CLAUDE.md (workflow), .mcp.json, .claude/settings.json
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,  # Identity/persona only
        setting_sources=["project"],  # Loads CLAUDE.md for workflow
        permission_mode="bypassPermissions",
        model="claude-haiku-4-5-20251001",
        cwd=str(project_dir),
        output_format={
            "type": "json_schema",
            "schema": MonitoringResponse.model_json_schema()
        }
    )

    # Run the agent - will return structured output
    result = None
    processed_message_ids = set()

    async for message in query(prompt=request.task_description, options=options):
        # Log message types
        msg_type = type(message).__name__
        logger.info(f"[{msg_type}]")

        if hasattr(message, "subtype"):
            logger.info(f"  Subtype: {message.subtype}")

        # Log tool uses
        if hasattr(message, "content") and isinstance(message.content, list):
            for block in message.content:
                if hasattr(block, "name"):
                    logger.info(f"  [ToolUse] {block.name}")

        # Track cost per step (avoid double-counting same message ID)
        if isinstance(message, AssistantMessage) and hasattr(message, 'usage'):
            message_id = getattr(message, 'id', None)
            if message_id and message_id not in processed_message_ids:
                processed_message_ids.add(message_id)
                usage = message.usage
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                cache_read = usage.get("cache_read_input_tokens", 0)
                cache_write = usage.get("cache_creation_input_tokens", 0)
                logger.info(f"  Step usage (msg {message_id}): input={input_tokens}, output={output_tokens}, cache_read={cache_read}, cache_write={cache_write}")

        if isinstance(message, ResultMessage):
            if message.subtype == "success" and message.structured_output:
                # Validate and parse into MonitoringResponse
                result = MonitoringResponse.model_validate(message.structured_output)
                logger.info(f"  STRUCTURED OUTPUT: {result}")

                # Log total cost from result message
                if hasattr(message, 'total_cost_usd'):
                    logger.info(f"  TOTAL COST: ${message.total_cost_usd:.4f}")
            elif message.subtype == "error_max_structured_output_retries":
                logger.error("  ERROR: Could not produce valid structured output")

    logger.info("Monitoring task completed")

    # Return the validated result
    if isinstance(result, MonitoringResponse):
        return result

    # Fallback if something went wrong
    return MonitoringResponse(
        condition_met=False,
        evidence="Failed to generate structured output",
        confidence=0,
        next_check_at=None,
        sources=[],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
