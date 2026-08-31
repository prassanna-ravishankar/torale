"""Torale agent A2A server."""

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import logfire
from a2a.helpers import (
    new_data_artifact_update_event,
    new_task_from_user_message,
    new_text_message,
)
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.mcp import MCPToolset
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from agent import create_monitoring_agent
from models import Clients, MonitoringDeps, MonitoringResponse, create_clients
from runtime import MONITORING_USAGE_LIMITS, record_run_usage
from tools import extract_activity

load_dotenv()

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _build_mcp_toolsets(
    mcp_servers: list[dict] | None,
) -> list[MCPToolset]:
    """Construct Pydantic AI MCP toolsets from A2A metadata entries.

    Each entry is expected to be {"toolkit": str, "url": str}. The Composio API
    key is read from the process env since the backend doesn't ship the secret
    over the wire. FastMCP owns the connection lifecycle and follows Composio's
    endpoint redirects, so no shared HTTP client or manual cleanup is required.
    """
    if not mcp_servers:
        return []
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        logger.warning(
            "mcp_servers passed in metadata but COMPOSIO_API_KEY not set in agent env; "
            "MCP tools will be unreachable for this run"
        )
        return []

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
        return []

    return [
        MCPToolset(url, headers={"x-api-key": api_key}, id=toolkit)
        for toolkit, url in valid_entries
    ]


class ToraleAgentExecutor(AgentExecutor):
    """A2A executor that runs the Torale monitoring agent."""

    def __init__(self, agent: Agent[MonitoringDeps, MonitoringResponse]) -> None:
        self.agent = agent
        self.clients: Clients | None = None

    async def _emit_failure(
        self, event_queue: EventQueue, task_id: str, context_id: str, error_data: dict
    ) -> None:
        """Enqueue a final failed status with structured error details."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.TASK_STATE_FAILED,
                    message=new_text_message(
                        json.dumps(error_data),
                        context_id=context_id,
                        task_id=task_id,
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

        if context.message is None:
            raise ValueError("A2A request is missing its user message")

        # A2A 1.x requires task mode to start with the initial Task before any
        # status or artifact updates are emitted.
        await event_queue.enqueue_event(new_task_from_user_message(context.message))

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

        mcp_toolsets = _build_mcp_toolsets(metadata.get("mcp_servers"))

        # Signal working state
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(state=TaskState.TASK_STATE_WORKING),
            )
        )

        try:
            result = await self.agent.run(
                user_input,
                deps=deps,
                toolsets=mcp_toolsets or None,
                usage_limits=MONITORING_USAGE_LIMITS,
            )
            record_run_usage(
                result,
                operation="a2a",
                task_id=monitoring_task_id,
                user_id=user_id,
            )
            response = result.output

            # Extract activity trail from message history
            activity = extract_activity(result.all_messages())
            if activity:
                response.activity = activity

            # Stream the structured application result, then finish the task.
            await event_queue.enqueue_event(
                new_data_artifact_update_event(
                    task_id=task_id,
                    context_id=context_id,
                    name="monitoring-response",
                    data=response.model_dump(mode="json"),
                    media_type="application/json",
                    last_chunk=True,
                )
            )
            await event_queue.enqueue_event(
                TaskStatusUpdateEvent(
                    task_id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
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
                status=TaskStatus(state=TaskState.TASK_STATE_CANCELED),
            )
        )


agent_card = AgentCard(
    name="torale-agent",
    description="Torale search monitoring agent",
    supported_interfaces=[
        AgentInterface(
            url=os.environ.get("AGENT_URL", "http://localhost:8001"),
            protocol_binding="JSONRPC",
            protocol_version="1.0",
        )
    ],
    version="0.1.0",
    default_input_modes=["text"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=True),
    skills=[],
)


monitoring_agent = create_monitoring_agent()
executor = ToraleAgentExecutor(monitoring_agent)
task_store = InMemoryTaskStore()
request_handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=task_store,
    agent_card=agent_card,
)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with create_clients() as clients:
        executor.clients = clients
        try:
            yield
        finally:
            executor.clients = None
            await request_handler.aclose()


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/ready", health, methods=["GET"]),
    *create_agent_card_routes(agent_card),
    *create_jsonrpc_routes(request_handler, rpc_url="/"),
]

app = Starlette(routes=routes, lifespan=lifespan)
