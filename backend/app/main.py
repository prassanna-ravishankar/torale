import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.endpoints import monitoring, notifications, source_discovery, user_queries
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.core.supabase_client import get_supabase_client

# Setup logging first
settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL)
logger = structlog.get_logger(__name__)


class CORSOptionsMiddleware(BaseHTTPMiddleware):
    """Custom middleware to handle CORS requests, especially OPTIONS preflight."""

    def __init__(self, app, cors_origins):
        super().__init__(app)
        self.cors_origins = cors_origins

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # Determine allowed origin
        allowed_origin = None
        if origin and str(origin) in [str(o) for o in self.cors_origins]:
            allowed_origin = origin
        elif self.cors_origins:
            allowed_origin = str(self.cors_origins[0])  # Default to first allowed origin

        if request.method == "OPTIONS":
            # Handle preflight requests immediately - bypass authentication
            headers = {
                "Access-Control-Allow-Origin": allowed_origin or "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",  # Cache preflight for 24 hours
            }
            return Response(status_code=200, headers=headers)

        # Process the actual request
        response = await call_next(request)

        # Add CORS headers to actual responses
        if allowed_origin:
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("torale_api_starting", service_name=settings.PROJECT_NAME)

    # Test Supabase connection
    try:
        supabase = get_supabase_client()
        # Simple test query to verify connection
        result = supabase.table("user_queries").select("count", count="exact").execute()
        logger.info("supabase_connection_successful", query_count=result.count)
    except Exception as e:
        logger.error("supabase_connection_failed", error=str(e))
        # Don't fail startup - let the app start and handle errors per request

    yield

    # Shutdown
    logger.info("torale_api_shutting_down")


app = FastAPI(
    title="Torale API",
    description="A content monitoring and alerting system",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS with custom middleware that handles authentication properly
app.add_middleware(CORSOptionsMiddleware, cors_origins=settings.CORS_ORIGINS or [])

# Include routers
app.include_router(
    monitoring.router,
    prefix=settings.API_V1_STR,
    tags=["monitoring"],
)

app.include_router(
    source_discovery.router,
    prefix=settings.API_V1_STR,
    tags=["source-discovery"],
)

app.include_router(
    user_queries.router,
    prefix=settings.API_V1_STR,
    tags=["user-queries"],
)

app.include_router(
    notifications.router,
    prefix=settings.API_V1_STR + "/notifications",
    tags=["notifications"],
)


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "torale-api"}


@app.get("/supabase-test")
async def test_supabase():
    """Test Supabase connection."""
    try:
        supabase = get_supabase_client()
        result = supabase.table("user_queries").select("count", count="exact").execute()
        return {
            "status": "supabase_connected",
            "test_result": "success",
            "data_count": result.count,
        }
    except Exception as e:
        return {
            "status": "supabase_error",
            "test_result": "failed",
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use our custom logging config
    )
