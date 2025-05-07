from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from app.api import alerts # Old router, to be replaced
# from app.core.database import init_db # Old DB init, to be replaced

from backend.app.core.config import settings # Corrected import path
from backend.app.core.db import Base, engine # For table creation
from backend.app.api.endpoints import source_discovery, monitoring # New routers

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.2.0", # Updated version for next-gen
    description="Next-generation alerting service API with AI-powered source discovery and change detection."
)

# Configure CORS
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create database tables on startup (for development; use Alembic for production)
@app.on_event("startup")
def on_startup():
    # This creates tables if they don't exist. 
    # For production, Alembic migrations are preferred.
    Base.metadata.create_all(bind=engine)
    # await init_db() # Replaced old init_db

# Include new routers
app.include_router(source_discovery.router, prefix=settings.API_V1_STR, tags=["Source Discovery"])
app.include_router(monitoring.router, prefix=settings.API_V1_STR, tags=["Monitoring & Alerts"])
# app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"]) # Removed old alerts router

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API v0.2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
