from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from torale.api.rate_limiter import limiter
from torale.api.routers import (
    admin,
    auth,
    email_verification,
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
from torale.api.users import get_async_session
from torale.core.config import settings
from torale.core.database import db


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' https://*.torale.ai; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting Torale API on {settings.api_host}:{settings.api_port}")
    await db.connect()
    print("Database connection pool established")

    # Create test user for TORALE_NOAUTH mode
    if settings.torale_noauth:
        print("⚠️  TORALE_NOAUTH mode enabled - creating test user")
        await db.execute(
            """
            INSERT INTO users (id, clerk_user_id, email, is_active)
            VALUES ('00000000-0000-0000-0000-000000000001', 'test_user_noauth', $1, true)
            ON CONFLICT (clerk_user_id) DO UPDATE SET email = EXCLUDED.email
        """,
            settings.torale_noauth_email,
        )
        print(f"✓ Test user ready ({settings.torale_noauth_email})")

    yield
    await db.disconnect()
    print("Shutting down Torale API")


app = FastAPI(
    title="Torale API",
    description="Platform-agnostic background task manager for AI-powered automation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


# Exception handler to ensure CORS headers are added to all responses, including errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Add CORS headers to HTTP exception responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
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


@app.get("/health")
async def health_check():
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
