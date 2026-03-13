"""User Pydantic models for API."""

import uuid
from datetime import datetime

from pydantic import BaseModel


# Pydantic schemas for API
class UserRead(BaseModel):
    """User data returned from API."""

    id: uuid.UUID
    clerk_user_id: str
    email: str
    first_name: str | None = None
    username: str | None = None
    is_active: bool
    has_seen_welcome: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """Data required to create a new user."""

    clerk_user_id: str
    email: str
    first_name: str | None = None
