"""Torale agent A2A server."""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import logfire
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.events.event_queue import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    Artifact,
    DataPart,
    Message,
    Role,
    Task as A2ATask,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError

from agent import create_monitoring_agent
from models import Clients, MonitoringDeps, MonitoringResponse, create_clients
from tools import extract_activity

load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ToraleAgentExecutor(AgentExecutor):
    """A2A executor that runs the Torale monitoring agent."""

    def __init__(self, agent: Agent[MonitoringDeps, MonitoringResponse]) -> None:
        self.agent = agent
        self.clients: Clients | None = None

    async def _emit_failure(
        self, event_queue: EventQueue, task_id: str, context_id: str, error_data: dict
    ) -> None:
        """Enqueue a failed A2ATask with structured error details in status.message."""
        await event_queue.enqueue_event(
            A2ATask(
                id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=Message(
                        message_id=str(uuid4()),
                        role=Role.agent,
                        parts=[TextPart(text=json.dumps(error_data))],  # type: ignore
                    ),
                ),
            )
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute a monitoring task received via A2A protocol.

        Extracts user context from A2A metadata, runs the Pydantic AI agent with
        monitoring dependencies, and emits task results via the A2A event queue.

        Workflow:
        1. Extract user_id and task_id from context.metadata
        2. Emit "working" state to caller
        3. Run agent with MonitoringDeps context
        4. On success: emit completed task with MonitoringResponse as DataPart artifact
        5. On error: emit failed task with structured error details in status.message

        Args:
            context: A2A request context containing task metadata (user_id, task_id required)
            event_queue: Queue for emitting task state updates and results

        Error Handling:
            - ConfigurationError: Missing user_id or task_id in metadata
            - ModelHTTPError: Preserves status_code for 429 rate limit detection
            - ValueError/RuntimeError: General execution failures
        """
        task_id = context.task_id or ""
        context_id = context.context_id or ""
        user_input = context.get_user_input()

        # Extract user_id and task_id from A2A metadata
        # Security note: This agent is deployed as ClusterIP (internal-only) in production,
        # accessible only from the authenticated backend. The backend validates user sessions
        # and ensures user_id/task_id match the authenticated user before calling this endpoint.
        # External spoofing is mitigated by network isolation.
        metadata = context.metadata
        user_id = metadata.get("user_id", "")
        monitoring_task_id = metadata.get("task_id", "")

        if not user_id or not monitoring_task_id:
            missing = [
                f"'{field}'"
                for field, value in (
                    ("user_id", user_id),
                    ("task_id", monitoring_task_id),
                )
                if not value
            ]
            error_msg = f"Missing required metadata: {', '.join(missing)}"
            logger.error(
                "Agent task failed: %s",
                error_msg,
                extra={"task_id": task_id, "metadata": metadata},
            )
            await self._emit_failure(
                event_queue,
                task_id,
                context_id,
                {
                    "error_type": "ConfigurationError",
                    "message": error_msg,
                    "metadata_received": metadata,
                },
            )
            return

        deps = MonitoringDeps(
            user_id=user_id, task_id=monitoring_task_id, clients=self.clients
        )

        # Signal working state
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                final=False,
                status=TaskStatus(state=TaskState.working),
            )
        )

        try:
            result = await self.agent.run(user_input, deps=deps)
            response = result.output

            # Extract activity trail from message history
            activity = extract_activity(result.all_messages())
            if activity:
                response.activity = activity

            # Return completed Task with MonitoringResponse as DataPart artifact
            await event_queue.enqueue_event(
                A2ATask(
                    id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.completed),
                    artifacts=[
                        Artifact(
                            artifact_id=str(uuid4()),
                            parts=[DataPart(data=response.model_dump(mode="json"))],  # type: ignore
                        )
                    ],
                )
            )

        except ModelHTTPError as e:
            logger.error(
                "Agent task failed: ModelHTTPError - %s (status=%d, model=%s)",
                str(e),
                e.status_code,
                e.model_name,
                extra={
                    "task_id": task_id,
                    "user_id": user_id,
                    "monitoring_task_id": monitoring_task_id,
                    "model_name": e.model_name,
                    "status_code": e.status_code,
                },
            )
            await self._emit_failure(
                event_queue,
                task_id,
                context_id,
                {
                    "error_type": "ModelHTTPError",
                    "status_code": e.status_code,
                    "model_name": str(e.model_name),
                    "message": str(e),
                },
            )

        except (ValueError, RuntimeError) as e:
            logger.error(
                "Agent task failed: %s - %s",
                type(e).__name__,
                str(e),
                exc_info=True,
                extra={
                    "task_id": task_id,
                    "user_id": user_id,
                    "monitoring_task_id": monitoring_task_id,
                    "error_type": type(e).__name__,
                },
            )
            await self._emit_failure(
                event_queue,
                task_id,
                context_id,
                {
                    "error_type": type(e).__name__,
                    "message": str(e),
                },
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id or "",
                context_id=context.context_id or "",
                final=True,
                status=TaskStatus(state=TaskState.canceled),
            )
        )


agent_card = AgentCard(
    name="torale-agent",
    description="Torale search monitoring agent",
    url="http://localhost:8001/",
    version="0.1.0",
    default_input_modes=["text"],
    default_output_modes=["text"],
    capabilities=AgentCapabilities(),
    skills=[],
)


monitoring_agent = create_monitoring_agent()
executor = ToraleAgentExecutor(monitoring_agent)
task_store = InMemoryTaskStore()
request_handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=task_store,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with create_clients() as clients:
        executor.clients = clients
        yield
        executor.clients = None


a2a_app = A2AFastAPIApplication(
    agent_card=agent_card,
    http_handler=request_handler,
)

app = a2a_app.build(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ok"}
