"""A2A client for the torale-agent using a2a-sdk."""

import ast
import asyncio
import json
import logging
import time
import uuid

import httpx
from a2a.client import A2AClient
from a2a.client.errors import A2AClientHTTPError
from a2a.types import (
    DataPart,
    GetTaskRequest,
    JSONRPCErrorResponse,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskQueryParams,
    TaskState,
    TextPart,
)

from torale.core.config import settings
from torale.lib.posthog import capture as posthog_capture
from torale.scheduler.models import MonitoringResponse

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
POLL_BACKOFF = [0.5, 1, 2, 4, 8, 16, 32]  # exponential backoff steps
MAX_CONSECUTIVE_POLL_FAILURES = 3


def _extract_error_details(task: Task) -> dict | None:
    """Extract structured error details from failed task.

    Checks both artifacts (new a2a-sdk format) and status.message (legacy fallback).
    Returns None if error details are missing or malformed.
    """
    # First try artifacts (new format with a2a-sdk)
    artifacts = task.artifacts or []
    for artifact in artifacts:
        for part_wrapper in artifact.parts:
            part = part_wrapper.root
            if isinstance(part, DataPart) and part.data:
                data = part.data
                if isinstance(data, dict) and "error_type" in data:
                    return data

    # Fallback: check status.message (legacy format)
    message = task.status.message
    if not message:
        return None

    parts = message.parts
    if not parts:
        return None

    part = parts[0].root
    if not isinstance(part, TextPart):
        return None

    text = part.text
    if not text:
        return None

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(
            "Failed to parse error details from task status: %s. Raw content: %s",
            e,
            text[:500],
        )
        # Return structured error instead of None to preserve context
        return {
            "error_type": "JSONParseError",
            "message": f"Agent returned malformed error data: {text[:200]}",
            "parse_error": str(e),
        }


def _handle_failed_task(task: Task) -> None:
    """Process failed task and raise appropriate error.

    Extracts error details from task status and raises:
    - A2AClientHTTPError(429) for rate limits (triggers paid tier fallback)
    - RuntimeError for other errors
    """
    task_id = task.id
    error_details = _extract_error_details(task)

    if not error_details:
        raise RuntimeError(f"Agent task {task_id} failed without error details: {task.status}")

    error_type = error_details.get("error_type")
    message = error_details.get("message", "Unknown error")

    logger.info(
        "Extracted agent error details: type=%s, message=%s",
        error_type,
        message[:200],
    )

    if error_type == "ModelHTTPError":
        status_code = error_details.get("status_code")
        if status_code == 429:
            raise A2AClientHTTPError(429, f"Agent task {task_id} hit rate limit: {message}")
        raise RuntimeError(f"Agent task {task_id} HTTP error {status_code}: {message}")

    raise RuntimeError(f"Agent task {task_id} {error_type}: {message}")


async def call_agent(
    prompt: str, user_id: str | None = None, task_id: str | None = None
) -> MonitoringResponse:
    """Send task to agent with automatic paid tier fallback on 429."""
    try:
        result = await _call_agent_internal(settings.agent_url_free, prompt, user_id, task_id)
        tier, fallback = "free", False
    except A2AClientHTTPError as e:
        if e.status_code != 429:
            raise
        logger.info(
            "Free tier rate limit hit (429), falling back to paid tier",
            extra={"status_code": e.status_code},
        )
        result = await _call_agent_internal(settings.agent_url_paid, prompt, user_id, task_id)
        tier, fallback = "paid", True

    if user_id:
        posthog_capture(
            distinct_id=user_id,
            event="agent_tier_used",
            properties={
                "tier": tier,
                "fallback_triggered": fallback,
            },
        )
    return result


async def _call_agent_internal(
    base_url: str, prompt: str, user_id: str | None = None, task_id: str | None = None
) -> MonitoringResponse:
    """Send task to torale-agent via A2A and poll for result."""
    message_id = f"msg-{uuid.uuid4().hex[:12]}"
    request_id = f"req-{uuid.uuid4().hex[:12]}"

    async with httpx.AsyncClient() as httpx_client:
        client = A2AClient(httpx_client=httpx_client, url=base_url)
        poll_start_time = time.monotonic()

        message = Message(
            role=Role.user,
            kind="message",
            message_id=message_id,
            parts=[Part(root=TextPart(kind="text", text=prompt))],
        )

        configuration = MessageSendConfiguration(accepted_output_modes=["application/json"])

        request = SendMessageRequest(
            id=request_id,
            params=MessageSendParams(
                message=message,
                configuration=configuration,
                metadata={"user_id": user_id, "task_id": task_id},
            ),
        )

        try:
            send_response = await client.send_message(request)
        except A2AClientHTTPError as e:
            # Re-raise 429 to preserve status_code for fallback logic
            # Wrap other HTTP errors in RuntimeError for consistent error handling
            if e.status_code == 429:
                raise
            raise RuntimeError(
                f"Failed to send task to agent at {base_url}: status={e.status_code} {e.message[:200]}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to send task to agent at {base_url}: {e}") from e

        response = send_response.root
        if isinstance(response, JSONRPCErrorResponse):
            raise RuntimeError(f"Agent returned error: {response.error}")

        task = response.result
        a2a_task_id = task.id
        logger.info(f"Agent task sent successfully, task_id={a2a_task_id}")

        # Poll for completion
        deadline = time.monotonic() + AGENT_TIMEOUT
        backoff_idx = 0
        consecutive_poll_failures = 0
        poll_count = 0

        while time.monotonic() < deadline:
            poll_count += 1
            delay = POLL_BACKOFF[min(backoff_idx, len(POLL_BACKOFF) - 1)]
            await asyncio.sleep(delay)
            backoff_idx += 1

            try:
                poll_response = await client.get_task(
                    GetTaskRequest(
                        id=request_id,
                        params=TaskQueryParams(id=a2a_task_id),
                    )
                )
                consecutive_poll_failures = 0
            except Exception as e:
                consecutive_poll_failures += 1
                logger.warning(
                    f"Poll failure {consecutive_poll_failures}/{MAX_CONSECUTIVE_POLL_FAILURES} "
                    f"for agent task {a2a_task_id}: {e}"
                )
                if consecutive_poll_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                    raise RuntimeError(
                        f"Agent poll failed {MAX_CONSECUTIVE_POLL_FAILURES} consecutive times "
                        f"for task {a2a_task_id}"
                    ) from e
                continue

            poll_result = poll_response.root
            if isinstance(poll_result, JSONRPCErrorResponse):
                consecutive_poll_failures += 1
                logger.warning(f"Poll error for task {a2a_task_id}: {poll_result.error}")
                if consecutive_poll_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                    raise RuntimeError(
                        f"Agent poll returned errors {MAX_CONSECUTIVE_POLL_FAILURES} times "
                        f"for task {a2a_task_id}"
                    )
                continue

            task = poll_result.result
            state = task.status.state
            logger.debug(f"Agent task {a2a_task_id} state: {state}")

            match state:
                case TaskState.completed:
                    parsed = _parse_agent_response(task)
                    poll_duration = time.monotonic() - poll_start_time
                    if user_id:
                        posthog_capture(
                            distinct_id=user_id,
                            event="agent_task_completed",
                            properties={
                                "poll_duration_seconds": round(poll_duration, 2),
                                "poll_iterations": poll_count,
                            },
                        )
                    return MonitoringResponse.model_validate(parsed)
                case TaskState.failed:
                    _handle_failed_task(task)
                case TaskState.working | TaskState.submitted:
                    continue

        raise TimeoutError(f"Agent did not complete within {AGENT_TIMEOUT}s")


def _parse_agent_response(task: Task) -> dict:
    """Parse A2A Task into monitoring result shape.

    Prefers DataPart (structured JSON). Falls back to TextPart for legacy
    agent versions -- remove this fallback once all agents return DataPart.
    """
    artifacts = task.artifacts or []
    text_content = ""

    for artifact in artifacts:
        for part_wrapper in artifact.parts:
            part = part_wrapper.root

            if isinstance(part, DataPart) and part.data:
                data = part.data
                # Unwrap if agent wrapped response in 'result' key
                if isinstance(data, dict) and "result" in data and len(data) == 1:
                    return data["result"]
                return data

            if isinstance(part, TextPart):
                text_content += part.text or ""

    if not text_content:
        raise RuntimeError(
            f"Agent returned empty response (artifacts={len(artifacts)}, task_keys={list(Task.model_fields.keys())})"
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
