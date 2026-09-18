from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class Criterion(BaseModel):
    """Rubric criterion used for proposal quality evaluation."""
    id: str = Field(..., description="Unique identifier for the criterion")
    name: str = Field(..., description="Display name of the criterion")
    definition: str = Field(..., description="Description/definition of what is being evaluated")
    anchor_low: str = Field(..., description="Description of poor performance (score = 1)")
    anchor_high: str = Field(..., description="Description of excellent performance (score = 5)")


class CriterionScore(BaseModel):
    """Score and feedback for a single evaluation criterion."""
    criterion_id: str = Field(..., description="Unique criterion ID matching the rubric")
    criterion_name: str = Field(..., description="Name of the criterion")
    score: int = Field(..., ge=1, le=5, description="Evaluation score between 1 and 5")
    max_score: int = Field(default=5, description="Maximum possible score (default 5)")
    comment: str = Field(..., description="Specific feedback and evidence-based rationale")


class ScoringResult(BaseModel):
    """Aggregate evaluation result for a proposal."""
    proposal_name: Optional[str] = Field(default=None, description="Optional proposal filename or identifier")
    rubric_scores: List[CriterionScore] = Field(..., description="List of criterion evaluations")
    summary: Optional[str] = Field(default=None, description="Brief summary of overall strengths and weaknesses")

    @computed_field
    @property
    def total_score(self) -> int:
        return sum(item.score for item in self.rubric_scores)

    @computed_field
    @property
    def max_total_score(self) -> int:
        return sum(item.max_score for item in self.rubric_scores)

    @computed_field
    @property
    def average_score(self) -> float:
        if not self.rubric_scores:
            return 0.0
        return round(self.total_score / len(self.rubric_scores), 2)

    @computed_field
    @property
    def percentage(self) -> float:
        if not self.max_total_score:
            return 0.0
        return round((self.total_score / self.max_total_score) * 100, 1)
