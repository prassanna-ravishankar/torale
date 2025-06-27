from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging

from config import get_settings
from api import discovery

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Set up standard logging
settings = get_settings()
logging.basicConfig(
    format="%(message)s",
    level=getattr(logging, settings.log_level.upper()),
)

logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Discovery Service",
    description="Microservice for discovering monitorable sources from natural language queries",
    version="0.1.0",
)

# Configure CORS
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(discovery.router, prefix="/api/v1", tags=["discovery"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": settings.service_name}


@app.on_event("startup")
async def startup_event():
    logger.info(
        "discovery_service_started",
        port=settings.service_port,
        ai_provider=settings.ai_provider,
        cors_origins=cors_origins
    )


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("discovery_service_shutdown")