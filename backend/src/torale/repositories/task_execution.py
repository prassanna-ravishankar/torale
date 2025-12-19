import json
from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Now

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


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
        condition_met: bool | None = None,
        change_summary: str | None = None,
        grounding_sources: list[dict] | None = None,
    ) -> dict:
        """Update execution record.

        Args:
            execution_id: Execution UUID
            status: New status
            completed_at: Completion timestamp (use "NOW()" for current time)
            result: Result dict
            error_message: Error message
            condition_met: Whether condition was met
            change_summary: Change summary text
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
        if condition_met is not None:
            data["condition_met"] = condition_met
        if change_summary is not None:
            data["change_summary"] = change_summary
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
        """Find executions where condition was met (notifications sent).

        Args:
            task_id: Task UUID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of execution records where condition_met = true
        """
        query = PostgreSQLQuery.from_(self.executions).select("*")
        query = query.where(self.executions.task_id == Parameter("$1"))
        query = query.where(self.executions.condition_met.eq(True))
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

        return await self.db.fetch_one(str(query), task_id, "success")

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
