"""A2A client for the torale-agent using a2a-sdk."""

import asyncio
import json
import logging
import time
import uuid
from http import HTTPStatus

import httpx
from a2a.client import ClientConfig, create_client
from a2a.client.errors import A2AClientError
from a2a.helpers import get_data_parts, get_text_parts, new_text_message
from a2a.types import (
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    StreamResponse,
    Task,
    TaskState,
)

from webwhen.core.config import settings
from webwhen.lib.posthog import capture as posthog_capture
from webwhen.scheduler.models import MonitoringResponse

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
# Upstream model failures worth retrying on the paid tier.
FALLBACK_STATUS_CODES = frozenset({HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.SERVICE_UNAVAILABLE})

# Reuse httpx client for connection pooling
_httpx_client: httpx.AsyncClient | None = None


class AgentUpstreamHTTPError(RuntimeError):
    """Structured model-provider failure eligible for tier fallback."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _get_httpx_client() -> httpx.AsyncClient:
    """Get or create a shared httpx client for connection reuse."""
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(timeout=AGENT_TIMEOUT))
    return _httpx_client


def _extract_error_details(task: Task) -> dict | None:
    """Extract structured error details from a failed task's status.message.

    The agent emits error details as JSON-encoded TextPart in status.message.

    Returns:
        Parsed error dict if valid JSON found.
        Fallback error dict with error_type="JSONParseError" if parsing fails.
        None if status.message or parts are missing.
    """
    message = task.status.message
    if not message or not message.parts:
        return None

    part = message.parts[0]
    if not part.HasField("text") or not part.text:
        return None

    try:
        return json.loads(part.text)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(
            "Failed to parse error details from task status: %s. Raw content: %s",
            e,
            part.text[:500],
        )
        return {
            "error_type": "JSONParseError",
            "message": f"Agent returned malformed error data: {part.text[:200]}",
            "parse_error": str(e),
        }


def _handle_failed_task(task: Task) -> None:
    """Process failed task and raise appropriate error.

    Extracts error details from task status and raises:
    - AgentUpstreamHTTPError for failures eligible for paid tier fallback
      (see FALLBACK_STATUS_CODES)
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
        if status_code in FALLBACK_STATUS_CODES:
            raise AgentUpstreamHTTPError(
                status_code, f"Agent task {task_id} upstream {status_code}: {message}"
            )
        raise RuntimeError(f"Agent task {task_id} HTTP error {status_code}: {message}")

    raise RuntimeError(f"Agent task {task_id} {error_type}: {message}")


async def call_agent(
    prompt: str,
    user_id: str | None = None,
    task_id: str | None = None,
    mcp_servers: list[dict] | None = None,
) -> MonitoringResponse:
    """Send task to agent with automatic paid tier fallback on upstream failures.

    mcp_servers is a list of `{toolkit, url}` dicts; forwarded in A2A metadata
    so the agent can wire per-run MCP tools. Omit or empty for the common
    no-connectors path.
    """
    try:
        result = await _call_agent_internal(
            settings.agent_url_free, prompt, user_id, task_id, mcp_servers
        )
        tier, fallback = "free", False
    except AgentUpstreamHTTPError as e:
        if e.status_code not in FALLBACK_STATUS_CODES:
            raise
        logger.info(
            "Free tier upstream failure (%s), falling back to paid tier",
            e.status_code,
            extra={"status_code": e.status_code},
        )
        result = await _call_agent_internal(
            settings.agent_url_paid, prompt, user_id, task_id, mcp_servers
        )
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
    base_url: str,
    prompt: str,
    user_id: str | None = None,
    task_id: str | None = None,
    mcp_servers: list[dict] | None = None,
) -> MonitoringResponse:
    """Stream one monitoring task from torale-agent over A2A."""
    message_id = f"msg-{uuid.uuid4().hex[:12]}"

    httpx_client = _get_httpx_client()
    stream_start_time = time.monotonic()

    message = new_text_message(
        prompt,
        role=Role.ROLE_USER,
    )
    message.message_id = message_id

    configuration = SendMessageConfiguration(accepted_output_modes=["application/json"])

    metadata: dict = {"user_id": user_id, "task_id": task_id}
    if mcp_servers:
        metadata["mcp_servers"] = mcp_servers

    request = SendMessageRequest(
        message=message,
        configuration=configuration,
        metadata=metadata,
    )

    try:
        async with asyncio.timeout(AGENT_TIMEOUT):
            client = await create_client(
                base_url,
                ClientConfig(
                    streaming=True,
                    polling=False,
                    httpx_client=httpx_client,
                    accepted_output_modes=["application/json"],
                ),
            )
            task: Task | None = None
            event_count = 0

            stream = client.send_message(request)
            async for event in stream:
                event_count += 1
                task = _apply_stream_event(task, event)
                if task is None:
                    continue

                state = task.status.state
                logger.debug("Agent task %s state: %s", task.id, TaskState.Name(state))

                if state == TaskState.TASK_STATE_COMPLETED:
                    parsed = _parse_agent_response(task)
                    if user_id:
                        posthog_capture(
                            distinct_id=user_id,
                            event="agent_task_completed",
                            properties={
                                "stream_duration_seconds": round(
                                    time.monotonic() - stream_start_time, 2
                                ),
                                "stream_event_count": event_count,
                                "terminal_state": TaskState.Name(state),
                            },
                        )
                    return MonitoringResponse.model_validate(parsed)
                if state == TaskState.TASK_STATE_FAILED:
                    _handle_failed_task(task)
                if state in {
                    TaskState.TASK_STATE_CANCELED,
                    TaskState.TASK_STATE_REJECTED,
                }:
                    raise RuntimeError(f"Agent task {task.id} ended in {TaskState.Name(state)}")

            raise RuntimeError("Agent stream ended without a terminal task response")
    except TimeoutError as e:
        raise TimeoutError(f"Agent did not complete within {AGENT_TIMEOUT}s") from e
    except AgentUpstreamHTTPError:
        raise
    except (A2AClientError, httpx.HTTPError, ValueError) as e:
        raise RuntimeError(f"Failed to stream task from agent at {base_url}: {e}") from e


def _apply_stream_event(task: Task | None, event: StreamResponse) -> Task | None:
    """Fold an A2A stream event into the latest task snapshot."""
    if event.HasField("task"):
        task = Task()
        task.CopyFrom(event.task)
        return task

    if task is None:
        return None

    if event.HasField("status_update"):
        task.status.CopyFrom(event.status_update.status)
    elif event.HasField("artifact_update"):
        update = event.artifact_update
        artifact = update.artifact
        existing = next(
            (item for item in task.artifacts if item.artifact_id == artifact.artifact_id),
            None,
        )
        if existing is None:
            task.artifacts.add().CopyFrom(artifact)
        elif update.append:
            existing.parts.extend(artifact.parts)
        else:
            existing.CopyFrom(artifact)
    return task


def _parse_agent_response(task: Task) -> dict:
    """Parse A2A Task into monitoring result shape.

    Prefers structured data. A narrow JSON text fallback remains while the
    server's temporary A2A v0.3 compatibility route is enabled.
    """
    artifacts = task.artifacts or []
    text_content = ""

    for artifact in artifacts:
        for data in get_data_parts(artifact.parts):
            if data:
                # Unwrap if agent wrapped response in 'result' key
                if isinstance(data, dict) and "result" in data and len(data) == 1:
                    return data["result"]
                return data
        text_content += "".join(get_text_parts(artifact.parts))

    if not text_content:
        raise RuntimeError(f"Agent returned empty response (artifacts={len(artifacts)})")

    # Legacy fallback: parse text as JSON
    try:
        return json.loads(text_content)
    except (json.JSONDecodeError, TypeError):
        pass

    raise RuntimeError(f"Agent returned non-JSON text response: {text_content[:200]}")
