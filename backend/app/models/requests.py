from pydantic import BaseModel, Field


class EvaluateProposalRequest(BaseModel):
    """Payload for submitting a proposal text directly for scoring."""
    proposal_text: str = Field(
        ...,
        description="Raw proposal text or markdown content to be evaluated",
        min_length=10,
    )
    rfp_text: str | None = Field(
        None,
        description="Optional RFP content to contextualize evaluation",
    )
    proposal_name: str | None = Field(
        None,
        description="Optional identifier or title for the proposal",
    )


class ProposalInfo(BaseModel):
    """Metadata about an available proposal document."""
    filename: str = Field(..., description="File name of the proposal")
    title: str = Field(..., description="Display title extracted from filename or content")
    size_bytes: int = Field(..., description="File size in bytes")
