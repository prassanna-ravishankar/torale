"""SQLAlchemy database configuration and session management."""


from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from torale.core.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


# Create async engine for SQLAlchemy
# Convert postgresql:// to postgresql+asyncpg:// for async support
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    """
    Get async database session.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with async_session_maker() as session:
        yield session
