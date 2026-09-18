from typing import Sequence
from google import genai
from google.genai import types

from app.core.config import settings
from app.data.criteria import DEFAULT_CRITERIA
from app.models.criteria import Criterion
from app.models.scoring import ScoringResult


def get_gemini_client() -> genai.Client:
    """Initialize and return the Google GenAI client.
    
    Raises ValueError if GOOGLE_API_KEY is missing or contains placeholder.
    """
    api_key = settings.GOOGLE_API_KEY
    if not api_key or api_key == "YOUR_GOOGLE_API_KEY":
        raise ValueError(
            "GOOGLE_API_KEY is not configured. Please set GOOGLE_API_KEY or GEMINI_API_KEY in your environment or .env file."
        )
    return genai.Client(api_key=api_key)


def build_scoring_prompt(
    proposal_text: str,
    criteria: Sequence[Criterion],
    rfp_text: str | None = None,
) -> str:
    """Construct structured evaluation prompt for the Gemini model."""
    criteria_block = "\n\n".join(
        f"""
ID: {criterion.id}
Name: {criterion.name}
Definition: {criterion.definition}
1 = {criterion.anchor_low}
5 = {criterion.anchor_high}
""".strip()
        for criterion in criteria
    )

    rfp_section = ""
    if rfp_text:
        rfp_section = f"""
RFP / TENDER CONTEXT:
{rfp_text.strip()}

"""

    return f"""
You are an experienced sales proposal reviewer.

Evaluate the following proposal based on the criteria on a scale from 1 to 5.
{rfp_section}
CRITERIA:

{criteria_block}

RULES:
1. Evaluate each criterion exactly once.
2. Use the exact specified criterion_id values.
3. Use the exact specified criterion_name values.
4. The score must be an integer between 1 and 5.
5. max_score is always 5.
6. Every comment must refer concretely to the proposal and provide clear rationale.
7. Do not invent facts or make unsubstantiated assumptions.
8. Provide a concise summary of overall strengths and weaknesses in the 'summary' field.
9. Return exclusively the defined JSON format.

PROPOSAL:

{proposal_text.strip()}
""".strip()


def score_proposal(
    proposal_text: str,
    criteria: Sequence[Criterion] | None = None,
    rfp_text: str | None = None,
    proposal_name: str | None = None,
    model: str | None = None,
    client: genai.Client | None = None,
) -> ScoringResult:
    """Score a proposal using Google Gemini and return a validated ScoringResult."""
    if criteria is None:
        criteria = DEFAULT_CRITERIA

    if client is None:
        client = get_gemini_client()

    selected_model = model or settings.GEMINI_MODEL
    prompt = build_scoring_prompt(proposal_text=proposal_text, criteria=criteria, rfp_text=rfp_text)

    response = client.models.generate_content(
        model=selected_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ScoringResult,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    result = ScoringResult.model_validate_json(response.text)
    if proposal_name:
        result.proposal_name = proposal_name
    return result