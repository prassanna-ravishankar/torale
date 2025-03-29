from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts
from app.core.database import init_db

app = FastAPI(
    title="AmbiAlert API",
    description="Natural language-powered alerting service API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


@app.get("/")
async def root():
    return {"message": "Welcome to AmbiAlert API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
