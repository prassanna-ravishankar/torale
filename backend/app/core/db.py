from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

sys_settings = get_settings()
SQLALCHEMY_DATABASE_URL = sys_settings.DATABASE_URL

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    # Add any async specific engine args here if needed, e.g., echo=True for debugging
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session


# Old synchronous engine and session maker
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL,
#     # connect_args={"check_same_thread": False} # Only for SQLite, if used
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
