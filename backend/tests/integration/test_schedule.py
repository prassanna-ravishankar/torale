import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_schedule_e2e(client: AsyncClient):
    """
    Test automatic task scheduling (Cron).
    Simulates:
    1. Create task with 1-minute schedule
    2. Wait for automatic execution by Temporal
    3. Verify execution success
    4. Test pause/unpause
    5. Cleanup
    """

    # 1. Create task with schedule "every minute"
    task_payload = {
        "name": "Scheduled Test Task (Pytest)",
        "schedule": "* * * * *",
        "search_query": "What is 1+1?",
        "condition_description": "A numerical answer is provided",
        "notify_behavior": "always",
        "is_active": True,
    }

    response = await client.post("/api/v1/tasks", json=task_payload)
    assert response.status_code == 200, f"Create task failed: {response.text}"
    task_data = response.json()
    task_id = task_data["id"]
    assert task_id is not None

    try:
        # 2. Wait for automatic execution (max 90 seconds)
        # Cron is * * * * *, so it should run at the start of the next minute
        found_execution = False
        max_retries = 90

        for _ in range(max_retries):
            await asyncio.sleep(1)

            response = await client.get(f"/api/v1/tasks/{task_id}/executions")
            assert response.status_code == 200
            executions = response.json()

            if len(executions) > 0:
                latest_execution = executions[0]
                status = latest_execution.get("status")

                if status == "success":
                    found_execution = True
                    break
                elif status == "failed":
                    pytest.fail(
                        f"Automatic execution failed: {latest_execution.get('error_message')}"
                    )

        if not found_execution:
            pytest.fail(
                "No automatic execution occurred within 90 seconds. Temporal schedule might not be working."
            )

        # 3. Test pause/unpause
        response = await client.put(f"/api/v1/tasks/{task_id}", json={"is_active": False})
        assert response.status_code == 200
        updated_task = response.json()
        assert updated_task["is_active"] is False, "Failed to pause task"

    finally:
        # 4. Cleanup
        await client.delete(f"/api/v1/tasks/{task_id}")
