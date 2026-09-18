from pathlib import Path
import sys

# Ensure backend directory is present in sys.path for robust imports
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.criteria import router as criteria_router
from app.api.routes.scoring import router as scoring_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent API for evaluating and scoring sales proposals against RFP criteria.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(scoring_router)
app.include_router(criteria_router)


@app.get(
    "/",
    tags=["General"],
    summary="Root service information",
)
def root():
    """Service landing endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
)
def health():
    """Health check endpoint for liveness probes."""
    return {"status": "ok"}