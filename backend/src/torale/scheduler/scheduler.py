import logging

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from torale.core.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _make_job_store_url() -> str:
    """Convert async database URL to sync for APScheduler 3.x SQLAlchemy job store."""
    url = settings.database_url
    # APScheduler 3.x uses sync SQLAlchemy, needs postgresql+psycopg2://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_scheduler() -> AsyncIOScheduler:
    """Get the singleton scheduler instance."""
    global _scheduler
    if _scheduler is None:
        jobstore_url = _make_job_store_url()
        _scheduler = AsyncIOScheduler(
            jobstores={
                "default": SQLAlchemyJobStore(url=jobstore_url),
            },
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 3600,
            },
        )
    return _scheduler
