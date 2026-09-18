from pydantic import BaseModel, Field


class Criterion(BaseModel):
    """Rubric criterion used for proposal evaluation."""
    id: str = Field(..., description="Unique identifier for the criterion")
    name: str = Field(..., description="Display name of the criterion")
    definition: str = Field(..., description="Description/definition of what is being evaluated")
    anchor_low: str = Field(..., description="Description of poor performance (score = 1)")
    anchor_high: str = Field(..., description="Description of excellent performance (score = 5)")