from fastapi import APIRouter, HTTPException, Query, status

from app.models.requests import EvaluateProposalRequest, ProposalInfo
from app.models.scoring import ScoringResult
from app.services.proposal_reader import list_available_proposals
from app.services.scoring import evaluate_proposal, evaluate_proposal_text

router = APIRouter(
    prefix="/score",
    tags=["Scoring"],
)


@router.get(
    "/proposals",
    response_model=list[ProposalInfo],
    summary="List available proposals",
    description="Retrieve a list of all proposal documents available for scoring.",
)
def get_available_proposals():
    """List all available proposal markdown files."""
    return list_available_proposals()


@router.get(
    "/{proposal_filename}",
    response_model=ScoringResult,
    summary="Score proposal by filename",
    description="Score an existing proposal file against the rubric criteria.",
)
def score_by_filename(
    proposal_filename: str,
    rfp_filename: str | None = Query(
        default=None,
        description="Optional RFP filename to evaluate against",
    ),
):
    """Evaluate an existing proposal file."""
    try:
        return evaluate_proposal(
            proposal_filename=proposal_filename,
            rfp_filename=rfp_filename,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        err_msg = str(exc)
        if "UNAVAILABLE" in err_msg or "high demand" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Gemini API temporarily unavailable: {err_msg}",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring error: {err_msg}",
        ) from exc


@router.post(
    "",
    response_model=ScoringResult,
    status_code=status.HTTP_200_OK,
    summary="Score raw proposal text",
    description="Submit raw proposal text to be evaluated against rubric criteria.",
)
def score_text(payload: EvaluateProposalRequest):
    """Evaluate submitted proposal text against the rubric."""
    try:
        return evaluate_proposal_text(
            proposal_text=payload.proposal_text,
            rfp_text=payload.rfp_text,
            proposal_name=payload.proposal_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring error: {str(exc)}",
        ) from exc