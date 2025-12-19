from typing import Any
from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery, Table

from torale.core.database import Database


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, db: Database):
        """Initialize repository with database connection.

        Args:
            db: Database instance from dependency injection
        """
        self.db = db

    async def find_by_id(self, table: Table, record_id: UUID) -> dict | None:
        """Find a record by ID.

        Args:
            table: PyPika table instance
            record_id: Record UUID

        Returns:
            Record dict or None if not found
        """
        query = PostgreSQLQuery.from_(table).select("*").where(table.id == Parameter("$1"))
        return await self.db.fetch_one(str(query), record_id)

    async def find_all(
        self,
        table: Table,
        where_conditions: list[Any] | None = None,
        params: list[Any] | None = None,
        order_by: tuple[Any, Order] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict]:
        """Find all records matching conditions.

        Args:
            table: PyPika table instance
            where_conditions: List of WHERE conditions
            params: List of parameters for the WHERE conditions
            order_by: Tuple of (field, Order) for sorting
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of record dicts
        """
        query = PostgreSQLQuery.from_(table).select("*")

        if where_conditions:
            for condition in where_conditions:
                query = query.where(condition)

        if order_by:
            field, order = order_by
            query = query.orderby(field, order=order)

        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        return await self.db.fetch_all(str(query), *(params or []))

    async def count(
        self, table: Table, where_conditions: list[Any] | None = None, params: list[Any] | None = None
    ) -> int:
        """Count records matching conditions.

        Args:
            table: PyPika table instance
            where_conditions: List of WHERE conditions
            params: List of parameters for the WHERE conditions

        Returns:
            Count of matching records
        """
        query = PostgreSQLQuery.from_(table).select("COUNT(*)")

        if where_conditions:
            for condition in where_conditions:
                query = query.where(condition)

        return await self.db.fetch_val(str(query), *(params or [])) or 0

    async def delete_by_id(self, table: Table, record_id: UUID) -> str:
        """Delete a record by ID.

        Args:
            table: PyPika table instance
            record_id: Record UUID

        Returns:
            SQL execution result
        """
        query = PostgreSQLQuery.from_(table).delete().where(table.id == Parameter("$1"))
        return await self.db.execute(str(query), record_id)

    def _build_insert_query(
        self, table: Table, data: dict, returning: bool = True
    ) -> tuple[str, list]:
        """Build INSERT query from data dict.

        Args:
            table: PyPika table instance
            data: Dict of column: value pairs
            returning: Whether to include RETURNING *

        Returns:
            Tuple of (SQL string, parameters list)
        """
        columns = list(data.keys())
        params = list(data.values())

        # Build parameter placeholders ($1, $2, etc.)
        param_placeholders = [Parameter(f"${i + 1}") for i in range(len(params))]

        query = PostgreSQLQuery.into(table).columns(*columns).insert(*param_placeholders)

        if returning:
            query = query.returning("*")

        return str(query), params

    def _build_update_query(
        self, table: Table, record_id: UUID, data: dict, returning: bool = True
    ) -> tuple[str, list]:
        """Build UPDATE query from data dict.

        Args:
            table: PyPika table instance
            record_id: Record UUID to update
            data: Dict of column: value pairs
            returning: Whether to include RETURNING *

        Returns:
            Tuple of (SQL string, parameters list)
        """
        query = PostgreSQLQuery.update(table)

        params = []
        for i, (column, value) in enumerate(data.items(), start=1):
            query = query.set(column, Parameter(f"${i}"))
            params.append(value)

        # ID is the last parameter
        params.append(record_id)
        query = query.where(table.id == Parameter(f"${len(params)}"))

        if returning:
            query = query.returning("*")

        return str(query), params
