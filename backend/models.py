"""Typed API contracts shared by the Level 3 scoring service."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    ADDRESSED = "addressed"
    PARTIAL = "partial"
    MISSING = "missing"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"


class PriorityChange(BaseModel):
    requirement_id: str
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    hard_gate: Optional[bool] = None
    decision: Literal["adjusted", "confirmed"] = "confirmed"


class Level3Request(BaseModel):
    level2_evaluation: Dict[str, Any]
    changes: List[PriorityChange] = Field(default_factory=list)


class Level3Result(BaseModel):
    score: int
    grade: str
    recommendation: str
    readiness: str
    hard_gate_failed: bool
    hard_gate_pending: bool
    deal_breakers: List[Dict[str, Any]]
    hard_gate_clarifications: List[Dict[str, Any]]
    ranked_issues: List[Dict[str, Any]]
    scorecard: List[Dict[str, Any]]