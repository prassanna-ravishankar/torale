import logging
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import discovery
from config import get_settings

# Configure structured logging for production
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Configure standard logging
settings = get_settings()
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=settings.LOG_LEVEL.upper(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    cors_origins = (
        [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
        if settings.CORS_ORIGINS
        else []
    )
    logger.info(
        "discovery_service_started",
        port=settings.SERVICE_PORT,
        ai_provider=settings.AI_PROVIDER,
        cors_origins=cors_origins,
    )
    yield
    logger.info("discovery_service_shutdown")


# Create FastAPI app
app = FastAPI(
    title="Discovery Service",
    description="Microservice for discovering monitorable sources from natural language queries",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = (
    [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
    if settings.CORS_ORIGINS
    else []
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(discovery.router, prefix="/api/v1", tags=["discovery"])


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Discovery Service",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "discovery-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.SERVICE_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
