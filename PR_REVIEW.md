# PR Review: feat/agentic-workflow

## Summary
This PR introduces a significant and positive architectural shift, moving from a monolithic "god activity" to a structured, pipeline-based approach for monitoring tasks. The introduction of the `MonitoringPipeline` and the decomposition of the `TaskExecutionWorkflow` into granular activities (`get_task_data`, `perform_grounded_search`, `execute_monitoring_pipeline`) greatly improves maintainability, observability, and error handling.

However, there is a **critical bug** in the API endpoint that needs immediate attention, along with some architectural refinements regarding caching and error handling.

## Critical Issues 🚨

### 1. API Endpoint Signature Mismatch
In `backend/src/torale/api/routers/tasks.py`, the `preview_search` function calls `pipeline.execute` with incorrect arguments.

**Current Code:**
```python
monitoring_result = await pipeline.execute(
    search_query=request.search_query,
    condition_description=condition_description,
    search_results=search_result["answer"],
    sources=search_result.get("grounding_sources", []),
    previous_state=None,
)
```

**Actual Signature (`monitoring_pipeline.py`):**
```python
async def execute(
    self,
    task: dict,
    search_result: dict,
    previous_state: dict | None = None,
) -> MonitoringResult:
```

**Fix:**
Construct a `task` dictionary and pass the full `search_result` object.
```python
task_config = {
    "search_query": request.search_query,
    "condition_description": condition_description
}
monitoring_result = await pipeline.execute(
    task=task_config,
    search_result=search_result,
    previous_state=None,
)
```

### 2. Testing Gap
The test `backend/tests/test_preview_endpoint.py` failed to catch the above bug because it mocks `MonitoringPipeline.execute` without verifying that the call signature matches the implementation. The test creates a mock that accepts *any* arguments, masking the runtime `TypeError`.

**Recommendation:** Update the test to verify call arguments or use a more strict mock/fake that adheres to the class interface.

## Architectural Improvements 🏗️

### 3. Ineffective Schema Caching
In `backend/src/torale/providers/gemini/schema.py`, `GeminiSchemaProvider` uses an instance-level dictionary `_schema_cache`.
```python
self._schema_cache = {}
```
In `backend/src/torale/workers/activities.py`, the provider is instantiated fresh for every activity execution via `ProviderFactory`.
```python
pipeline = MonitoringPipeline(
    schema_provider=ProviderFactory.create_schema_provider(provider_type),
    ...
)
```
**Impact:** The cache is empty for every execution, rendering it useless.
**Recommendation:** Since this is a distributed worker environment, either remove the cache (if schema generation is cheap/fast enough) or use a persistent store like Redis. If sticking to in-memory for the same worker process, the cache needs to be static/global or the provider needs to be a singleton (carefully managed).

### 4. Deleted Task Retry Logic
In `backend/src/torale/workers/activities.py`, `get_task_data` raises a `ValueError` if a task is not found.
```python
if not task:
    raise ValueError(f"Task {task_id} not found")
```
The `TaskExecutionWorkflow` uses a default retry policy (max 5 attempts).
**Impact:** If a task is deleted but the schedule triggers, the worker will needlessly retry 5 times before failing.
**Recommendation:** Mark `ValueError` (or a custom `TaskNotFoundError`) as a `non_retryable_error_type` in the workflow's `RetryPolicy`, or handle it explicitly to cancel the schedule.

## Code Quality & Nitpicks 🔍

- **`backend/src/torale/workers/activities.py`**:
  - The import `from torale.core.models import TaskData` is inside the `get_task_data` function. While this avoids circular imports, consider moving it to the top if possible or using `TYPE_CHECKING` blocks for cleaner code structure.

- **`backend/src/torale/providers/gemini/search.py`**:
  - `_extract_domain_from_uri`: The check `if domain.startswith(prefix):` for `m.` (mobile) is good, but ensure it covers other cases if necessary. It's a minor point but `m.` is specific.

- **`backend/src/torale/core/models.py`**:
  - `EnrichedMonitoringResult` unpacking in `TaskExecutionWorkflow` (`**monitoring_result`) assumes `monitoring_result` is a dict matching the schema. This is generally fine given `execute_monitoring_pipeline` returns `result.model_dump()`, but explicit field mapping is often safer for refactoring.

## Conclusion
Great work on the refactoring! The new structure is much cleaner. Please fix the critical API bug and consider the caching and retry logic improvements before merging.
