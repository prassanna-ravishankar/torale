"""Torale agent A2A server."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
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
from pydantic_ai.mcp import MCPServerStreamableHTTP

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


def _build_mcp_toolsets(
    mcp_servers: list[dict] | None,
) -> tuple[list[MCPServerStreamableHTTP], list[httpx.AsyncClient]]:
    """Construct Pydantic AI MCP toolsets from A2A metadata entries.

    Each entry is expected to be {"toolkit": str, "url": str}. The composio API
    key is read from the process env since the backend doesn't ship the secret
    over the wire. Returns ([], []) when mcp_servers is None/empty so the common
    path stays allocation-free.

    Composio's `mcp.generate()` returns a URL that 307-redirects to the real
    endpoint (`.../v3/mcp/{id}` -> `.../v3/mcp/{id}/mcp`). The MCP streamable-http
    client doesn't follow redirects by default, so we share one httpx client
    across all toolsets with `follow_redirects=True`. The toolsets share config
    (the same x-api-key header), so a single client suffices.

    The shared client is returned alongside the toolsets so the caller can
    close it after the agent run — otherwise each run leaks file descriptors.
    """
    if not mcp_servers:
        return [], []
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        logger.warning(
            "mcp_servers passed in metadata but COMPOSIO_API_KEY not set in agent env; "
            "MCP tools will be unreachable for this run"
        )
        return [], []

    # Build entries first so we don't allocate a client when nothing valid lands.
    valid_entries: list[tuple[str, str]] = []
    for entry in mcp_servers:
        url = entry.get("url") if isinstance(entry, dict) else None
        toolkit = entry.get("toolkit") if isinstance(entry, dict) else None
        if not url or not toolkit:
            logger.warning("Skipping malformed mcp_server entry: %r", entry)
            continue
        valid_entries.append((toolkit, url))

    if not valid_entries:
        return [], []

    shared_client = httpx.AsyncClient(
        follow_redirects=True,
        headers={"x-api-key": api_key},
    )
    toolsets = [
        MCPServerStreamableHTTP(url=url, http_client=shared_client, id=toolkit)
        for toolkit, url in valid_entries
    ]
    return toolsets, [shared_client]


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

        mcp_toolsets, mcp_http_clients = _build_mcp_toolsets(metadata.get("mcp_servers"))

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
            result = await self.agent.run(
                user_input,
                deps=deps,
                toolsets=mcp_toolsets or None,
            )
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
        finally:
            if mcp_http_clients:
                results = await asyncio.gather(
                    *(client.aclose() for client in mcp_http_clients),
                    return_exceptions=True,
                )
                for res in results:
                    if isinstance(res, Exception):
                        logger.warning(
                            "Failed to close MCP httpx client", exc_info=res
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
