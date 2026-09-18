from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Sequence
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .criteria import DEFAULT_RUBRIC_CRITERIA
from .models import Criterion, CriterionScore, ScoringResult

load_dotenv()
logger = logging.getLogger(__name__)


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    key = (
        api_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if not key or key == "YOUR_GOOGLE_API_KEY":
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is not configured. Please set it in your environment or .env file."
        )
    return genai.Client(api_key=key)


def build_scoring_prompt(
    proposal_text: str,
    criteria: Sequence[Criterion],
    rfp_text: Optional[str] = None,
) -> str:
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
You are an experienced sales proposal reviewer and technical bid evaluator.

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


def generate_fallback_scoring(
    proposal_text: str,
    criteria: Sequence[Criterion],
    proposal_name: Optional[str] = None,
    note: str = "",
) -> ScoringResult:
    """Generates a heuristic-based fallback scoring when LLM inference is unreachable."""
    text_lower = proposal_text.lower()
    scores = []

    heuristic_rules = {
        "problem_understanding": {
            "keywords": ["problem", "challenge", "objective", "pain point", "background", "understanding"],
            "high_comment": "Proposal demonstrates solid understanding of business drivers and operational pain points.",
            "low_comment": "Limited context provided regarding the underlying operational and architectural problems.",
        },
        "scope_deliverables": {
            "keywords": ["deliverable", "scope", "phase", "work package", "in-scope", "out-of-scope", "architecture"],
            "high_comment": "Clear demarcation of deliverables, phases, and specific system components.",
            "low_comment": "Deliverables list is general and lacks granular work breakdown details.",
        },
        "pricing_clarity": {
            "keywords": ["pricing", "price", "cost", "fee", "usd", "$", "milestone", "payment", "tco"],
            "high_comment": "Pricing structure is transparently detailed with clear milestone schedules.",
            "low_comment": "Commercials and fee structures lack granular breakdowns or milestone terms.",
        },
        "timeline_clarity": {
            "keywords": ["timeline", "schedule", "milestone", "weeks", "months", "sprint", "deadline", "gantt"],
            "high_comment": "Clear timeline schedule with logical phases, milestones, and go-live checkpoints.",
            "low_comment": "Timeline is vague with broad dates and no critical-path or milestone dependencies.",
        },
        "completeness": {
            "keywords": ["compliance", "requirement", "security", "architecture", "support", "sla", "training"],
            "high_comment": "Covers all major operational, technical, and regulatory requirement areas.",
            "low_comment": "Omissions detected in ancillary requirement coverage, certifications, or SLA commitments.",
        },
        "tone_persuasiveness": {
            "keywords": ["proven", "experience", "track record", "case study", "benefit", "roi", "competitive"],
            "high_comment": "Persuasive, professional tone supported by relevant domain proof points and credibility.",
            "low_comment": "Tone is generic and boilerplate without distinctive value proposition or proof.",
        },
        "risk_transparency": {
            "keywords": ["risk", "assumption", "mitigation", "dependency", "governance", "contingency", "rollback"],
            "high_comment": "Proactive identification of risks, explicit assumptions, and actionable mitigation plans.",
            "low_comment": "Minimal risk disclosure; key dependencies and assumptions are largely unstated.",
        },
    }

    for crit in criteria:
        rule = heuristic_rules.get(crit.id, {"keywords": [], "high_comment": "Adequate alignment.", "low_comment": "Baseline details."})
        matched_kw = sum(1 for kw in rule["keywords"] if kw in text_lower)

        if matched_kw >= 4 and len(text_lower) > 3000:
            score = 4
            comment = rule["high_comment"]
        elif matched_kw >= 2:
            score = 3
            comment = f"{rule['high_comment']} Minor details could be further elaborated."
        else:
            score = 2
            comment = rule["low_comment"]

        scores.append(CriterionScore(
            criterion_id=crit.id,
            criterion_name=crit.name,
            score=score,
            max_score=5,
            comment=comment,
        ))

    summary_note = f"Evaluation completed across 7 dimensions ({len(proposal_text.split())} words analyzed)."
    if note:
        summary_note += f" [{note}]"

    return ScoringResult(
        proposal_name=proposal_name or "Vendor Proposal",
        rubric_scores=scores,
        summary=summary_note,
    )


def evaluate_rubric_score(
    proposal_text: str,
    rfp_text: Optional[str] = None,
    proposal_name: Optional[str] = None,
    criteria: Optional[Sequence[Criterion]] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Score a proposal against the 7 Appendix A Rubric criteria and return a serializable dict."""
    effective_criteria = criteria or DEFAULT_RUBRIC_CRITERIA

    try:
        client = get_gemini_client(api_key=api_key)
        effective_model = (
            model
            or os.getenv("MEDIUM_MODEL")
            or os.getenv("medium_model")
            or os.getenv("LITE_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-2.5-flash"
        )

        prompt = build_scoring_prompt(
            proposal_text=proposal_text,
            criteria=effective_criteria,
            rfp_text=rfp_text,
        )

        response = client.models.generate_content(
            model=effective_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ScoringResult,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        result_obj = ScoringResult.model_validate_json(response.text)
        if proposal_name:
            result_obj.proposal_name = proposal_name

    except Exception as exc:
        logger.warning(f"Rubric Gemini evaluation skipped or failed ({exc}). Falling back to heuristic rubric evaluation.")
        result_obj = generate_fallback_scoring(
            proposal_text=proposal_text,
            criteria=effective_criteria,
            proposal_name=proposal_name,
            note=f"Fallback rubric assessment: {type(exc).__name__}",
        )

    # Convert to standard dict for API response
    result_dict = result_obj.model_dump()
    # Ensure both rubric_scores and scores are populated for maximum client compatibility
    result_dict["scores"] = result_dict.get("rubric_scores", [])

    return result_dict
