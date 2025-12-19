from uuid import UUID

from pypika_tortoise import Order, Parameter, PostgreSQLQuery

from torale.core.database import Database
from torale.repositories.base import BaseRepository
from torale.repositories.tables import tables


class TaskTemplateRepository(BaseRepository):
    """Repository for task template operations."""

    def __init__(self, db: Database):
        super().__init__(db)
        self.templates = tables.task_templates

    async def find_all_active(self) -> list[dict]:
        """Find all active task templates.

        Returns:
            List of active template records
        """
        query = PostgreSQLQuery.from_(self.templates).select("*")
        query = query.where(self.templates.is_active.eq(True))
        query = query.orderby(self.templates.display_order, order=Order.asc)

        return await self.db.fetch_all(str(query))

    async def find_by_slug(self, slug: str) -> dict | None:
        """Find template by slug.

        Args:
            slug: Template slug

        Returns:
            Template record or None
        """
        query = PostgreSQLQuery.from_(self.templates).select("*")
        query = query.where(self.templates.slug == Parameter("$1"))
        query = query.where(self.templates.is_active.eq(True))

        return await self.db.fetch_one(str(query), slug)

    async def increment_usage_count(self, template_id: UUID) -> None:
        """Increment template usage count.

        Args:
            template_id: Template UUID
        """
        query = (
            PostgreSQLQuery.update(self.templates)
            .set(self.templates.usage_count, self.templates.usage_count + 1)
            .where(self.templates.id == Parameter("$1"))
        )
        await self.db.execute(str(query), template_id)
