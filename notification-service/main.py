import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from api.notifications import router as notifications_router, set_service
from config import settings
from services.notification_service import NotificationApiService
from clients.notificationapi_client import NotificationApiHttpClient

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
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    logger.info("Starting notification service", version="0.2.0")
    
    try:
        notificationapi_client = NotificationApiHttpClient()
        notification_service = NotificationApiService(notificationapi_client=notificationapi_client)
        set_service(notification_service)
        logger.info("NotificationAPI client and service initialized.")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e), exc_info=True)
        raise
    
    logger.info("Shutting down notification service.")

# Create FastAPI application
app = FastAPI(
    title="Torale Notification Service",
    description="Microservice for handling notifications via NotificationAPI.",
    version="0.2.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(notifications_router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper()))
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )