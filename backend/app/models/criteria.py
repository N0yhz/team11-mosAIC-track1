from pydantic import BaseModel, Field


class Criterion(BaseModel):
    id: str
    name: str
    definition: str
    anchor_low: str
    anchor_high: str