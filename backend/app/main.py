from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import (
    monitoring,
    source_discovery,
    user_queries,
)  # Corrected import

# from app.api import alerts # Old router, to be replaced
# from app.core.database import init_db # Old DB init, to be replaced
from app.core.config import get_settings  # Import get_settings instead of settings
from app.core.logging_config import setup_logging  # Corrected import

app = FastAPI(
    title=get_settings().PROJECT_NAME,  # Use get_settings() here
    version="0.2.0",  # Updated version for next-gen
    description=(
        "Next-generation alerting service API with AI-powered source discovery "
        "and change detection."
    ),
)

# Setup logging before including routers or defining startup events
# that might log, ensures logs from startup are captured correctly.
sys_settings = get_settings()  # Call get_settings() here
setup_logging(log_level=sys_settings.LOG_LEVEL)

# Configure CORS
if sys_settings.CORS_ORIGINS:  # Use the instance
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in sys_settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create database tables on startup (for development; use Alembic for production)
# @app.on_event("startup")
# async def on_startup(): # Make the function asynchronous
#     # This creates tables if they don\'t exist.
#     # For production, Alembic migrations are preferred.
#     logging.info("Creating database tables if they don\'t exist...")
#     async with engine.begin() as conn: # Use async context manager for engine
#         await conn.run_sync(Base.metadata.create_all) # Use run_sync for create_all
#     logging.info("Database tables checked/created.")
# await init_db() # Replaced old init_db

# Include new routers
app.include_router(
    source_discovery.router, prefix=sys_settings.API_V1_STR, tags=["Source Discovery"]
)  # Use the instance
app.include_router(
    monitoring.router, prefix=sys_settings.API_V1_STR, tags=["Monitoring & Alerts"]
)  # Use the instance
app.include_router(
    user_queries.router,
    prefix=f"{sys_settings.API_V1_STR}/user-queries",
    tags=["User Queries"],
)  # Add new router
# app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"]) # Old router


@app.get("/")
async def root():
    return {"message": f"Welcome to {sys_settings.PROJECT_NAME} API v0.2.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}