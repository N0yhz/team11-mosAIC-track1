"""
Level 2 Feedback & Correction Evaluator
----------------------------------------
Evaluates a vendor response/proposal against criteria from a JSON file,
using the Google Gemini API (via google-generativeai or google-genai).

Outputs:
- response_feedback_<response_name>.json: Detailed structured feedback, strengths, weaknesses, and scorecard.
- response_correction_<response_name>.json: Actionable recommendations and fully corrected proposal data.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Suppress minor deprecation / warning notices
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables from .env
from dotenv import load_dotenv

load_dotenv()


# =====================================================================
# =====================================================================
# Prompt Template for Structured JSON Feedback & Correction
# =====================================================================
EVALUATION_PROMPT_TEMPLATE = """
You are an expert Senior Procurement Specialist, Bid Evaluator, and Technical Proposal Reviewer.
You have been tasked with evaluating a vendor's proposal/response against a formal set of customer requirements and criteria.

### EVALUATION CRITERIA (CONFIGURED BY CUSTOMER/EVALUATOR):
```json
{criteria_json}
```

### VENDOR'S SUBMITTED RESPONSE / PROPOSAL:
```markdown
{response_markdown}
```

---

### CRITICAL INSTRUCTIONS ON REQUIREMENTS AND PRIORITIES:
1. Treat each requirement `description`, `rationale`, and source quote as immutable customer text. Priority changes are metadata only and must never change the requirement's meaning.
2. Evaluate factual coverage using only the original requirement text and its source quote. Return one normalized status per criterion: `addressed`, `partial`, `missing`, `contradicted`, or `unverifiable`.
3. Priority 5 is not automatically a hard gate. Only a criterion with `hard_gate: true` is a disqualifying gatekeeper.
4. In your Task A Scorecard, reflect the assigned priority level. Echo the criteria' hard-gate value only as `source_hard_gate`; do not create or override hard-gate policy.
5. Treat Level 2 grade and recommendation as descriptive context only; the canonical weighted decision is calculated later by Level 3.
6. In your Task B corrected proposal, provide suggested wording and fixes only. Do not invent vendor capabilities, guarantees, SLAs, prices, or timelines. Every proposed revision requires vendor confirmation.
7. Do not reduce compliance because of details that the RFP does not explicitly require. If additional technical detail would be useful but is not required, put it under `suggested_clarifications` rather than using it as a reason for `partial`, `missing`, or `contradicted`.
8. For every scorecard row, include grounded evidence from both documents when available. If the proposal contains no relevant statement for a requirement, use status `missing` and an empty proposal evidence quote. Use `unverifiable` only when the proposal makes a relevant claim but provides insufficient information to verify it. Never invent evidence.
9. A criterion may contain multiple explicit checks or sub-requirements. A criterion is `addressed` only when every mandatory check is explicitly covered. Use `partial` when at least one mandatory check is covered and another is missing, vague, or deferred. Use `missing` when none is mentioned. Do not infer omitted checks from a generic feature name.
10. STATUS DEFINITIONS: `addressed` means all explicit mandatory checks are clearly satisfied; `partial` means at least one is satisfied but another explicit check is missing, vague, or deferred; `missing` means no relevant proposal statement exists; `contradicted` means the proposal explicitly conflicts with the RFP; `unverifiable` means the proposal makes a relevant claim but the wording is too ambiguous or unsupported to verify.
11. A proposal promising delivery earlier than an "within N months" deadline does not contradict the deadline. Evaluate whether the required milestone, scope, and feasibility are sufficiently described.
12. Do not infer compliance with a prohibition from silence. For constraints such as "no database migration", require an explicit proposal statement confirming no migration or replacement. Existing PostgreSQL integration alone is `partial` or `unverifiable` for the no-migration check.

---

### YOUR TASKS:

#### Task A (Feedback & Evaluation):
1. Evaluate the vendor's response against each criterion in the criteria list.
2. Highlight specific **Strengths** of the proposal (what was addressed well, if anything).
3. Highlight specific **Weaknesses and Critical Gaps** (which must-have or high-priority criteria were missing, vague, deferred, or inadequate).
4. Provide a structured criteria-by-criteria scorecard with: criterion_id, requirement_title, priority_level, status, source_hard_gate, rfp_evidence, proposal_evidence, matched_checks, missing_checks, check_results, suggested_clarifications, and evaluation_notes.
5. Provide an overall Compliance Grade (A, B, C, D, or F) and bid recommendation (Accept, Shortlist with Clarifications, or Reject).

#### Task B (Correction & Actionable Improvements):
1. Provide a concrete list of **Actionable Recommendations** for improving the proposal to win the bid, specifically addressing all missing or partially compliant criteria.
2. Highlight the **Key Improvements Made** compared to the original proposal.
3. Provide suggested revisions for all relevant criteria, giving top priority to Score 5 and Score 4 requirements. Do not present suggestions as approved vendor commitments.

---

### OUTPUT FORMAT:
You MUST return your response strictly as a single valid, well-formed JSON object matching this schema:
{{
  "feedback": {{
    "response_file": "{response_file_name}",
    "vendor_name": "string - Name of the vendor who submitted the proposal",
    "compliance_grade": "string - e.g. C+, B-, or D",
    "bid_recommendation": "string - e.g. Shortlist with Clarifications / Reject / Accept",
    "executive_summary": "string - Overall evaluation summary of the proposal reflecting user criteria priorities",
    "strengths": [
      "string - Specific strength 1",
      "string - Specific strength 2"
    ],
    "weaknesses_and_gaps": [
      "string - Specific weakness/gap 1",
      "string - Specific weakness/gap 2"
    ],
    "scorecard": [
      {{
        "criterion_id": "REQ-01",
        "requirement_title": "string",
        "priority_level": "string",
        "status": "addressed | partial | missing | contradicted | unverifiable",
        "source_hard_gate": false,
                "matched_checks": ["Explicit check covered by the proposal"],
                "missing_checks": ["Explicit check not covered or not verifiable"],
                "check_results": [
                    {{"check_id": "REQ-01.1", "status": "addressed", "evidence_quote": "verbatim proposal quote"}}
                ],
                "rfp_evidence": {{
                    "section": "string",
                    "quote": "verbatim RFP quote or empty string"
                }},
                "proposal_evidence": {{
                    "section": "string",
                    "quote": "verbatim proposal quote or empty string"
                }},
                "suggested_clarifications": ["string"],
        "evaluation_notes": "string"
      }}
    ]
  }},
  "correction": {{
    "response_file": "{response_file_name}",
    "vendor_name": "string",
    "actionable_recommendations": [
      "string - Recommendation 1",
      "string - Recommendation 2"
    ],
    "key_improvements_made": [
      "string - Improvement 1",
      "string - Improvement 2"
    ],
        "corrected_proposal": {{
            "title": "Draft Proposal Revisions",
            "requirements_revisions": [
                {{
                    "criterion_id": "REQ-01",
                    "deficiency_resolved": "string",
                    "suggested_revision": "string - Draft wording requiring vendor confirmation",
                    "requires_vendor_confirmation": true,
                    "confirmation_fields": ["string"]
                }}
            ]
        }}
  }}
}}

Do NOT output any markdown ticks outside the JSON or commentary. Only return valid JSON.
"""


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    """Validate and retrieve Gemini API key from parameter or environment."""
    key = explicit_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or key.strip() == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing!\n"
            "Please ensure GEMINI_API_KEY is configured in your .env file.\n"
            "Get an API key at: https://aistudio.google.com/app/apikey"
        )
    return key.strip()


def _call_gemini_api(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """
    Call Gemini API supporting both `google-generativeai` and `google-genai`.
    """
    # 1. Try google-genai (current official SDK)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        target_model = (
            model_name
            or os.getenv("STRONG_MODEL")
            or os.getenv("strong_model")
            or os.getenv("MEDIUM_MODEL")
            or os.getenv("medium_model")
            or os.getenv("GEMINI_MODEL")
            or "gemini-3.8-flash"
        )

        candidate_fallbacks = [
            target_model,
            os.getenv("STRONG_MODEL"),
            os.getenv("strong_model"),
            "gemini-3.8-flash",
            "gemini-3.1-pro-preview",
            os.getenv("MEDIUM_MODEL"),
            os.getenv("medium_model"),
            "gemini-3.6-flash",
            os.getenv("LITE_MODEL"),
            os.getenv("lite_model"),
            "gemini-3.5-flash-lite",
        ]
        seen = set()
        models_to_try = [m for m in candidate_fallbacks if m and not (m in seen or seen.add(m))]

        last_error = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                        max_output_tokens=8192,
                    ),
                )
                if response.text:
                    return response.text
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error

    except ImportError:
        pass

    # 2. Try google-generativeai (legacy SDK)
    try:
        legacy_genai = importlib.import_module("google.generativeai")

        legacy_genai.configure(api_key=api_key)
        target_model = model_name or os.getenv("STRONG_MODEL") or os.getenv("strong_model") or os.getenv("MEDIUM_MODEL") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
        model = legacy_genai.GenerativeModel(
            model_name=target_model,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "max_output_tokens": 8192,
            },
        )
        response = model.generate_content(prompt)
        return response.text

    except ImportError:
        raise ImportError(
            "Neither 'google-genai' nor 'google-generativeai' is installed.\n"
            "Please install the Google Gemini SDK via: pip install google-genai"
        )


def _parse_gemini_json_output(raw_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Parse and validate Gemini's canonical feedback/correction wrapper."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise ValueError(
            "Gemini returned invalid or truncated JSON. "
            f"JSON error: {err}. Response preview: {cleaned[:500]}"
        ) from err

    if not isinstance(data, dict):
        raise ValueError(
            f"Gemini output must be a JSON object, got {type(data).__name__}."
        )

    feedback_data = data.get("feedback") or data.get("response_feedback") or data.get("Task A")
    correction_data = data.get("correction") or data.get("response_correction") or data.get("Task B")

    if feedback_data is None and isinstance(data.get("scorecard"), list):
        feedback_data = data
        correction_data = {}

    if isinstance(feedback_data, str):
        try:
            feedback_data = json.loads(feedback_data)
        except json.JSONDecodeError as err:
            raise ValueError("Gemini returned feedback as an invalid JSON string.") from err

    if isinstance(correction_data, str):
        try:
            correction_data = json.loads(correction_data)
        except json.JSONDecodeError as err:
            raise ValueError("Gemini returned correction as an invalid JSON string.") from err

    if not isinstance(feedback_data, dict):
        raise ValueError("Gemini output does not contain a valid 'feedback' object.")

    scorecard = feedback_data.get("scorecard")
    if not isinstance(scorecard, list) or not scorecard:
        raise ValueError("Gemini feedback does not contain a non-empty 'scorecard' array.")

    if correction_data is None:
        correction_data = {}
    if not isinstance(correction_data, dict):
        raise ValueError("Gemini output contains an invalid 'correction' object.")

    return feedback_data, correction_data


def lvl2_feedback_response(
    criteria_file: str,
    response_file: str,
    feedback_output_path: Optional[str] = None,
    correction_output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Evaluate a text response against criteria using Google Gemini API and export JSON files.

    :param criteria_file: Path to JSON file (e.g. criterias_output.json) with criteria.
    :param response_file: Path to Markdown file (e.g. response/response_2_medium.md) to evaluate.
    :param feedback_output_path: Path for feedback JSON file (default: response_feedback_<response_name>.json).
    :param correction_output_path: Path for correction JSON file (default: response_correction_<response_name>.json).
    :param api_key: Gemini API Key (optional, defaults to GEMINI_API_KEY in .env).
    :param model_name: Gemini model override (optional, defaults to GEMINI_MODEL in .env).
    :return: Tuple containing (feedback_dict, correction_dict).
    """
    # -----------------------------------------------------------------
    # 1. Error Handling & Input Validation
    # -----------------------------------------------------------------
    crit_path = Path(criteria_file)
    if not crit_path.exists():
        raise FileNotFoundError(f"Criteria file not found: {crit_path.resolve()}")
    if not crit_path.is_file():
        raise ValueError(f"Criteria path is not a file: {crit_path.resolve()}")

    resp_path = Path(response_file)
    if not resp_path.exists():
        raise FileNotFoundError(f"Response file not found: {resp_path.resolve()}")
    if not resp_path.is_file():
        raise ValueError(f"Response path is not a file: {resp_path.resolve()}")

    # Determine output JSON file paths suffixed with the response file name
    resp_stem = resp_path.stem  # e.g., 'response_2_medium'
    actual_feedback_path = feedback_output_path or f"response_feedback_{resp_stem}.json"
    actual_correction_path = correction_output_path or f"response_correction_{resp_stem}.json"

    # Ensure output paths end with .json
    if not actual_feedback_path.endswith(".json"):
        actual_feedback_path = f"{os.path.splitext(actual_feedback_path)[0]}.json"
    if not actual_correction_path.endswith(".json"):
        actual_correction_path = f"{os.path.splitext(actual_correction_path)[0]}.json"

    # -----------------------------------------------------------------
    # 2. Read and Parse Input Files
    # -----------------------------------------------------------------
    try:
        with open(crit_path, "r", encoding="utf-8") as f:
            criteria_raw = f.read().strip()
            criteria_data = json.loads(criteria_raw)
            criteria_json_str = json.dumps(criteria_data, indent=2, ensure_ascii=False)
    except json.JSONDecodeError as err:
        raise ValueError(f"Invalid JSON format in criteria file '{crit_path}': {err}")
    except Exception as err:
        raise IOError(f"Failed to read criteria file '{crit_path}': {err}")

    try:
        with open(resp_path, "r", encoding="utf-8") as f:
            response_text = f.read().strip()
    except Exception as err:
        raise IOError(f"Failed to read response file '{resp_path}': {err}")

    if not response_text:
        raise ValueError(f"Response file '{resp_path}' is empty.")

    # -----------------------------------------------------------------
    # 3. Resolve API Key & Query Gemini
    # -----------------------------------------------------------------
    effective_api_key = _get_api_key(api_key)

    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        criteria_json=criteria_json_str,
        response_markdown=response_text,
        response_file_name=resp_path.name
    )

    print(f"[AI] Evaluating '{resp_path.name}' against criteria in '{crit_path.name}'...")
    raw_api_output = _call_gemini_api(prompt, api_key=effective_api_key, model_name=model_name)
    print(f"[Gemini] Raw response length: {len(raw_api_output)} characters")
    print(f"[Gemini] Response ending: {raw_api_output[-500:]}")

    # -----------------------------------------------------------------
    # 4. Extract Structured JSON Output
    # -----------------------------------------------------------------
    feedback_data, correction_data = _parse_gemini_json_output(raw_api_output)

    criteria_items = criteria_data.get("criteria", [])
    scorecard_items = feedback_data.get("scorecard", [])
    criteria_ids = {
        str(item.get("id", "")).strip().upper()
        for item in criteria_items
    }
    scorecard_ids = {
        str(item.get("criterion_id", "")).strip().upper()
        for item in scorecard_items
    }
    missing_ids = criteria_ids - scorecard_ids
    unknown_ids = scorecard_ids - criteria_ids
    if missing_ids:
        raise ValueError(
            f"Gemini scorecard is missing criteria: {sorted(missing_ids)}"
        )
    if unknown_ids:
        raise ValueError(
            f"Gemini scorecard contains unknown criteria: {sorted(unknown_ids)}"
        )

    # Ensure source metadata is present
    if isinstance(feedback_data, dict) and "response_file" not in feedback_data:
        feedback_data["response_file"] = resp_path.name
    if isinstance(correction_data, dict) and "response_file" not in correction_data:
        correction_data["response_file"] = resp_path.name

    # -----------------------------------------------------------------
    # 5. Save Output JSON Files
    # -----------------------------------------------------------------
    fb_target = Path(actual_feedback_path)
    fb_target.parent.mkdir(parents=True, exist_ok=True)
    with open(fb_target, "w", encoding="utf-8") as f:
        json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    print(f"[Export JSON] Saved feedback to: {fb_target.resolve()}")

    corr_target = Path(actual_correction_path)
    corr_target.parent.mkdir(parents=True, exist_ok=True)
    with open(corr_target, "w", encoding="utf-8") as f:
        json.dump(correction_data, f, indent=2, ensure_ascii=False)
    print(f"[Export JSON] Saved correction to: {corr_target.resolve()}")

    return feedback_data, correction_data


# =====================================================================
# CLI Entrypoint
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate a vendor response against criteria and export JSON files."
    )
    default_criteria = "criterias_output.json"
    default_response = "response/response_2_medium.md"

    parser.add_argument(
        "response_file",
        nargs="?",
        default=default_response,
        help=f"Path to response markdown file (default: {default_response})",
    )
    parser.add_argument(
        "--criteria-file",
        "-cr",
        default=default_criteria,
        help=f"Path to criteria JSON file (default: {default_criteria})",
    )
    parser.add_argument(
        "--feedback-out",
        "-f",
        default=None,
        help="Path to save feedback JSON file (default: response_feedback_<response_name>.json)",
    )
    parser.add_argument(
        "--correction-out",
        "-c",
        default=None,
        help="Path to save correction JSON file (default: response_correction_<response_name>.json)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Override Gemini model name",
    )

    args = parser.parse_args()

    try:
        lvl2_feedback_response(
            criteria_file=args.criteria_file,
            response_file=args.response_file,
            feedback_output_path=args.feedback_out,
            correction_output_path=args.correction_out,
            model_name=args.model,
        )
        print("\nEvaluation complete! JSON output files generated successfully.")
    except Exception as exc:
        print(f"\n[ERROR]: {exc}", file=sys.stderr)
        sys.exit(1)
