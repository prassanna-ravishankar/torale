from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from torale.api.routers import admin, auth, tasks, templates
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
        await db.execute("""
            INSERT INTO users (id, clerk_user_id, email, is_active)
            VALUES ('00000000-0000-0000-0000-000000000001', 'test_user_noauth', 'test@example.com', true)
            ON CONFLICT (clerk_user_id) DO NOTHING
        """)
        print("✓ Test user ready (test@example.com)")

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

# API routes
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "torale-api"}
