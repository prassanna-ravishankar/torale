"""User model and database operations."""

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from torale.core.database_alchemy import Base


class User(Base):
    """User model for Clerk-authenticated users."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String(length=320), unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    username = Column(String(30), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


# Pydantic schemas for API
class UserRead(BaseModel):
    """User data returned from API."""

    id: uuid.UUID
    clerk_user_id: str
    email: str
    first_name: str | None = None
    username: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Data required to create a new user."""

    clerk_user_id: str
    email: str
    first_name: str | None = None
