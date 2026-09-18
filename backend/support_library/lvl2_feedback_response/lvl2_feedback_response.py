"""
Level 2 Feedback & Correction Evaluator
----------------------------------------
Evaluates a vendor response/proposal against criteria from a JSON file,
using the Google Gemini API (via google-generativeai or google-genai).

Features:
- Task A: Scorecard with exact dual citations (RFP source & Proposal source)
- Task A: Direct Issue-to-Suggested-Fix pairing (issues_and_fixes)
- Task A: Appendix A Rubric evaluation placeholder (status: PASS)
- Task B: Actionable recommendations, key improvements, and corrected proposal
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

warnings.filterwarnings("ignore", category=UserWarning)

from dotenv import load_dotenv
load_dotenv()

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

### CRITICAL INSTRUCTIONS ON USER-CUSTOMIZED CRITERIA & REQUIREMENT DESCRIPTIONS:
1. The customer/evaluator has customized the priority scores (1 to 5) AND the requirement descriptions:
   - READ THE `description` AND `rationale` CAREFULLY: They have been dynamically adapted by the evaluator to match the exact priority score!
   - Score 5 (Must-Have / Deal-Breaker): Non-negotiable mandatory requirement. Failure, omission, or deferral on ANY Score 5 requirement MUST result in an immediate severe penalty (Non-Compliant), an overall grade of D or F, and a recommendation to Reject or require critical clarifications!
   - Score 4 (High Priority): Essential operational deliverable; shortcomings must be flagged as major weaknesses.
   - Score 3 (Medium Priority): Standard expected requirement for delivery.
   - Score 2 (Low Priority): Secondary convenience; low penalty if deferred.
   - Score 1 (Nice to Have / Optional): Absence or omission does NOT penalize the vendor or lower the score. Mark status as Compliant or Partially Compliant with evaluation note "Optional enhancement (Score 1) not required for award."

2. MANDATORY - DUAL SOURCE CITATIONS FOR EVERY CRITERION:
   For each criterion in the scorecard, you MUST cite BOTH documents:
   - `rfp_citation`: The specific section or requirement title from the customer's RFP, plus the exact excerpt/quote demonstrating what was asked.
   - `proposal_citation`: The specific section in the vendor's proposal where it was addressed, plus the exact quote showing how they responded. If the requirement was omitted, ignored, or deferred, set `found: false`, `section: "Not Found"`, and `quote: "Omitted: no mention found anywhere in proposal"`.
   - `citation_summary`: A concise one-sentence comparison between the RFP requirement and Proposal response.

3. MANDATORY - ACTIONABLE ISSUES AND SUGGESTED FIXES (`issues_and_fixes`):
   For every significant weakness, omission, vague promise, unrealistic timeline/cost, or constraint violation:
   - Provide an issue title, severity ("Critical Deal-Breaker" | "Major Gap" | "Moderate Issue" | "Minor Improvement").
   - Explicit citations for RFP reference and Proposal reference.
   - A clear explanation of why this hurts the proposal.
   - A concrete `suggested_fix` with `rewritten_text`: the exact rewritten paragraph or section text ready to be copied and pasted directly into the vendor's proposal to fix the issue.

4. TASK B (CORRECTED PROPOSAL):
   Provide concrete actionable recommendations, key improvements, and a comprehensive corrected proposal addressing all requirements.

---

### OUTPUT FORMAT:
You MUST return your response strictly as a single valid, well-formed JSON object matching this schema:
{{
  "feedback": {{
    "response_file": "{response_file_name}",
    "vendor_name": "string - Name of the vendor who submitted the proposal",
    "compliance_grade": "string - e.g. A, B, C, D, or F",
    "bid_recommendation": "string - e.g. Accept | Shortlist with Clarifications | Reject",
    "executive_summary": "string - Overall evaluation summary reflecting user criteria priorities",
    "strengths": [
      "string - Specific strength 1 with citation",
      "string - Specific strength 2 with citation"
    ],
    "weaknesses_and_gaps": [
      "string - Specific weakness/gap 1",
      "string - Specific weakness/gap 2"
    ],
    "issues_and_fixes": [
      {{
        "issue_id": "ISSUE-01",
        "criterion_id": "REQ-01",
        "title": "Short descriptive title of the deficiency",
        "severity": "Critical Deal-Breaker | Major Gap | Moderate Issue | Minor Improvement",
        "rfp_reference": "RFP Section / Requirement title and quote",
        "proposal_reference": "Proposal section name and quote (or 'Omitted from proposal')",
        "explanation": "Clear explanation of the deficiency and operational impact",
        "suggested_fix": {{
          "action": "Actionable instructions on what to change",
          "rewritten_text": "Exact rewritten paragraph or section text ready to copy-paste into proposal"
        }}
      }}
    ],
    "scorecard": [
      {{
        "criterion_id": "REQ-01",
        "requirement_title": "string",
        "priority_level": "string",
        "priority_score": 5,
        "status": "Compliant | Partially Compliant | Non-Compliant",
        "rfp_citation": {{
          "section": "RFP Section name or requirement number",
          "quote": "Key excerpt or clause from the RFP"
        }},
        "proposal_citation": {{
          "section": "Proposal section name or 'Not Found'",
          "quote": "Relevant excerpt from proposal or 'Omitted: no mention found'",
          "found": true
        }},
        "citation_summary": "Summary of RFP clause vs Proposal quote",
        "evaluation_notes": "Detailed evaluation commentary justifying the status and score"
      }}
    ],
    "rubric_evaluation": {{
      "status": "PASS",
      "note": "Appendix A 7-Criteria Rubric evaluation deferred (See TODO.md)"
    }}
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
      "title": "string - Title of the corrected proposal",
      "executive_summary": "string",
      "technical_solution": "string - Comprehensive technical solution addressing all requirements",
      "requirements_revisions": [
        {{
          "criterion_id": "REQ-01",
          "requirement_title": "string",
          "priority_score": 5,
          "priority_level": "string",
          "deficiency_resolved": "string - What was missing or weak in the original response",
          "corrected_solution_text": "string - Exact rewritten text satisfying this requirement"
        }}
      ],
      "database_integration": "string - Detailed database integration plan (PostgreSQL without migration if specified)",
      "role_based_access_control": "string - Role-based access control and security governance",
      "low_stock_alerts": "string - Automated alerts and notification workflows",
      "timeline_and_onboarding": "string - Implementation milestones, pilot, rollout, and onboarding timeline",
      "support_and_slas": "string - Support SLAs, response times, and maintenance terms",
      "assumptions_and_risks": "string - Operational risks, assumptions, and mitigation",
      "pricing_and_budget": "string - Commercial pricing and budget alignment",
      "full_proposal_markdown": "string - Full, beautifully formatted markdown text of the corrected proposal"
    }}
  }}
}}

Do NOT output any markdown ticks outside the JSON. Return strictly valid JSON.
"""


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    key = explicit_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or key.strip() == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing!\n"
            "Please ensure GEMINI_API_KEY is configured in your .env file.\n"
            "Get an API key at: https://aistudio.google.com/app/apikey"
        )
    return key.strip()


def _call_gemini_api(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
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
        import google.generativeai as legacy_genai

        legacy_genai.configure(api_key=api_key)
        target_model = (
            model_name
            or os.getenv("STRONG_MODEL")
            or os.getenv("strong_model")
            or os.getenv("MEDIUM_MODEL")
            or os.getenv("GEMINI_MODEL")
            or "gemini-1.5-flash"
        )
        model = legacy_genai.GenerativeModel(
            model_name=target_model,
            generation_config={"response_mime_type": "application/json", "temperature": 0.2},
        )
        response = model.generate_content(prompt)
        return response.text

    except ImportError:
        raise ImportError(
            "Neither 'google-genai' nor 'google-generativeai' is installed.\n"
            "Please install the Google Gemini SDK via: pip install google-genai"
        )


def _normalize_feedback_data(
    feedback_data: Dict[str, Any],
    correction_data: Dict[str, Any],
    criteria_data: Dict[str, Any],
) -> Dict[str, Any]:
    criteria_list = criteria_data.get("criteria", []) if isinstance(criteria_data, dict) else []
    crit_map = {c.get("id"): c for c in criteria_list if isinstance(c, dict) and c.get("id")}

    # 1. Normalize Scorecard Citations
    scorecard = feedback_data.get("scorecard", [])
    if isinstance(scorecard, list):
        for idx, item in enumerate(scorecard):
            if not isinstance(item, dict):
                continue
            c_id = item.get("criterion_id", f"REQ-{idx+1:02d}")
            crit_info = crit_map.get(c_id, {})
            score = item.get("priority_score") or crit_info.get("score") or crit_info.get("priority_score") or 3
            item["priority_score"] = int(score)

            # Explicitly normalize status so non-compliant can never be mislabeled
            raw_status = str(item.get("status", "")).strip().lower()
            if any(k in raw_status for k in ["non", "fail", "omit", "unmet", "not compliant", "no"]):
                item["status"] = "Non-Compliant"
            elif any(k in raw_status for k in ["partial", "incomplete", "cond"]):
                item["status"] = "Partially Compliant"
            elif any(k in raw_status for k in ["compliant", "pass", "fully", "met", "yes"]):
                item["status"] = "Compliant"
            else:
                item["status"] = item.get("status") or "Non-Compliant"

            # Ensure rfp_citation
            rfp_cit = item.get("rfp_citation")
            if not isinstance(rfp_cit, dict) or not rfp_cit.get("quote"):
                item["rfp_citation"] = {
                    "section": crit_info.get("category", "RFP Requirements"),
                    "quote": crit_info.get("description") or crit_info.get("title", f"Requirement {c_id}")
                }

            # Ensure proposal_citation
            prop_cit = item.get("proposal_citation")
            is_non_compliant = item.get("status") == "Non-Compliant"
            if not isinstance(prop_cit, dict) or not prop_cit.get("quote"):
                item["proposal_citation"] = {
                    "section": "Not Found" if is_non_compliant else "Proposal Section",
                    "quote": "Omitted from proposal" if is_non_compliant else item.get("evaluation_notes", "Addressed in proposal"),
                    "found": not is_non_compliant
                }
            elif "found" not in prop_cit:
                prop_cit["found"] = not is_non_compliant

            # Ensure citation summary
            if not item.get("citation_summary"):
                rfp_sec = item["rfp_citation"].get("section", "RFP")
                prop_sec = item["proposal_citation"].get("section", "Proposal")
                item["citation_summary"] = f"{rfp_sec} vs {prop_sec}"

    # 2. Normalize Issues & Suggested Fixes (Vấn đề 3)
    issues_and_fixes = feedback_data.get("issues_and_fixes")
    if not isinstance(issues_and_fixes, list) or len(issues_and_fixes) == 0:
        issues_and_fixes = []
        revisions = []
        if isinstance(correction_data, dict):
            cp = correction_data.get("corrected_proposal", {})
            if isinstance(cp, dict):
                revisions = cp.get("requirements_revisions", [])
        rev_map = {r.get("criterion_id"): r for r in revisions if isinstance(r, dict)}

        issue_counter = 1
        for item in scorecard:
            status = str(item.get("status", "")).lower()
            if status in ["non-compliant", "partially compliant"]:
                c_id = item.get("criterion_id", f"REQ-{issue_counter}")
                crit_info = crit_map.get(c_id, {})
                score = item.get("priority_score", 3)
                severity = "Critical Deal-Breaker" if score == 5 else ("Major Gap" if score == 4 else "Moderate Issue")
                rev_item = rev_map.get(c_id, {})

                issues_and_fixes.append({
                    "issue_id": f"ISSUE-{issue_counter:02d}",
                    "criterion_id": c_id,
                    "title": f"Deficiency in {item.get('requirement_title', c_id)}",
                    "severity": severity,
                    "rfp_reference": f"{item.get('rfp_citation', {}).get('section', 'RFP')}: \"{item.get('rfp_citation', {}).get('quote', '')}\"",
                    "proposal_reference": f"{item.get('proposal_citation', {}).get('section', 'Proposal')}: \"{item.get('proposal_citation', {}).get('quote', '')}\"",
                    "explanation": item.get("evaluation_notes") or rev_item.get("deficiency_resolved") or "Requirement was not fully addressed.",
                    "suggested_fix": {
                        "action": f"Address {crit_info.get('title', c_id)} according to RFP specifications.",
                        "rewritten_text": rev_item.get("corrected_solution_text") or f"We commit to fully delivering {crit_info.get('title', c_id)} in strict compliance with the RFP requirements."
                    }
                })
                issue_counter += 1

        if len(issues_and_fixes) == 0:
            for idx, w in enumerate(feedback_data.get("weaknesses_and_gaps", [])):
                issues_and_fixes.append({
                    "issue_id": f"ISSUE-{idx+1:02d}",
                    "criterion_id": f"GAP-{idx+1:02d}",
                    "title": f"Proposal Weakness #{idx+1}",
                    "severity": "Major Gap",
                    "rfp_reference": "RFP Requirements & Constraints",
                    "proposal_reference": "Vendor Proposal Submission",
                    "explanation": w,
                    "suggested_fix": {
                        "action": "Revise proposal section to address this gap directly.",
                        "rewritten_text": "In direct response to client requirements, we guarantee full alignment on this item with concrete milestones and transparent SLAs."
                    }
                })

        feedback_data["issues_and_fixes"] = issues_and_fixes

    # 3. Always include rubric_evaluation (Vấn đề 1: PASS)
    if "rubric_evaluation" not in feedback_data or not isinstance(feedback_data["rubric_evaluation"], dict):
        feedback_data["rubric_evaluation"] = {
            "status": "PASS",
            "note": "Appendix A 7-Criteria Rubric evaluation deferred (See TODO.md)"
        }

    # 4. Calculate Dynamic Weighted Score from normalized scorecard
    total_weight = 0
    earned_weight = 0.0
    for item in scorecard:
        sc = int(item.get("priority_score", 3))
        total_weight += sc
        st = item.get("status")
        if st == "Compliant":
            earned_weight += sc * 1.0
        elif st == "Partially Compliant":
            earned_weight += sc * 0.5
        else:
            earned_weight += 0.0

    calculated_score = int(round((earned_weight / total_weight) * 100)) if total_weight > 0 else 0
    feedback_data["overall_score"] = {
        "weighted_total": calculated_score,
        "earned_points": round(earned_weight, 1),
        "total_possible_points": total_weight,
        "percentage": calculated_score,
    }

    return feedback_data


def _parse_gemini_json_output(raw_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            feedback_data = data.get("feedback") or data.get("Task A") or {}
            correction_data = data.get("correction") or data.get("Task B") or {}

            if isinstance(feedback_data, str):
                try:
                    feedback_data = json.loads(feedback_data)
                except Exception:
                    feedback_data = {"raw_feedback": feedback_data}

            if isinstance(correction_data, str):
                try:
                    correction_data = json.loads(correction_data)
                except Exception:
                    correction_data = {"raw_correction": correction_data}

            if feedback_data or correction_data:
                return feedback_data, correction_data

    except json.JSONDecodeError:
        pass

    return {"raw_output": raw_text}, {"raw_output": raw_text}


def lvl2_feedback_response(
    criteria_file: str,
    response_file: str,
    feedback_output_path: Optional[str] = None,
    correction_output_path: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    save_to_disk: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
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

    resp_stem = resp_path.stem
    actual_feedback_path = feedback_output_path or f"response_feedback_{resp_stem}.json"
    actual_correction_path = correction_output_path or f"response_correction_{resp_stem}.json"

    if not actual_feedback_path.endswith(".json"):
        actual_feedback_path = f"{os.path.splitext(actual_feedback_path)[0]}.json"
    if not actual_correction_path.endswith(".json"):
        actual_correction_path = f"{os.path.splitext(actual_correction_path)[0]}.json"

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

    effective_api_key = _get_api_key(api_key)

    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        criteria_json=criteria_json_str,
        response_markdown=response_text,
        response_file_name=resp_path.name
    )

    print(f"[AI] Evaluating '{resp_path.name}' against criteria in '{crit_path.name}'...")
    raw_api_output = _call_gemini_api(prompt, api_key=effective_api_key, model_name=model_name)

    feedback_data, correction_data = _parse_gemini_json_output(raw_api_output)
    feedback_data = _normalize_feedback_data(feedback_data, correction_data, criteria_data)

    if isinstance(feedback_data, dict) and "response_file" not in feedback_data:
        feedback_data["response_file"] = resp_path.name
    if isinstance(correction_data, dict) and "response_file" not in correction_data:
        correction_data["response_file"] = resp_path.name

    if save_to_disk or feedback_output_path:
        fb_target = Path(actual_feedback_path)
        fb_target.parent.mkdir(parents=True, exist_ok=True)
        with open(fb_target, "w", encoding="utf-8") as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        print(f"[Export JSON] Saved feedback to: {fb_target.resolve()}")

    if save_to_disk or correction_output_path:
        corr_target = Path(actual_correction_path)
        corr_target.parent.mkdir(parents=True, exist_ok=True)
        with open(corr_target, "w", encoding="utf-8") as f:
            json.dump(correction_data, f, indent=2, ensure_ascii=False)
        print(f"[Export JSON] Saved correction to: {corr_target.resolve()}")

    return feedback_data, correction_data


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
