from fastapi import APIRouter

from app.data.criteria import DEFAULT_CRITERIA
from app.models.criteria import Criterion

router = APIRouter(
    prefix="/criteria",
    tags=["Criteria"],
)


@router.get(
    "",
    response_model=list[Criterion],
    summary="List evaluation criteria",
    description="Retrieve all rubric criteria used to evaluate proposals.",
)
def get_criteria():
    """Return the default evaluation criteria rubric."""
    return DEFAULT_CRITERIA
