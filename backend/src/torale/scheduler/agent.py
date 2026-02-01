"""A2A JSON-RPC client for the torale-agent.

Shared by the scheduler (job.py) and the suggest endpoint (tasks router).
"""

import ast
import asyncio
import json
import logging
import time
import uuid

import httpx

from torale.core.config import settings

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 120  # seconds
POLL_BACKOFF = [0.5, 1, 2, 4, 8, 16, 32]  # exponential backoff steps
MAX_CONSECUTIVE_POLL_FAILURES = 3


async def call_agent(prompt: str) -> dict:
    """Send task to torale-agent via A2A JSON-RPC and poll for result."""
    message_id = f"msg-{uuid.uuid4().hex[:12]}"

    async with httpx.AsyncClient(timeout=AGENT_TIMEOUT) as client:
        send_payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{"kind": "text", "text": prompt}],
                }
            },
        }

        try:
            resp = await client.post(settings.agent_url, json=send_payload)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to send task to agent at {settings.agent_url}: {e}") from e

        try:
            send_result = resp.json()
        except Exception as e:
            raise RuntimeError(
                f"Agent returned non-JSON response from {settings.agent_url} "
                f"(status={resp.status_code}): {resp.text[:200]}"
            ) from e

        task_id = send_result.get("result", {}).get("id")
        if not task_id:
            raise RuntimeError(f"Agent did not return task_id: {send_result}")

        logger.info(f"Agent task sent successfully, task_id={task_id}")

        deadline = time.monotonic() + AGENT_TIMEOUT
        backoff_idx = 0
        consecutive_poll_failures = 0

        while time.monotonic() < deadline:
            delay = POLL_BACKOFF[min(backoff_idx, len(POLL_BACKOFF) - 1)]
            await asyncio.sleep(delay)
            backoff_idx += 1

            poll_payload = {
                "jsonrpc": "2.0",
                "id": "2",
                "method": "tasks/get",
                "params": {"id": task_id},
            }

            try:
                poll_resp = await client.post(settings.agent_url, json=poll_payload)
                poll_resp.raise_for_status()
                consecutive_poll_failures = 0
            except httpx.HTTPError as e:
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

            try:
                poll_result = poll_resp.json()
            except Exception as e:
                consecutive_poll_failures += 1
                logger.warning(f"Poll returned non-JSON response for agent task {task_id}: {e}")
                if consecutive_poll_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
                    raise RuntimeError(
                        f"Agent poll returned non-JSON {MAX_CONSECUTIVE_POLL_FAILURES} times "
                        f"for task {task_id}"
                    ) from e
                continue

            task_status = poll_result.get("result", {}).get("status", {})
            state = task_status.get("state") if isinstance(task_status, dict) else task_status

            logger.debug(f"Agent task {task_id} state: {state}")

            if state == "completed":
                return _parse_agent_response(poll_result)
            elif state == "failed":
                error = poll_result.get("result", {}).get("error", "Unknown agent error")
                raise RuntimeError(f"Agent task failed: {error}")

        raise TimeoutError(f"Agent did not complete within {AGENT_TIMEOUT}s")


def _parse_agent_response(poll_result: dict) -> dict:
    """Parse A2A response into monitoring result shape."""
    result = poll_result.get("result", {})

    text_content = ""
    artifacts = result.get("artifacts", [])
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                text_content += part.get("text", "")

    if not text_content:
        raise RuntimeError(
            f"Agent returned empty text content "
            f"(artifacts={len(artifacts)}, result_keys={list(result.keys())})"
        )

    try:
        parsed = json.loads(text_content)
    except (json.JSONDecodeError, TypeError):
        # Agent sometimes returns Python dict repr (single quotes) instead of JSON
        try:
            parsed = ast.literal_eval(text_content)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(f"Agent returned non-JSON response: {text_content[:200]}") from e

    return parsed
