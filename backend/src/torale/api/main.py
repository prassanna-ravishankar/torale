from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from torale.api.routers import admin, auth, email_verification, tasks, templates, waitlist, webhooks
from torale.api.users import get_async_session
from torale.core.config import settings
from torale.core.database import db


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

# Auth routes
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Admin routes
app.include_router(admin.router)

# Waitlist routes
app.include_router(waitlist.router, tags=["waitlist"])

# API routes
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(email_verification.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "torale-api"}


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
