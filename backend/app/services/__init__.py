"""Services package."""

from app.services.gemini import get_gemini_client, score_proposal
from app.services.proposal_reader import (
    list_available_proposals,
    read_text_file,
    resolve_proposal_path,
)
from app.services.scoring import (
    evaluate_proposal,
    evaluate_proposal_text,
    load_rfp_text,
)

__all__ = [
    "get_gemini_client",
    "score_proposal",
    "list_available_proposals",
    "read_text_file",
    "resolve_proposal_path",
    "evaluate_proposal",
    "evaluate_proposal_text",
    "load_rfp_text",
]
