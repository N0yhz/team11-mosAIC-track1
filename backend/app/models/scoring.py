from pydantic import BaseModel, Field


class CriterionScore(BaseModel):
    criterion_id: str
    criterion_name: str
    score: int = Field(ge=1, le=5)
    max_score: int = 5
    comment: str


class ScoringResult(BaseModel):
    rubric_scores: list[CriterionScore]