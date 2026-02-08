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
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fasta2a.schema import Message, TextPart
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
    ) -> None:
        """Update task state while preserving existing error message."""
        # Capture existing message before parent overwrites status dict
        existing_message = self.tasks.get(task_id, {}).get("status", {}).get("message")

        # Let parent do its normal update
        await super().update_task(task_id, state, new_artifacts, new_messages)

        # Restore message if it existed
        if existing_message and task_id in self.tasks:
            self.tasks[task_id]["status"]["message"] = existing_message


def create_error_message(error: Exception) -> Message:
    """Create A2A Message with structured error details.

    Serializes error information into JSON format that the backend can parse.
    Special handling for ModelHTTPError to extract status codes.
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

    return Message(
        role="agent",
        kind="message",
        message_id=str(uuid4()),
        parts=[TextPart(kind="text", text=json.dumps(error_data))],
    )


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
        except Exception as e:
            logger.info(
                "Capturing error details for task %s: %s",
                params.get("id"),
                type(e).__name__,
            )

            # Store error details in task status using ErrorAwareStorage
            if hasattr(self.storage, "tasks"):
                task = self.storage.tasks.get(params["id"])
                if task:
                    task["status"] = {
                        "state": "failed",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "message": create_error_message(e).model_dump(),
                    }

            raise

    AgentWorker.run_task = patched_run_task
    logger.info("Patched AgentWorker.run_task to preserve error details")
