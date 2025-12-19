import json
from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Count, Now

from torale.core.database import Database
from torale.core.models import TaskState
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class TaskRepository(BaseRepository):
    """Repository for task operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.tasks = tables.tasks
        self.users = tables.users
        self.executions = tables.task_executions

    async def create_task(
        self,
        user_id: UUID,
        name: str,
        schedule: str,
        executor_type: str,
        config: dict,
        state: str,
        search_query: str | None,
        condition_description: str | None,
        notify_behavior: str,
        notifications: list[dict],
        notification_channels: list[str],
        notification_email: str | None,
        webhook_url: str | None,
        webhook_secret: str | None,
        extraction_schema: dict | None = None,
    ) -> dict:
        """Create a new task.

        Args:
            user_id: User UUID
            name: Task name
            schedule: Cron expression
            executor_type: Executor type (e.g., "llm_grounded_search")
            config: Task configuration as dict
            state: Task state (active/paused/completed)
            search_query: Search query for grounded search
            condition_description: Condition description
            notify_behavior: Notification behavior (once/always/track_state)
            notifications: List of notification configs
            notification_channels: List of channel types (email/webhook)
            notification_email: Email address for notifications
            webhook_url: Webhook URL
            webhook_secret: Webhook secret
            extraction_schema: Optional extraction schema

        Returns:
            Created task record dict
        """
        data = {
            "user_id": user_id,
            "name": name,
            "schedule": schedule,
            "executor_type": executor_type,
            "config": json.dumps(config),
            "state": state,
            "search_query": search_query,
            "condition_description": condition_description,
            "notify_behavior": notify_behavior,
            "notifications": json.dumps(notifications),
            "notification_channels": notification_channels,
            "notification_email": notification_email,
            "webhook_url": webhook_url,
            "webhook_secret": webhook_secret,
            "extraction_schema": json.dumps(extraction_schema) if extraction_schema else None,
        }

        sql, params = self._build_insert_query(self.tasks, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_user(self, user_id: UUID, state: TaskState | None = None) -> list[dict]:
        """Find all tasks for a user with latest execution embedded.

        Args:
            user_id: User UUID
            state: Optional state filter

        Returns:
            List of task records with embedded execution data
        """
        # Build query with LEFT JOIN for latest execution
        query = PostgreSQLQuery.from_(self.tasks).select(
            self.tasks.star,
            self.users.username.as_("creator_username"),
            self.executions.id.as_("exec_id"),
            self.executions.condition_met.as_("exec_condition_met"),
            self.executions.started_at.as_("exec_started_at"),
            self.executions.completed_at.as_("exec_completed_at"),
            self.executions.status.as_("exec_status"),
            self.executions.result.as_("exec_result"),
            self.executions.change_summary.as_("exec_change_summary"),
            self.executions.grounding_sources.as_("exec_grounding_sources"),
        )

        query = query.join(self.users).on(self.tasks.user_id == self.users.id)
        query = query.left_join(self.executions).on(
            self.tasks.last_execution_id == self.executions.id
        )
        query = query.where(self.tasks.user_id == Parameter("$1"))

        if state:
            query = query.where(self.tasks.state == Parameter("$2"))

        query = query.orderby(self.tasks.created_at, order=Order.desc)

        if state:
            return await self.db.fetch_all(str(query), user_id, state.value)
        return await self.db.fetch_all(str(query), user_id)

    async def find_by_id_with_execution(self, task_id: UUID) -> dict | None:
        """Find task by ID with latest execution embedded.

        Args:
            task_id: Task UUID

        Returns:
            Task record with execution data or None
        """
        query = PostgreSQLQuery.from_(self.tasks).select(
            self.tasks.star,
            self.users.username.as_("creator_username"),
            self.executions.id.as_("exec_id"),
            self.executions.condition_met.as_("exec_condition_met"),
            self.executions.started_at.as_("exec_started_at"),
            self.executions.completed_at.as_("exec_completed_at"),
            self.executions.status.as_("exec_status"),
            self.executions.result.as_("exec_result"),
            self.executions.change_summary.as_("exec_change_summary"),
            self.executions.grounding_sources.as_("exec_grounding_sources"),
        )

        query = query.join(self.users).on(self.tasks.user_id == self.users.id)
        query = query.left_join(self.executions).on(
            self.tasks.last_execution_id == self.executions.id
        )
        query = query.where(self.tasks.id == Parameter("$1"))

        return await self.db.fetch_one(str(query), task_id)

    async def update_task(
        self,
        task_id: UUID,
        name: str | None = None,
        schedule: str | None = None,
        config: dict | None = None,
        state: str | None = None,
        search_query: str | None = None,
        condition_description: str | None = None,
        notify_behavior: str | None = None,
        notification_channels: list[str] | None = None,
        notification_email: str | None = None,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        notifications: list[dict] | None = None,
    ) -> dict:
        """Update task fields.

        Args:
            task_id: Task UUID
            name: New task name
            schedule: New schedule
            config: New config dict
            state: New state
            search_query: New search query
            condition_description: New condition
            notify_behavior: New notify behavior
            notification_channels: New channels
            notification_email: New email
            webhook_url: New webhook URL
            webhook_secret: New webhook secret (None means keep existing)
            notifications: New notifications list

        Returns:
            Updated task record
        """
        data = {}

        if name is not None:
            data["name"] = name
        if schedule is not None:
            data["schedule"] = schedule
        if config is not None:
            data["config"] = json.dumps(config)
        if state is not None:
            data["state"] = state
        if search_query is not None:
            data["search_query"] = search_query
        if condition_description is not None:
            data["condition_description"] = condition_description
        if notify_behavior is not None:
            data["notify_behavior"] = notify_behavior
        if notification_channels is not None:
            data["notification_channels"] = notification_channels
        if notification_email is not None:
            data["notification_email"] = notification_email
        if webhook_url is not None:
            data["webhook_url"] = webhook_url
        if webhook_secret is not None:
            data["webhook_secret"] = webhook_secret
        if notifications is not None:
            data["notifications"] = json.dumps(notifications)

        if not data:
            return await self.find_by_id(self.tasks, task_id)

        sql, params = self._build_update_query(self.tasks, task_id, data)
        return await self.db.fetch_one(sql, *params)

    async def update_last_execution(
        self, task_id: UUID, execution_id: UUID, last_known_state: dict | list | None
    ) -> dict:
        """Update task's last execution reference and state.

        Args:
            task_id: Task UUID
            execution_id: Execution UUID
            last_known_state: New last known state

        Returns:
            Updated task record
        """
        data = {
            "last_execution_id": execution_id,
            "last_known_state": json.dumps(last_known_state) if last_known_state else None,
        }

        sql, params = self._build_update_query(self.tasks, task_id, data)
        return await self.db.fetch_one(sql, *params)

    async def update_state(self, task_id: UUID, state: str) -> dict:
        """Update task state and state_changed_at timestamp.

        Args:
            task_id: Task UUID
            state: New state value

        Returns:
            Updated task record
        """
        query = (
            PostgreSQLQuery.update(self.tasks)
            .set(self.tasks.state, Parameter("$1"))
            .set(self.tasks.state_changed_at, Now())
            .where(self.tasks.id == Parameter("$2"))
            .returning("*")
        )
        return await self.db.fetch_one(str(query), state, task_id)

    async def update_visibility(
        self, task_id: UUID, is_public: bool, slug: str | None = None
    ) -> dict:
        """Update task visibility (public/private).

        Args:
            task_id: Task UUID
            is_public: Whether task should be public
            slug: URL slug (required if making public)

        Returns:
            Updated task record
        """
        data = {"is_public": is_public}
        if slug is not None:
            data["slug"] = slug

        sql, params = self._build_update_query(self.tasks, task_id, data)
        return await self.db.fetch_one(sql, *params)

    async def increment_view_count(self, task_id: UUID) -> None:
        """Increment task view count.

        Args:
            task_id: Task UUID
        """
        query = (
            PostgreSQLQuery.update(self.tasks)
            .set(self.tasks.view_count, self.tasks.view_count + 1)
            .where(self.tasks.id == Parameter("$1"))
        )
        await self.db.execute(str(query), task_id)

    async def increment_subscriber_count(self, task_id: UUID) -> None:
        """Increment task subscriber count (fork count).

        Args:
            task_id: Task UUID
        """
        query = (
            PostgreSQLQuery.update(self.tasks)
            .set(self.tasks.subscriber_count, self.tasks.subscriber_count + 1)
            .where(self.tasks.id == Parameter("$1"))
        )
        await self.db.execute(str(query), task_id)

    async def find_public_tasks(
        self, limit: int = 50, offset: int = 0, search: str | None = None
    ) -> list[dict]:
        """Find public tasks for discovery.

        Args:
            limit: Maximum results
            offset: Pagination offset
            search: Optional search term

        Returns:
            List of public task records
        """
        query = PostgreSQLQuery.from_(self.tasks).select(
            self.tasks.star, self.users.username.as_("creator_username")
        )
        query = query.join(self.users).on(self.tasks.user_id == self.users.id)
        query = query.where(self.tasks.is_public.eq(True))

        if search:
            search_param = f"%{search}%"
            search_condition = (
                (self.tasks.name.like(Parameter("$1")))
                | (self.tasks.search_query.like(Parameter("$1")))
                | (self.tasks.condition_description.like(Parameter("$1")))
            )
            query = query.where(search_condition)

        query = query.orderby(self.tasks.subscriber_count, order=Order.desc)
        query = query.limit(limit).offset(offset)

        if search:
            return await self.db.fetch_all(str(query), search_param)
        return await self.db.fetch_all(str(query))

    async def find_by_slug(self, slug: str) -> dict | None:
        """Find public task by slug.

        Args:
            slug: Task slug

        Returns:
            Task record or None
        """
        query = PostgreSQLQuery.from_(self.tasks).select(
            self.tasks.star, self.users.username.as_("creator_username")
        )
        query = query.join(self.users).on(self.tasks.user_id == self.users.id)
        query = query.where(self.tasks.slug == Parameter("$1"))
        query = query.where(self.tasks.is_public.eq(True))

        return await self.db.fetch_one(str(query), slug)

    async def slug_exists(self, slug: str) -> bool:
        """Check if slug already exists.

        Args:
            slug: Slug to check

        Returns:
            True if slug exists
        """
        query = (
            PostgreSQLQuery.from_(self.tasks)
            .select(Count("*"))
            .where(self.tasks.slug == Parameter("$1"))
        )

        count = await self.db.fetch_val(str(query), slug)
        return count > 0
