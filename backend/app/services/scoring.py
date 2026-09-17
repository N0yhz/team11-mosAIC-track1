from pathlib import Path

from app.data.criteria import DEFAULT_CRITERIA
from app.services.proposal_reader import read_text_file
from app.services.gemini import score_proposal



PROPOSALS_DIR = Path("PATH_TO_PROPOSALS_DIRECTORY")
RFPS_DIR = Path("PATH_TO_RFPS_DIRECTORY")


def evaluate_proposal(
    proposal_filename: str,
) :

    
    proposal_path = PROPOSALS_DIR / proposal_filename

    proposal_text = read_text_file(
        proposal_path
    )

    result = score_proposal(
        proposal_text=proposal_text,
        criteria=DEFAULT_CRITERIA,
    )

    return result