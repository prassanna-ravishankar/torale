import json
from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Now

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables
from torale.tasks.tasks import TaskData, TaskState, TaskStatus


class TaskRepository(BaseRepository):
    """Repository for task operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.tasks = tables.tasks
        self.executions = tables.task_executions

    async def create_task(self, data: TaskData) -> dict:
        """Create a new task.

        Args:
            data: Task fields to insert

        Returns:
            Created task record dict
        """
        insert_data = dict(data)
        if "notifications" in insert_data:
            insert_data["notifications"] = json.dumps(insert_data["notifications"])

        sql, params = self._build_insert_query(self.tasks, insert_data)
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
            self.executions.id.as_("exec_id"),
            self.executions.notification.as_("exec_notification"),
            self.executions.started_at.as_("exec_started_at"),
            self.executions.completed_at.as_("exec_completed_at"),
            self.executions.status.as_("exec_status"),
            self.executions.result.as_("exec_result"),
            self.executions.grounding_sources.as_("exec_grounding_sources"),
        )

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
            self.executions.id.as_("exec_id"),
            self.executions.notification.as_("exec_notification"),
            self.executions.started_at.as_("exec_started_at"),
            self.executions.completed_at.as_("exec_completed_at"),
            self.executions.status.as_("exec_status"),
            self.executions.result.as_("exec_result"),
            self.executions.grounding_sources.as_("exec_grounding_sources"),
        )

        query = query.left_join(self.executions).on(
            self.tasks.last_execution_id == self.executions.id
        )
        query = query.where(self.tasks.id == Parameter("$1"))

        return await self.db.fetch_one(str(query), task_id)

    async def update_task(self, task_id: UUID, data: TaskData) -> dict:
        """Update task fields.

        Args:
            task_id: Task UUID
            data: Task fields to update (only provided keys are changed)

        Returns:
            Updated task record
        """
        if not data:
            return await self.find_by_id(self.tasks, task_id)

        update_data = dict(data)
        if "notifications" in update_data:
            update_data["notifications"] = json.dumps(update_data["notifications"])

        sql, params = self._build_update_query(self.tasks, task_id, update_data)
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

    async def update_visibility(self, task_id: UUID, is_public: bool) -> dict:
        """Update task visibility (public/private).

        Args:
            task_id: Task UUID
            is_public: Whether task should be public

        Returns:
            Updated task record
        """
        data = {"is_public": is_public}

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
        query = PostgreSQLQuery.from_(self.tasks).select(self.tasks.star)
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


class TaskExecutionRepository(BaseRepository):
    """Repository for task execution operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.executions = tables.task_executions

    async def create_execution(self, task_id: UUID, status: str = "pending") -> dict:
        """Create a new task execution.

        Args:
            task_id: Task UUID
            status: Initial status (default: pending)

        Returns:
            Created execution record
        """
        data = {
            "task_id": task_id,
            "status": status,
        }

        sql, params = self._build_insert_query(self.executions, data)
        return await self.db.fetch_one(sql, *params)

    async def update_execution(
        self,
        execution_id: UUID,
        status: str | None = None,
        completed_at: str | None = None,
        result: dict | None = None,
        error_message: str | None = None,
        notification: str | None = None,
        grounding_sources: list[dict] | None = None,
    ) -> dict:
        """Update execution record.

        Args:
            execution_id: Execution UUID
            status: New status
            completed_at: Completion timestamp (use "NOW()" for current time)
            result: Result dict
            error_message: Error message
            notification: Notification text (if condition met)
            grounding_sources: List of grounding sources

        Returns:
            Updated execution record
        """
        data = {}

        if status is not None:
            data["status"] = status
        if result is not None:
            data["result"] = json.dumps(result)
        if error_message is not None:
            data["error_message"] = error_message
        if notification is not None:
            data["notification"] = notification
        if grounding_sources is not None:
            data["grounding_sources"] = json.dumps(grounding_sources)

        if not data and completed_at is None:
            return await self.find_by_id(self.executions, execution_id)

        # Handle completed_at - use PyPika's Now() function for "NOW()"
        if completed_at == "NOW()":
            # Build PyPika UPDATE query with Now() function
            query = PostgreSQLQuery.update(self.executions)

            # Add all data fields to SET clause
            param_index = 1
            params = []
            for col, val in data.items():
                query = query.set(getattr(self.executions, col), Parameter(f"${param_index}"))
                params.append(val)
                param_index += 1

            # Add completed_at with Now()
            query = query.set(self.executions.completed_at, Now())

            # WHERE clause
            query = query.where(self.executions.id == Parameter(f"${param_index}"))
            params.append(execution_id)

            # RETURNING clause
            query = query.returning("*")

            return await self.db.fetch_one(str(query), *params)
        elif completed_at is not None:
            data["completed_at"] = completed_at

        sql, params = self._build_update_query(self.executions, execution_id, data)
        return await self.db.fetch_one(sql, *params)

    async def find_by_task(
        self,
        task_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[dict]:
        """Find executions for a task.

        Args:
            task_id: Task UUID
            limit: Maximum results
            offset: Pagination offset
            status: Optional status filter

        Returns:
            List of execution records
        """
        query = PostgreSQLQuery.from_(self.executions).select("*")
        query = query.where(self.executions.task_id == Parameter("$1"))

        param_index = 2
        params = [task_id]

        if status:
            query = query.where(self.executions.status == Parameter(f"${param_index}"))
            params.append(status)
            param_index += 1

        query = query.orderby(self.executions.started_at, order=Order.desc)
        query = query.limit(limit).offset(offset)

        return await self.db.fetch_all(str(query), *params)

    async def find_notifications(
        self, task_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """Find executions where a notification was sent.

        Args:
            task_id: Task UUID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of execution records where notification IS NOT NULL
        """
        query = PostgreSQLQuery.from_(self.executions).select("*")
        query = query.where(self.executions.task_id == Parameter("$1"))
        query = query.where(self.executions.notification.isnotnull())
        query = query.orderby(self.executions.started_at, order=Order.desc)
        query = query.limit(limit).offset(offset)

        return await self.db.fetch_all(str(query), task_id)

    async def get_last_successful(self, task_id: UUID) -> dict | None:
        """Get the last successful execution for a task.

        Args:
            task_id: Task UUID

        Returns:
            Last successful execution record or None
        """
        query = PostgreSQLQuery.from_(self.executions).select("*")
        query = query.where(self.executions.task_id == Parameter("$1"))
        query = query.where(self.executions.status == Parameter("$2"))
        query = query.orderby(self.executions.completed_at, order=Order.desc)
        query = query.limit(1)

        return await self.db.fetch_one(str(query), task_id, TaskStatus.SUCCESS.value)

    async def count_by_task(self, task_id: UUID, status: str | None = None) -> int:
        """Count executions for a task.

        Args:
            task_id: Task UUID
            status: Optional status filter

        Returns:
            Count of executions
        """
        conditions = [self.executions.task_id == Parameter("$1")]
        params = [task_id]

        if status:
            conditions.append(self.executions.status == Parameter("$2"))
            params.append(status)

        count = await self.count(self.executions, conditions, params=params)
        return count
