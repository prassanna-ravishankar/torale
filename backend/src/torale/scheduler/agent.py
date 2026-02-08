"""A2A client for the torale-agent using fasta2a SDK."""

import ast
import asyncio
import json
import logging
import time
import uuid

from fasta2a.client import A2AClient, UnexpectedResponseError
from fasta2a.schema import Message, MessageSendConfiguration, TextPart

from torale.core.config import settings
from torale.scheduler.models import MonitoringResponse

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
POLL_BACKOFF = [0.5, 1, 2, 4, 8, 16, 32]  # exponential backoff steps
MAX_CONSECUTIVE_POLL_FAILURES = 3


async def call_agent(prompt: str) -> MonitoringResponse:
    """Send task to agent with automatic paid tier fallback on 429."""
    try:
        return await _call_agent_internal(settings.agent_url_free, prompt)
    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
            logger.info(
                "Free tier rate limit hit, falling back to paid tier", extra={"error": str(e)[:200]}
            )
            return await _call_agent_internal(settings.agent_url_paid, prompt)
        raise


async def _call_agent_internal(base_url: str, prompt: str) -> MonitoringResponse:
    """Send task to torale-agent via A2A and poll for result."""
    message_id = f"msg-{uuid.uuid4().hex[:12]}"
    client = A2AClient(base_url=base_url)

    message = Message(
        role="user",
        kind="message",
        message_id=message_id,
        parts=[TextPart(kind="text", text=prompt)],
    )

    configuration = MessageSendConfiguration(accepted_output_modes=["application/json"])

    try:
        send_response = await client.send_message(message, configuration=configuration)
    except UnexpectedResponseError as e:
        raise RuntimeError(
            f"Failed to send task to agent at {base_url}: status={e.status_code} {e.content[:200]}"
        ) from e
    except Exception as e:
        raise RuntimeError(f"Failed to send task to agent at {base_url}: {e}") from e

    if "error" in send_response:
        raise RuntimeError(f"Agent returned error: {send_response['error']}")

    task = send_response["result"]
    task_id = task["id"]
    logger.info(f"Agent task sent successfully, task_id={task_id}")

    # Poll for completion
    deadline = time.monotonic() + AGENT_TIMEOUT
    backoff_idx = 0
    consecutive_poll_failures = 0

    while time.monotonic() < deadline:
        delay = POLL_BACKOFF[min(backoff_idx, len(POLL_BACKOFF) - 1)]
        await asyncio.sleep(delay)
        backoff_idx += 1

        try:
            poll_response = await client.get_task(task_id)
            consecutive_poll_failures = 0
        except Exception as e:
            consecutive_poll_failures += 1
            logger.warning(
                f"Poll failure {consecutive_poll_failures}/{MAX_CONSECUTIVE_POLL_FAILURES} "
                f"for agent task {task_id}: {e}"
            )
            if consecutive_poll_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                raise RuntimeError(
                    f"Agent poll failed {MAX_CONSECUTIVE_POLL_FAILURES} consecutive times "
                    f"for task {task_id}"
                ) from e
            continue

        if "error" in poll_response:
            consecutive_poll_failures += 1
            logger.warning(f"Poll error for task {task_id}: {poll_response['error']}")
            if consecutive_poll_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                raise RuntimeError(
                    f"Agent poll returned errors {MAX_CONSECUTIVE_POLL_FAILURES} times "
                    f"for task {task_id}"
                )
            continue

        task = poll_response["result"]
        state = task["status"]["state"]
        logger.debug(f"Agent task {task_id} state: {state}")

        if state == "completed":
            parsed = _parse_agent_response(task)
            return MonitoringResponse.model_validate(parsed)
        elif state == "failed":
            raise RuntimeError(f"Agent task failed: {task.get('status', {})}")

    raise TimeoutError(f"Agent did not complete within {AGENT_TIMEOUT}s")


def _parse_agent_response(task: dict) -> dict:
    """Parse A2A Task into monitoring result shape.

    Prefers DataPart (structured JSON). Falls back to TextPart for legacy
    agent versions -- remove this fallback once all agents return DataPart.
    """
    artifacts = task.get("artifacts", [])
    text_content = ""

    for artifact in artifacts:
        for part in artifact.get("parts", []):
            kind = part.get("kind")

            if kind == "data" and part.get("data"):
                return part["data"]

            if kind == "text":
                text_content += part.get("text", "")

    if not text_content:
        raise RuntimeError(
            f"Agent returned empty response (artifacts={len(artifacts)}, task_keys={list(task.keys())})"
        )

    # Legacy fallback: parse text as JSON
    try:
        return json.loads(text_content)
    except (json.JSONDecodeError, TypeError):
        pass

    # Agent sometimes returns Python dict repr (single quotes)
    try:
        return ast.literal_eval(text_content)
    except (ValueError, SyntaxError) as e:
        raise RuntimeError(f"Agent returned non-JSON text response: {text_content[:200]}") from e
