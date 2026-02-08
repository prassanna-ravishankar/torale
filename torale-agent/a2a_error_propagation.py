"""Error propagation system for Pydantic AI A2A framework.

This module patches Pydantic AI's AgentWorker to preserve error details in task status,
allowing the backend to make informed decisions about fallback behavior.

The default A2A implementation catches exceptions during agent.run() and marks tasks as
"failed" but doesn't store error details in a way the backend can retrieve. This module
fixes that by:

1. Providing custom storage that preserves error messages
2. Patching AgentWorker.run_task to capture and serialize exceptions
3. Creating properly structured A2A Messages with error details
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic_ai._a2a import InMemoryStorage
from pydantic_ai.exceptions import ModelHTTPError

logger = logging.getLogger(__name__)


class ErrorAwareStorage(InMemoryStorage):
    """Storage backend that preserves error messages in task status.

    The default InMemoryStorage.update_task() creates a new status dict,
    which drops the 'message' field we set during error handling.
    This subclass preserves it.
    """

    async def update_task(
        self,
        task_id: str,
        state: str,
        new_artifacts: list[dict[str, Any]] | None = None,
        new_messages: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Update task state while preserving existing error message."""
        existing_message = self.tasks.get(task_id, {}).get("status", {}).get("message")

        # Let parent do its normal update
        result = await super().update_task(task_id, state, new_artifacts, new_messages)

        # Restore message if it existed
        if existing_message and task_id in self.tasks:
            self.tasks[task_id]["status"]["message"] = existing_message

        return result


def create_error_message(error: Exception) -> dict:
    """Create A2A Message dict with structured error details.

    Serializes error information into JSON format that the backend can parse.
    Special handling for ModelHTTPError to extract status codes.
    Returns a dict matching the A2A Message schema.
    """
    if isinstance(error, ModelHTTPError):
        error_data = {
            "error_type": "ModelHTTPError",
            "status_code": error.status_code,
            "model_name": error.model_name,
            "message": str(error),
        }
    else:
        error_data = {
            "error_type": type(error).__name__,
            "message": str(error),
        }

    # Return dict matching Pydantic AI's internal A2A Message schema
    return {
        "role": "agent",
        "kind": "message",
        "message_id": str(uuid4()),
        "parts": [{"kind": "text", "text": json.dumps(error_data)}],
    }


def enable_error_propagation() -> None:
    """Patch AgentWorker.run_task to preserve error details in task status.

    This monkey patch intercepts exceptions during agent execution and stores
    them in the task's status.message field as structured JSON before they're lost.

    Must be called before creating the A2A app, and requires using ErrorAwareStorage.
    """
    from pydantic_ai._a2a import AgentWorker

    original_run_task = AgentWorker.run_task

    async def patched_run_task(self, params: dict[str, Any]) -> dict[str, Any]:
        """Wrapper that captures exceptions and stores error details."""
        try:
            return await original_run_task(self, params)
        except (ModelHTTPError, ValueError, RuntimeError) as e:
            logger.error(
                "Agent task failed: %s - %s",
                type(e).__name__,
                str(e),
                extra={"task_id": params["id"], "error_type": type(e).__name__},
            )

            # Store error details in task status using ErrorAwareStorage
            if hasattr(self.storage, "tasks"):
                task = self.storage.tasks.get(params.get("id"))
                if task:
                    error_msg = create_error_message(e)
                    task["status"] = {
                        "state": "failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "message": error_msg,
                    }
                    logger.info("Stored error details in task status for %s", params.get("id"))

            raise

    AgentWorker.run_task = patched_run_task
    logger.info("Patched AgentWorker.run_task to preserve error details")
