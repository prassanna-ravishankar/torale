from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


# Base schema with common fields
class UserQueryBase(BaseModel):
    raw_query: str = Field(
        ..., min_length=1, description="The raw query submitted by the user"
    )
    config_hints_json: Optional[Dict[str, Any]] = Field(
        None, description="Optional configuration hints for the query processing"
    )


# Schema for creating a new user query (input)
class UserQueryCreate(UserQueryBase):
    pass


# Schema for reading a user query from the DB (output)
class UserQueryInDB(UserQueryBase):
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2 style

    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    # Remove Pydantic v1 style Config class
    # class Config:
    #     orm_mode = True # Compatibility with SQLAlchemy models
