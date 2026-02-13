import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from torale.access import (
    NoAuthProvider,
    ProductionAuthProvider,
    set_auth_provider,
)
from torale.api.rate_limiter import limiter
from torale.api.routers import (
    admin,
    auth,
    email_verification,
    integrations,
    notifications,
    og,
    public_tasks,
    sitemap,
    tasks,
    templates,
    usernames,
    waitlist,
    webhooks,
)
from torale.core.config import PROJECT_ROOT, settings
from torale.core.database import db
from torale.core.database_alchemy import get_async_session
from torale.lib.posthog import shutdown as shutdown_posthog
from torale.scheduler import get_scheduler
from torale.scheduler.jobs.webhook_retry import execute_webhook_retry_job
from torale.scheduler.migrate import reap_stale_executions, sync_jobs_from_database

logger = logging.getLogger(__name__)

_startup_sync_ok = False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Modern security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # CSP - frame-ancestors replaces X-Frame-Options, CSP replaces X-XSS-Protection
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' https://*.torale.ai; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Torale API on {settings.api_host}:{settings.api_port}")
    await db.connect()
    logger.info("Database connection pool established")

    # Initialize Auth Provider
    if settings.torale_noauth:
        logger.info("⚠️  TORALE_NOAUTH mode enabled - using NoAuthProvider")
        provider = NoAuthProvider()
        set_auth_provider(provider)
        await provider.setup(db)
    else:
        logger.info("🔒 Using ProductionAuthProvider (Clerk + API Keys)")
        set_auth_provider(ProductionAuthProvider())

    # Start scheduler
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("APScheduler started")

    global _startup_sync_ok
    try:
        await sync_jobs_from_database()
        _startup_sync_ok = True
        logger.info("Scheduler jobs synced from database")
    except Exception as e:
        logger.error(f"Failed to sync scheduler jobs from database: {e}", exc_info=True)

    # Register stale execution reaper (runs every 15 minutes)
    scheduler.add_job(
        reap_stale_executions,
        trigger="interval",
        minutes=15,
        id="reap-stale-executions",
        replace_existing=True,
    )

    # Register webhook retry job (runs every 5 minutes)
    scheduler.add_job(
        execute_webhook_retry_job,
        trigger="interval",
        minutes=5,
        id="webhook-retry-job",
        replace_existing=True,
    )
    logger.info("Webhook retry job registered")

    yield

    scheduler.shutdown(wait=False)
    logger.info("APScheduler shut down")
    shutdown_posthog()
    logger.info("PostHog shut down")
    await db.disconnect()
    logger.info("Shutting down Torale API")


app = FastAPI(
    title="Torale API",
    description="Platform-agnostic background task manager for AI-powered automation",
    version="0.1.0",
    lifespan=lifespan,
)

_CORS_ORIGINS = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add SlowAPI rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return structured JSON for HTTP exceptions. CORS headers are handled by CORSMiddleware."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Auth routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Admin routes
app.include_router(admin.router)

# Waitlist routes
app.include_router(waitlist.router, tags=["waitlist"])

# SEO routes (at root level for standard locations)
app.include_router(sitemap.router)

# API routes
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(email_verification.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(usernames.router, prefix="/api/v1")
app.include_router(public_tasks.router, prefix="/api/v1")
app.include_router(og.router, prefix="/api/v1")
app.include_router(integrations.router, prefix="/api/v1")

# Serve changelog.json as static file
app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT / "static")), name="static")


@app.get("/health")
async def health_check():
    scheduler = get_scheduler()
    scheduler_running = scheduler.running
    if not scheduler_running or not _startup_sync_ok:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "scheduler_running": scheduler_running,
                "startup_sync_ok": _startup_sync_ok,
            },
        )
    return {"status": "healthy"}


@app.get("/public/stats")
async def get_public_stats(session: AsyncSession = Depends(get_async_session)):
    """
    Public endpoint for landing page stats.
    Returns available user capacity for beta signup messaging.
    """
    # Count active users
    user_result = await session.execute(
        text("""
        SELECT COUNT(*) as total_users
        FROM users
        WHERE is_active = true
        """)
    )
    user_row = user_result.first()
    total_users = user_row[0] if user_row else 0

    # Get max users from settings
    max_users = settings.max_users
    available_slots = max(0, max_users - total_users)

    return {
        "capacity": {
            "max_users": max_users,
            "current_users": total_users,
            "available_slots": available_slots,
        }
    }
