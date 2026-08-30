# A2A 1.x and Pydantic AI 2.x boundary

- Backend and agent are upgraded together because their wire contract meets in
  `backend/src/webwhen/scheduler/agent.py` and `torale-agent/server.py`.
- A2A 1.x uses protobuf messages and streamed `StreamResponse` events. The
  executor must emit an initial `Task` before status or artifact updates.
- The backend consumes `Client.send_message()` directly. Do not reintroduce
  `get_task()` polling, exponential backoff, or v0.3 Pydantic wire wrappers.
- The structured application result is a data artifact containing exactly the
  duplicated `MonitoringResponse` schema. The copies stay local so the services
  can deploy independently; `torale-agent/tests/test_backend_contract.py`
  compares their structural Pydantic schemas and makes drift a CI failure.
- Paid-tier fallback is application behavior, not transport behavior. The agent
  serializes `ModelHTTPError` details into the final failed status; the backend
  falls back only for 429 and 503.
- `MCPToolset` owns MCP connection entry/exit per agent run. Do not allocate a
  shared MCP `httpx.AsyncClient` or manually close MCP transports.
- Pydantic AI 2 defaults to `end_strategy="graceful"`; webwhen explicitly uses
  `"early"` to preserve the previous monitoring semantics.
- The temporary A2A v0.3-compatible JSON-RPC route is scheduled for removal by
  2026-09-30 in issue #363. New code must use 1.x APIs only.
- `AGENT_URL` is the URL advertised in the agent card. Helm sets it per tier;
  docker-compose must do the same for `agent-free` and `agent-paid`.
- Agent lint, typecheck, import, unit tests, and real in-process protocol tests
  are required in PR CI and through `just lint` / `just test`.
