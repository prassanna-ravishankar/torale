"""Fluent API builders for Torale SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from torale.core.models import NotifyBehavior, Task

if TYPE_CHECKING:
    from torale.sdk import Torale


class MonitorBuilder:
    """
    Fluent builder for creating monitoring tasks with beautiful chaining syntax.

    Example:
        >>> from torale import monitor
        >>> task = (monitor("iPhone 16 release date")
        ...     .when("specific date is announced")
        ...     .check_every("6 hours")
        ...     .notify(email="me@example.com", webhook="https://myapp.com/alert")
        ...     .create())
    """

    def __init__(self, client: Torale, search_query: str):
        self.client = client
        self._search_query = search_query
        self._condition_description: str | None = None
        self._schedule: str = "0 9 * * *"  # Default: 9am daily
        self._notify_behavior: NotifyBehavior = NotifyBehavior.ONCE
        self._notifications: list[dict] = []
        self._name: str | None = None
        self._config: dict = {"model": "gemini-2.0-flash-exp"}
        self._is_active: bool = True

    def when(self, condition_description: str) -> MonitorBuilder:
        """
        Specify the condition that triggers notifications.

        Args:
            condition_description: Human-readable condition description

        Returns:
            Self for chaining

        Example:
            >>> monitor("Bitcoin price").when("price exceeds $50,000")
        """
        self._condition_description = condition_description
        return self

    def check_every(self, schedule: str) -> MonitorBuilder:
        """
        Set how often to check the condition.

        Args:
            schedule: Cron expression or human-readable schedule.
                Supports:
                - Cron: "0 9 * * *" (9am daily)
                - Human: "5 minutes", "1 hour", "6 hours", "1 day"

        Returns:
            Self for chaining

        Example:
            >>> monitor("PS5 stock").when("in stock").check_every("5 minutes")
            >>> monitor("News").when("new article").check_every("0 */6 * * *")  # Every 6 hours
        """
        # Convert human-readable to cron if needed
        if "minute" in schedule.lower():
            minutes = schedule.split()[0]
            self._schedule = f"*/{minutes} * * * *"
        elif "hour" in schedule.lower():
            hours = schedule.split()[0]
            self._schedule = f"0 */{hours} * * *"
        elif "day" in schedule.lower():
            self._schedule = "0 9 * * *"  # 9am daily
        else:
            # Assume it's already a cron expression
            self._schedule = schedule

        return self

    def notify(
        self,
        email: str | None = None,
        webhook: str | None = None,
        behavior: str | NotifyBehavior = NotifyBehavior.ONCE,
        **kwargs,
    ) -> MonitorBuilder:
        """
        Configure notifications.

        Args:
            email: Email address to notify
            webhook: Webhook URL to call
            behavior: When to notify ("once", "always", or "track_state")
            **kwargs: Additional notification configuration

        Returns:
            Self for chaining

        Example:
            >>> (monitor("iPhone 16")
            ...     .when("released")
            ...     .notify(email="me@example.com", webhook="https://myapp.com/hook"))
            >>> (monitor("Bitcoin")
            ...     .when("price > 50k")
            ...     .notify(webhook="https://api.myapp.com/crypto", behavior="always"))
        """
        # Set notify behavior
        if isinstance(behavior, str):
            self._notify_behavior = NotifyBehavior(behavior)
        else:
            self._notify_behavior = behavior

        # Add email notification
        if email:
            self._notifications.append(
                {
                    "type": "email",
                    "address": email,
                    **{k: v for k, v in kwargs.items() if k.startswith("email_")},
                }
            )

        # Add webhook notification
        if webhook:
            self._notifications.append(
                {
                    "type": "webhook",
                    "url": webhook,
                    "method": kwargs.get("webhook_method", "POST"),
                    "headers": kwargs.get("webhook_headers"),
                }
            )

        return self

    def named(self, name: str) -> MonitorBuilder:
        """
        Set a custom name for the task.

        Args:
            name: Task name

        Returns:
            Self for chaining

        Example:
            >>> monitor("iPhone 16").when("released").named("iPhone Launch Monitor")
        """
        self._name = name
        return self

    def with_config(self, **config) -> MonitorBuilder:
        """
        Set custom executor configuration.

        Args:
            **config: Configuration options (e.g., model="gemini-2.5-flash")

        Returns:
            Self for chaining

        Example:
            >>> monitor("Query").when("condition").with_config(model="gemini-2.5-flash")
        """
        self._config.update(config)
        return self

    def paused(self) -> MonitorBuilder:
        """
        Create task in paused state (not active).

        Returns:
            Self for chaining

        Example:
            >>> monitor("Query").when("condition").paused().create()
        """
        self._is_active = False
        return self

    def create(self) -> Task:
        """
        Create the monitoring task.

        Returns:
            Created Task object

        Raises:
            ValueError: If required fields are missing

        Example:
            >>> task = monitor("Query").when("condition").notify(email="me@email.com").create()
        """
        if not self._condition_description:
            raise ValueError("Condition description is required. Use .when() to specify it.")

        # Generate name if not provided
        name = self._name or f"Monitor: {self._search_query[:50]}"

        # Create task using client
        return self.client.tasks.create(
            name=name,
            search_query=self._search_query,
            condition_description=self._condition_description,
            schedule=self._schedule,
            notify_behavior=self._notify_behavior,
            notifications=self._notifications,
            config=self._config,
            is_active=self._is_active,
        )


def monitor(search_query: str, client: Torale | None = None) -> MonitorBuilder:
    """
    Create a monitoring task with fluent API.

    Args:
        search_query: Query to monitor
        client: Torale client (optional, will create default if not provided)

    Returns:
        MonitorBuilder for chaining

    Example:
        >>> from torale import monitor
        >>> task = (monitor("When is iPhone 16 being released?")
        ...     .when("A specific date is announced")
        ...     .check_every("6 hours")
        ...     .notify(email="me@example.com")
        ...     .create())
    """
    if client is None:
        # Import here to avoid circular dependency
        from torale.sdk import Torale

        client = Torale()

    return MonitorBuilder(client, search_query)
