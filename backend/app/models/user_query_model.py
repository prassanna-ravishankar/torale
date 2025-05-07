from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.app.core.db import Base # Assuming Base is defined in core.db

class UserQuery(Base):
    __tablename__ = "user_queries"

    id = Column(Integer, primary_key=True, index=True)
    raw_query = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Potentially add a user_id if you have user accounts
    # user_id = Column(Integer, ForeignKey("users.id")) 