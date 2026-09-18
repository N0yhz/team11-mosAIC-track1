"""API routes package."""

from app.api.routes.criteria import router as criteria_router
from app.api.routes.scoring import router as scoring_router

__all__ = ["criteria_router", "scoring_router"]
