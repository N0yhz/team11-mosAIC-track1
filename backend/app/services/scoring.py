from pathlib import Path
from typing import Sequence

from app.core.config import settings
from app.data.criteria import DEFAULT_CRITERIA
from app.models.criteria import Criterion
from app.models.scoring import ScoringResult
from app.services.gemini import score_proposal
from app.services.proposal_reader import read_text_file, resolve_proposal_path


def load_rfp_text(rfp_filename: str | None = None) -> str | None:
    """Attempt to load RFP text if a filename is given or if a default RFP is present."""
    rfp_dir = settings.RFPS_DIR
    if not rfp_dir.exists():
        fallback_dir = settings.PROJECT_ROOT / "rfp"
        if fallback_dir.exists():
            rfp_dir = fallback_dir

    if rfp_filename:
        rfp_path = rfp_dir / rfp_filename
        if rfp_path.exists():
            return read_text_file(rfp_path)

    # Check for default RFP file if none specified
    default_rfp = rfp_dir / "rfp_nordframe.md"
    if default_rfp.exists():
        return read_text_file(default_rfp)

    return None


def evaluate_proposal(
    proposal_filename: str,
    rfp_filename: str | None = None,
    criteria: Sequence[Criterion] | None = None,
) -> ScoringResult:
    """Evaluate an existing proposal file by filename against the rubric."""
    proposal_path = resolve_proposal_path(proposal_filename)
    proposal_text = read_text_file(proposal_path)
    rfp_text = load_rfp_text(rfp_filename)

    return score_proposal(
        proposal_text=proposal_text,
        criteria=criteria or DEFAULT_CRITERIA,
        rfp_text=rfp_text,
        proposal_name=proposal_path.name,
    )


def evaluate_proposal_text(
    proposal_text: str,
    rfp_text: str | None = None,
    proposal_name: str | None = None,
    criteria: Sequence[Criterion] | None = None,
) -> ScoringResult:
    """Evaluate raw proposal text against the rubric."""
    if rfp_text is None:
        rfp_text = load_rfp_text()

    return score_proposal(
        proposal_text=proposal_text,
        criteria=criteria or DEFAULT_CRITERIA,
        rfp_text=rfp_text,
        proposal_name=proposal_name,
    )