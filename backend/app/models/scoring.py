from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    """Score and feedback for a single evaluation criterion."""
    criterion_id: str = Field(..., description="Unique criterion ID matching the rubric")
    criterion_name: str = Field(..., description="Name of the criterion")
    score: int = Field(..., ge=1, le=5, description="Evaluation score between 1 and 5")
    max_score: int = Field(default=5, description="Maximum possible score (default 5)")
    comment: str = Field(..., description="Specific feedback and evidence-based rationale")


class ScoringResult(BaseModel):
    """Aggregate evaluation result for a proposal."""
    proposal_name: str | None = Field(default=None, description="Optional proposal filename or identifier")
    rubric_scores: list[CriterionScore] = Field(..., description="List of criterion evaluations")
    summary: str | None = Field(default=None, description="Brief summary of overall strengths and weaknesses")

    @property
    def total_score(self) -> int:
        return sum(item.score for item in self.rubric_scores)

    @property
    def max_total_score(self) -> int:
        return sum(item.max_score for item in self.rubric_scores)

    @property
    def average_score(self) -> float:
        if not self.rubric_scores:
            return 0.0
        return round(self.total_score / len(self.rubric_scores), 2)