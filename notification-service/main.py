import asyncio
import logging
import structlog
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

from api.notifications import router as notifications_router, set_services
from config import settings
from services.notification_service import SupabaseNotificationService
from services.notification_processor import NotificationProcessor

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

# Global variables for services
supabase_client: Client = None
notification_service: SupabaseNotificationService = None
notification_processor: NotificationProcessor = None
processor_task: asyncio.Task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting notification service", version="0.1.0")
    
    try:
        # Initialize Supabase client
        global supabase_client, notification_service, notification_processor, processor_task
        
        supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info("Supabase client initialized")
        
        # Initialize notification service
        notification_service = SupabaseNotificationService(
            supabase_client=supabase_client,
            sendgrid_api_key=settings.sendgrid_api_key
        )
        logger.info("Notification service initialized")
        
        # Initialize notification processor
        notification_processor = NotificationProcessor(notification_service)
        logger.info("Notification processor initialized")
        
        # Set services in API router
        set_services(notification_service, notification_processor)
        
        # Start background processor
        processor_task = asyncio.create_task(notification_processor.start())
        logger.info("Background notification processor started")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e), exc_info=True)
        raise
    
    # Shutdown
    logger.info("Shutting down notification service")
    
    try:
        # Stop background processor
        if notification_processor:
            await notification_processor.stop()
            
        # Cancel processor task
        if processor_task and not processor_task.done():
            processor_task.cancel()
            try:
                await processor_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Notification service shutdown complete")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="Torale Notification Service",
    description="Microservice for handling email and push notifications",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "processor_running": notification_processor.is_running if notification_processor else False
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Torale Notification Service",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Configure logging level
    logging.basicConfig(level=getattr(logging, settings.log_level.upper()))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )