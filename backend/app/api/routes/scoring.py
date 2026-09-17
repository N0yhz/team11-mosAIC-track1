from fastapi import APIRouter, HTTPException

from app.services.scoring import evaluate_proposal


router = APIRouter(
    prefix="/score",
    tags=["Scoring"],
)


@router.get("/{proposal_filename}")
def score(proposal_filename: str):

    try:
        result = evaluate_proposal(
            proposal_filename
        )

        return result.model_dump()

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )