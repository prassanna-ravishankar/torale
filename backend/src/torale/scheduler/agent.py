"""A2A client for the torale-agent using fasta2a SDK."""

import ast
import asyncio
import json
import logging
import time
import uuid

from fasta2a.client import A2AClient, UnexpectedResponseError
from fasta2a.schema import Message, MessageSendConfiguration, TaskState, TextPart

from torale.core.config import settings
from torale.scheduler.models import MonitoringResponse

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
POLL_BACKOFF = [0.5, 1, 2, 4, 8, 16, 32]  # exponential backoff steps
MAX_CONSECUTIVE_POLL_FAILURES = 3


def _extract_error_details(task: dict) -> dict | None:
    """Extract structured error details from failed task's status message.

    The agent stores errors as JSON in task["status"]["message"]["parts"][0]["text"].
    Returns None if the error details are missing or malformed.
    """
    message = task.get("status", {}).get("message")
    if not message:
        return None

    parts = message.get("parts", [])
    if not parts:
        return None

    text = parts[0].get("text")
    if not text:
        return None

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("Failed to parse error details from task status: %s", e)
        return None


def _handle_failed_task(task: dict) -> None:
    """Process failed task and raise appropriate error.

    Extracts error details from task status and raises:
    - UnexpectedResponseError(429) for rate limits (triggers paid tier fallback)
    - RuntimeError for other errors
    """
    error_details = _extract_error_details(task)

    if not error_details:
        raise RuntimeError(f"Agent task failed without error details: {task.get('status', {})}")

    error_type = error_details.get("error_type")
    message = error_details.get("message", "Unknown error")

    if error_type == "ModelHTTPError":
        status_code = error_details.get("status_code")
        if status_code == 429:
            raise UnexpectedResponseError(429, f"Agent hit rate limit: {message}")
        raise RuntimeError(f"Agent HTTP error {status_code}: {message}")

    raise RuntimeError(f"Agent {error_type}: {message}")


async def call_agent(prompt: str) -> MonitoringResponse:
    """Send task to agent with automatic paid tier fallback on 429."""
    try:
        return await _call_agent_internal(settings.agent_url_free, prompt)
    except UnexpectedResponseError as e:
        # Check actual HTTP status code (not error message) to avoid prompt injection
        if e.status_code == 429:
            logger.info(
                "Free tier rate limit hit (429), falling back to paid tier",
                extra={"status_code": e.status_code},
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
        # Re-raise 429 to preserve status_code for fallback logic
        # Wrap other HTTP errors in RuntimeError for consistent error handling
        if e.status_code == 429:
            raise
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
        state: TaskState = task["status"]["state"]
        logger.debug(f"Agent task {task_id} state: {state}")

        match state:
            case "completed":
                parsed = _parse_agent_response(task)
                return MonitoringResponse.model_validate(parsed)
            case "failed":
                _handle_failed_task(task)
            case "working" | "submitted":
                continue

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
