"""User model and database operations."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from torale.core.config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    """User model for Clerk-authenticated users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String(length=320), unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# Create async engine for SQLAlchemy
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session():
    """Get async database session."""
    async with async_session_maker() as session:
        yield session


# Pydantic schemas for API
class UserRead(BaseModel):
    """User data returned from API."""

    id: uuid.UUID
    clerk_user_id: str
    email: str
    first_name: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Data required to create a new user."""

    clerk_user_id: str
    email: str
    first_name: str | None = None
