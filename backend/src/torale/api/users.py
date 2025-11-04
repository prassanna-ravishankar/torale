"""User model and database operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, EmailStr

from torale.core.config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    """User model for Clerk-authenticated users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String(length=320), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Create async engine for SQLAlchemy
engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
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
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Data required to create a new user."""

    clerk_user_id: str
    email: EmailStr
