"""Tasks resource for Torale SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from torale.core.models import NotificationConfig, NotifyBehavior, Task, TaskExecution

if TYPE_CHECKING:
    from torale.sdk.client import ToraleClient


class TasksResource:
    """Resource for managing tasks."""

    def __init__(self, client: ToraleClient):
        self.client = client

    def create(
        self,
        name: str,
        search_query: str,
        condition_description: str,
        schedule: str = "0 9 * * *",
        notify_behavior: str | NotifyBehavior = NotifyBehavior.ONCE,
        notifications: list[dict | NotificationConfig] | None = None,
        config: dict | None = None,
        is_active: bool = True,
    ) -> Task:
        """
        Create a new monitoring task.

        Args:
            name: Task name
            search_query: Query to monitor (e.g., "When is iPhone 16 being released?")
            condition_description: Condition to trigger on (e.g., "A specific date is announced")
            schedule: Cron expression for task schedule (default: "0 9 * * *" = 9am daily)
            notify_behavior: When to notify ("once", "always", or "track_state")
            notifications: List of notification configs
            config: Executor configuration (default: {"model": "gemini-2.0-flash-exp"})
            is_active: Whether task is active

        Returns:
            Created Task object

        Example:
            >>> task = client.tasks.create(
            ...     name="iPhone Monitor",
            ...     search_query="When is iPhone 16 being released?",
            ...     condition_description="A specific release date is announced",
            ...     notifications=[
            ...         {"type": "webhook", "url": "https://myapp.com/alert"}
            ...     ]
            ... )
        """
        # Convert notify_behavior to string if enum
        if isinstance(notify_behavior, NotifyBehavior):
            notify_behavior = notify_behavior.value

        # Convert NotificationConfig objects to dicts
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
            "config": config or {"model": "gemini-2.0-flash-exp"},
            "is_active": is_active,
            "executor_type": "llm_grounded_search",
        }

        response = self.client.post("/api/v1/tasks", json=data)
        return Task(**response)

    def list(self, active: bool | None = None) -> list[Task]:
        """
        List tasks.

        Args:
            active: Filter by active status (None = all tasks)

        Returns:
            List of Task objects

        Example:
            >>> tasks = client.tasks.list(active=True)
            >>> for task in tasks:
            ...     print(task.name)
        """
        params = {}
        if active is not None:
            params["is_active"] = active

        response = self.client.get("/api/v1/tasks", params=params)
        return [Task(**task_data) for task_data in response]

    def get(self, task_id: str | UUID) -> Task:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task object

        Example:
            >>> task = client.tasks.get("550e8400-e29b-41d4-a716-446655440000")
            >>> print(task.name)
        """
        response = self.client.get(f"/api/v1/tasks/{task_id}")
        return Task(**response)

    def update(
        self,
        task_id: str | UUID,
        name: str | None = None,
        search_query: str | None = None,
        condition_description: str | None = None,
        schedule: str | None = None,
        notify_behavior: str | NotifyBehavior | None = None,
        notifications: list[dict | NotificationConfig] | None = None,
        config: dict | None = None,
        is_active: bool | None = None,
    ) -> Task:
        """
        Update task.

        Args:
            task_id: Task ID
            name: New task name
            search_query: New search query
            condition_description: New condition description
            schedule: New schedule
            notify_behavior: New notify behavior
            notifications: New notification configs
            config: New config
            is_active: New active status

        Returns:
            Updated Task object

        Example:
            >>> task = client.tasks.update(
            ...     task_id="550e8400-e29b-41d4-a716-446655440000",
            ...     is_active=False
            ... )
        """
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
        if config is not None:
            data["config"] = config
        if is_active is not None:
            data["is_active"] = is_active

        response = self.client.put(f"/api/v1/tasks/{task_id}", json=data)
        return Task(**response)

    def delete(self, task_id: str | UUID) -> None:
        """
        Delete task.

        Args:
            task_id: Task ID

        Example:
            >>> client.tasks.delete("550e8400-e29b-41d4-a716-446655440000")
        """
        self.client.delete(f"/api/v1/tasks/{task_id}")

    def execute(self, task_id: str | UUID) -> TaskExecution:
        """
        Manually execute task (test run).

        Args:
            task_id: Task ID

        Returns:
            TaskExecution object

        Example:
            >>> execution = client.tasks.execute("550e8400-e29b-41d4-a716-446655440000")
            >>> print(execution.status)
        """
        response = self.client.post(f"/api/v1/tasks/{task_id}/execute")
        return TaskExecution(**response)

    def executions(self, task_id: str | UUID, limit: int = 100) -> list[TaskExecution]:
        """
        Get task execution history.

        Args:
            task_id: Task ID
            limit: Maximum number of executions to return

        Returns:
            List of TaskExecution objects

        Example:
            >>> executions = client.tasks.executions("550e8400-e29b-41d4-a716-446655440000")
            >>> for execution in executions:
            ...     print(f"{execution.started_at}: {execution.status}")
        """
        response = self.client.get(f"/api/v1/tasks/{task_id}/executions", params={"limit": limit})
        return [TaskExecution(**exec_data) for exec_data in response]

    def notifications(self, task_id: str | UUID, limit: int = 100) -> list[TaskExecution]:
        """
        Get task notifications (executions where condition was met).

        Args:
            task_id: Task ID
            limit: Maximum number of notifications to return

        Returns:
            List of TaskExecution objects where condition_met=True

        Example:
            >>> notifications = client.tasks.notifications("550e8400-e29b-41d4-a716-446655440000")
            >>> for notif in notifications:
            ...     print(f"{notif.started_at}: {notif.change_summary}")
        """
        response = self.client.get(
            f"/api/v1/tasks/{task_id}/notifications", params={"limit": limit}
        )
        return [TaskExecution(**exec_data) for exec_data in response]
