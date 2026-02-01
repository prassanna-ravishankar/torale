"""Async tasks resource for Torale SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from torale.tasks import NotificationConfig, NotifyBehavior, Task, TaskExecution, TaskState

if TYPE_CHECKING:
    from torale.sdk.async_client import ToraleAsyncClient


class AsyncTasksResource:
    """Async resource for managing tasks."""

    def __init__(self, client: ToraleAsyncClient):
        self.client = client

    async def create(
        self,
        name: str,
        search_query: str,
        condition_description: str,
        schedule: str = "0 9 * * *",
        notify_behavior: str | NotifyBehavior = NotifyBehavior.ONCE,
        notifications: list[dict | NotificationConfig] | None = None,
        state: str | TaskState = TaskState.ACTIVE,
    ) -> Task:
        """
        Create a new monitoring task (async).

        Args:
            name: Task name
            search_query: Query to monitor
            condition_description: Condition to trigger on
            schedule: Cron expression
            notify_behavior: When to notify
            notifications: List of notification configs
            state: Task state ("active" or "paused")

        Returns:
            Created Task object

        Example:
            >>> async with ToraleAsync() as client:
            ...     task = await client.tasks.create(
            ...         name="iPhone Monitor",
            ...         search_query="When is iPhone 16 being released?",
            ...         condition_description="A specific release date is announced"
            ...     )
        """
        if isinstance(notify_behavior, NotifyBehavior):
            notify_behavior = notify_behavior.value

        if isinstance(state, TaskState):
            state = state.value

        if notifications:
            notifications = [
                n.model_dump() if isinstance(n, NotificationConfig) else n for n in notifications
            ]

        data = {
            "name": name,
            "search_query": search_query,
            "condition_description": condition_description,
            "schedule": schedule,
            "notify_behavior": notify_behavior,
            "notifications": notifications or [],
            "state": state,
        }

        response = await self.client.post("/api/v1/tasks/", json=data)
        return Task(**response)

    async def list(self, active: bool | None = None) -> list[Task]:
        """
        List tasks (async).

        Args:
            active: Filter by active status

        Returns:
            List of Task objects
        """
        params = {}
        if active is not None:
            params["state"] = TaskState.ACTIVE.value if active else TaskState.PAUSED.value

        response = await self.client.get("/api/v1/tasks/", params=params)
        return [Task(**task_data) for task_data in response]

    async def get(self, task_id: str | UUID) -> Task:
        """Get task by ID (async)."""
        response = await self.client.get(f"/api/v1/tasks/{task_id}")
        return Task(**response)

    async def update(
        self,
        task_id: str | UUID,
        name: str | None = None,
        search_query: str | None = None,
        condition_description: str | None = None,
        schedule: str | None = None,
        notify_behavior: str | NotifyBehavior | None = None,
        notifications: list[dict | NotificationConfig] | None = None,
        state: str | TaskState | None = None,
    ) -> Task:
        """Update task (async)."""
        data = {}

        if name is not None:
            data["name"] = name
        if search_query is not None:
            data["search_query"] = search_query
        if condition_description is not None:
            data["condition_description"] = condition_description
        if schedule is not None:
            data["schedule"] = schedule
        if notify_behavior is not None:
            if isinstance(notify_behavior, NotifyBehavior):
                notify_behavior = notify_behavior.value
            data["notify_behavior"] = notify_behavior
        if notifications is not None:
            notifications = [
                n.model_dump() if isinstance(n, NotificationConfig) else n for n in notifications
            ]
            data["notifications"] = notifications
        if state is not None:
            if isinstance(state, TaskState):
                state = state.value
            data["state"] = state

        response = await self.client.put(f"/api/v1/tasks/{task_id}", json=data)
        return Task(**response)

    async def delete(self, task_id: str | UUID) -> None:
        """Delete task (async)."""
        await self.client.delete(f"/api/v1/tasks/{task_id}")

    async def execute(self, task_id: str | UUID) -> TaskExecution:
        """Manually execute task (async)."""
        response = await self.client.post(f"/api/v1/tasks/{task_id}/execute")
        return TaskExecution(**response)

    async def executions(self, task_id: str | UUID, limit: int = 100) -> list[TaskExecution]:
        """Get task execution history (async)."""
        response = await self.client.get(
            f"/api/v1/tasks/{task_id}/executions", params={"limit": limit}
        )
        return [TaskExecution(**exec_data) for exec_data in response]

    async def notifications(self, task_id: str | UUID, limit: int = 100) -> list[TaskExecution]:
        """Get task notifications (async)."""
        response = await self.client.get(
            f"/api/v1/tasks/{task_id}/notifications", params={"limit": limit}
        )
        return [TaskExecution(**exec_data) for exec_data in response]
