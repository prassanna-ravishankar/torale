from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from torale.api.routers import tasks, auth
from torale.core.config import settings
from torale.core.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting Torale API on {settings.api_host}:{settings.api_port}")
    await db.connect()
    print("Database connection pool established")
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

# API routes
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "torale-api"}