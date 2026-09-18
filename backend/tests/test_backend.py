from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.data.criteria import DEFAULT_CRITERIA
from app.main import app
from app.models.criteria import Criterion
from app.models.scoring import CriterionScore, ScoringResult
from app.services.gemini import build_scoring_prompt, score_proposal
from app.services.proposal_reader import (
    list_available_proposals,
    read_text_file,
    resolve_proposal_path,
)

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == settings.PROJECT_NAME


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_criteria_endpoint():
    response = client.get("/criteria")
    assert response.status_code == 200
    criteria = response.json()
    assert len(criteria) == len(DEFAULT_CRITERIA)
    assert criteria[0]["id"] == "problem_understanding"


def test_proposals_list_endpoint():
    response = client.get("/score/proposals")
    assert response.status_code == 200
    proposals = response.json()
    assert isinstance(proposals, list)
    filenames = [p["filename"] for p in proposals]
    assert "response_1_weak.md" in filenames
    assert "response_3_strong.md" in filenames


def test_resolve_proposal_path():
    path = resolve_proposal_path("response_1_weak.md")
    assert path.exists()
    assert path.name == "response_1_weak.md"

    # Testing extension auto-addition
    path_without_ext = resolve_proposal_path("response_1_weak")
    assert path_without_ext.exists()
    assert path_without_ext.name == "response_1_weak.md"


def test_resolve_proposal_path_traversal_prevention():
    # Attempting path traversal should only look for the basename
    with pytest.raises(FileNotFoundError):
        resolve_proposal_path("../../non_existent_file.md")


def test_scoring_result_computed_properties():
    result = ScoringResult(
        proposal_name="test_proposal.md",
        rubric_scores=[
            CriterionScore(
                criterion_id="problem_understanding",
                criterion_name="Problem Understanding",
                score=4,
                comment="Good understanding shown.",
            ),
            CriterionScore(
                criterion_id="pricing_clarity",
                criterion_name="Pricing Clarity",
                score=2,
                comment="Unclear milestone pricing.",
            ),
        ],
        summary="Mixed proposal.",
    )
    assert result.total_score == 6
    assert result.max_total_score == 10
    assert result.average_score == 3.0


def test_score_non_existent_file_returns_404():
    response = client.get("/score/definitely_not_existing_proposal.md")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_scoring_service_mocked():
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"rubric_scores": [{"criterion_id": "test", "criterion_name": "Test", "score": 5, "max_score": 5, "comment": "Great"}], "summary": "Excellent"}'
    mock_genai_client.models.generate_content.return_value = mock_response

    test_criteria = [
        Criterion(
            id="test",
            name="Test",
            definition="Def",
            anchor_low="Low",
            anchor_high="High",
        )
    ]

    result = score_proposal(
        proposal_text="This is a test proposal text.",
        criteria=test_criteria,
        proposal_name="sample.md",
        client=mock_genai_client,
    )

    assert len(result.rubric_scores) == 1
    assert result.rubric_scores[0].score == 5
    assert result.proposal_name == "sample.md"
    assert result.summary == "Excellent"


def test_post_score_endpoint_mocked():
    with patch("app.api.routes.scoring.evaluate_proposal_text") as mock_score:
        mock_score.return_value = ScoringResult(
            proposal_name="custom_input",
            rubric_scores=[
                CriterionScore(
                    criterion_id="problem_understanding",
                    criterion_name="Problem Understanding",
                    score=4,
                    comment="Well explained",
                )
            ],
            summary="Strong proposal",
        )

        response = client.post(
            "/score",
            json={
                "proposal_text": "We propose building a modern cloud native platform for Nordframe.",
                "proposal_name": "custom_input",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["proposal_name"] == "custom_input"
        assert len(data["rubric_scores"]) == 1
        assert data["rubric_scores"][0]["score"] == 4


def test_criteria_all_english():
    """Verify that all default criteria definitions and anchors are in English."""
    import re
    german_keywords = ["nicht", "gefunden", "sind", "wirkt", "vollständig", "ist", "überzeugend", "offengelegt", "kundenproblem"]
    for c in DEFAULT_CRITERIA:
        text = f"{c.name} {c.definition} {c.anchor_low} {c.anchor_high}".lower()
        for kw in german_keywords:
            assert not re.search(rf"\b{kw}\b", text), f"Found German keyword '{kw}' in criterion '{c.id}'"


def test_scoring_prompt_english():
    """Verify that prompt builder constructs English prompt text."""
    prompt = build_scoring_prompt(
        proposal_text="Sample proposal",
        criteria=DEFAULT_CRITERIA,
        rfp_text="Sample RFP",
    )
    assert "You are an experienced sales proposal reviewer" in prompt
    assert "CRITERIA:" in prompt
    assert "RULES:" in prompt
    assert "RFP / TENDER CONTEXT:" in prompt
    assert "Du bist" not in prompt
    assert "KRITERIEN" not in prompt
