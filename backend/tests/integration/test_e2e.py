import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_e2e(client: AsyncClient):
    # 1. Create task
    task_payload = {
        "name": "E2E Test Task (Pytest)",
        "schedule": "0 9 * * *",
        "search_query": "What is 2+2?",
        "condition_description": "A numerical answer is provided",
        "notify_behavior": "always",
    }

    response = await client.post("/api/v1/tasks", json=task_payload)
    assert response.status_code == 200, f"Create task failed: {response.text}"
    task_data = response.json()
    task_id = task_data["id"]
    assert task_id is not None

    try:
        # 2. Execute task
        response = await client.post(f"/api/v1/tasks/{task_id}/execute")
        assert response.status_code == 200, f"Execute task failed: {response.text}"
        execution_data = response.json()
        execution_id = execution_data["id"]
        assert execution_id is not None

        # 3. Poll for completion
        max_retries = 60
        for _ in range(max_retries):
            await asyncio.sleep(1)
            response = await client.get(f"/api/v1/tasks/{task_id}/executions")
            assert response.status_code == 200
            executions = response.json()

            if not executions:
                continue

            # Assuming most recent is first
            current_status = executions[0].get("status")

            if current_status == "success":
                break
            elif current_status == "failed":
                pytest.fail(f"Execution failed: {executions[0].get('error_message')}")
        else:
            pytest.fail("Timeout waiting for execution completion")

    finally:
        # 4. Cleanup
        await client.delete(f"/api/v1/tasks/{task_id}")
