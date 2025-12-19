import json
from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery
from pypika_tortoise.functions import Now

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class WebhookRepository(BaseRepository):
    """Repository for webhook delivery operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.deliveries = tables.webhook_deliveries

    async def create_delivery(
        self,
        task_id: UUID,
        webhook_url: str,
        payload: dict,
        status: str = "pending",
    ) -> dict:
        """Create a new webhook delivery record.

        Args:
            task_id: Task UUID
            webhook_url: Destination webhook URL
            payload: JSON payload to send
            status: Delivery status (pending/success/failed)

        Returns:
            Created delivery record
        """

        data = {
            "task_id": task_id,
            "webhook_url": webhook_url,
            "payload": json.dumps(payload),
            "status": status,
        }

        sql, params = self._build_insert_query(self.deliveries, data)
        return await self.db.fetch_one(sql, *params)

    async def update_delivery(
        self,
        delivery_id: UUID,
        status: str | None = None,
        response_code: int | None = None,
        response_body: str | None = None,
        error_message: str | None = None,
        delivered_at: str | None = None,
        retry_count: int | None = None,
        next_retry_at: str | None = None,
    ) -> dict:
        """Update webhook delivery record.

        Args:
            delivery_id: Delivery UUID
            status: New status
            response_code: HTTP response code
            response_body: HTTP response body
            error_message: Error message if failed
            delivered_at: Delivery timestamp (use "NOW()" for current time)
            retry_count: Number of retry attempts
            next_retry_at: Next retry timestamp

        Returns:
            Updated delivery record
        """
        data = {}

        if status is not None:
            data["status"] = status
        if response_code is not None:
            data["response_code"] = response_code
        if response_body is not None:
            data["response_body"] = response_body
        if error_message is not None:
            data["error_message"] = error_message
        if retry_count is not None:
            data["retry_count"] = retry_count
        if next_retry_at is not None:
            data["next_retry_at"] = next_retry_at

        if not data and delivered_at is None:
            return await self.find_by_id(self.deliveries, delivery_id)

        # Handle delivered_at - use PyPika's Now() function for "NOW()"
        if delivered_at == "NOW()":
            # Build PyPika UPDATE query with Now() function
            query = PostgreSQLQuery.update(self.deliveries)

            # Add all data fields to SET clause
            param_index = 1
            params = []
            for col, val in data.items():
                query = query.set(getattr(self.deliveries, col), Parameter(f"${param_index}"))
                params.append(val)
                param_index += 1

            # Add delivered_at with Now()
            query = query.set(self.deliveries.delivered_at, Now())

            # WHERE clause
            query = query.where(self.deliveries.id == Parameter(f"${param_index}"))
            params.append(delivery_id)

            # RETURNING clause
            query = query.returning("*")

            return await self.db.fetch_one(str(query), *params)
        elif delivered_at is not None:
            data["delivered_at"] = delivered_at

        sql, params = self._build_update_query(self.deliveries, delivery_id, data)
        return await self.db.fetch_one(sql, *params)

    async def find_pending_retries(self, limit: int = 100) -> list[dict]:
        """Find deliveries pending retry.

        Args:
            limit: Maximum results

        Returns:
            List of delivery records ready for retry
        """
        query = PostgreSQLQuery.from_(self.deliveries).select("*")
        query = query.where(self.deliveries.status == Parameter("$1"))
        query = query.where(self.deliveries.next_retry_at.isnotnull())
        query = query.where(self.deliveries.next_retry_at <= Now())
        query = query.orderby(self.deliveries.next_retry_at, order=Order.asc)
        query = query.limit(Parameter("$2"))

        return await self.db.fetch_all(str(query), "failed", limit)

    async def find_by_task(self, task_id: UUID, limit: int = 50, offset: int = 0) -> list[dict]:
        """Find webhook deliveries for a task.

        Args:
            task_id: Task UUID
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of delivery records
        """
        query = PostgreSQLQuery.from_(self.deliveries).select("*")
        query = query.where(self.deliveries.task_id == Parameter("$1"))
        query = query.orderby(self.deliveries.created_at, order=Order.desc)
        query = query.limit(limit).offset(offset)

        return await self.db.fetch_all(str(query), task_id)
