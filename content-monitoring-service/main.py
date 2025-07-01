import logging
import sys
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.monitoring import router as monitoring_router
from config import get_settings

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
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
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
    level=getattr(logging, getattr(settings, 'LOG_LEVEL', 'INFO').upper()),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("content_monitoring_service_starting", version=settings.VERSION)
    yield
    logger.info("content_monitoring_service_shutting_down")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Content monitoring microservice for scraping, change detection, and alert generation",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "unhandled_exception",
        exc_info=True,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"},
    )


# Include routers
app.include_router(
    monitoring_router,
    prefix="/api/v1",
    tags=["monitoring"],
)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "endpoints": {
            "health": "/api/v1/health",
            "process_source": "/api/v1/process-source/{source_id}",
            "process_batch": "/api/v1/process-batch",
            "source_status": "/api/v1/sources/{source_id}/status",
            "queue_status": "/api/v1/queue/status"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG,
        log_level="info",
    )