import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_grounded_search_e2e(client: AsyncClient):
    """
    Test grounded search functionality.
    Verifies:
    1. Task creation with search query and condition
    2. Execution results (condition_met, grounding_sources, answer)
    3. Notifications endpoint
    4. Task state tracking
    """

    # 1. Create grounded search task
    task_payload = {
        "name": "Test Grounded Search (Pytest)",
        "schedule": "0 9 * * *",
        "search_query": "What is the capital of France?",
        "condition_description": "A clear answer with the city name is provided",
        "notify_behavior": "once",
        "is_active": False,
    }

    response = await client.post("/api/v1/tasks", json=task_payload)
    assert response.status_code == 200, f"Create task failed: {response.text}"
    task_data = response.json()
    task_id = task_data["id"]

    # Verify fields
    assert task_data["search_query"] == task_payload["search_query"]
    assert task_data["condition_description"] == task_payload["condition_description"]
    assert task_data["notify_behavior"] == task_payload["notify_behavior"]

    try:
        # 2. Execute task manually
        response = await client.post(f"/api/v1/tasks/{task_id}/execute")
        assert response.status_code == 200

        # 3. Wait for completion
        max_retries = 30
        execution_result = None

        for _ in range(max_retries):
            await asyncio.sleep(2)

            response = await client.get(f"/api/v1/tasks/{task_id}/executions")
            assert response.status_code == 200
            executions = response.json()

            if not executions:
                continue

            latest = executions[0]
            if latest["status"] == "success":
                execution_result = latest
                break
            elif latest["status"] == "failed":
                pytest.fail(f"Execution failed: {latest.get('error_message')}")

        if not execution_result:
            pytest.fail("Execution did not complete within 60 seconds")

        # Verify grounded search specific fields
        assert "condition_met" in execution_result, "Missing condition_met field"
        assert "grounding_sources" in execution_result, "Missing grounding_sources field"
        assert execution_result["result"].get("answer"), "Missing answer in result"

        condition_met = execution_result["condition_met"]

        # 4. Test notifications endpoint
        if condition_met:
            response = await client.get(f"/api/v1/tasks/{task_id}/notifications")
            assert response.status_code == 200
            notifications = response.json()
            assert len(notifications) > 0, "Expected notifications but found none"

        # 5. Verify task state tracking
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        updated_task = response.json()

        assert updated_task["last_known_state"] is not None
        if updated_task.get("last_execution"):
            assert updated_task["last_execution"]["condition_met"] == condition_met

    finally:
        # 6. Cleanup
        await client.delete(f"/api/v1/tasks/{task_id}")
