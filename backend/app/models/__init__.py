"""Domain models package."""

from app.models.criteria import Criterion
from app.models.requests import EvaluateProposalRequest, ProposalInfo
from app.models.scoring import CriterionScore, ScoringResult

__all__ = [
    "Criterion",
    "CriterionScore",
    "ScoringResult",
    "EvaluateProposalRequest",
    "ProposalInfo",
]
