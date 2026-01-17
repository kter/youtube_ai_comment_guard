"""YouTube AI Comment Guard - FastAPI Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from youtube_guard.config import settings
from youtube_guard.routers import comments, scheduler
from youtube_guard.services.firestore_service import FirestoreService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Initialize Firestore on startup
    try:
        app.state.firestore = FirestoreService()
    except Exception as e:
        print(f"Error initializing Firestore: {e}")
        app.state.firestore = None
        
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="YouTube AI Comment Guard",
    description="コメント自動管理・要約システム",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(comments.router, prefix="/api/comments", tags=["Comments"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["Scheduler"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "YouTube AI Comment Guard"}


@app.get("/health")
async def health():
    """Health check for Cloud Run."""
    return {"status": "ok"}
