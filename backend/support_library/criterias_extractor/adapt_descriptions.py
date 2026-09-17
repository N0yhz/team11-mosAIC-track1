"""
Criteria Description Adaptation Module
----------------------------------------
Uses LITE_MODEL (gemini-3.5-flash-lite) to regenerate requirement descriptions
and rationales when the user adjusts the priority mark (1 to 5).

Ensures that the linguistic tone, contractual urgency, and evaluation expectations
of the requirement text directly reflect the new priority mark.
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from typing import Any, Dict, List, Optional, Union

warnings.filterwarnings("ignore", category=UserWarning)

from dotenv import load_dotenv

load_dotenv()

PRIORITY_MARK_INSTRUCTIONS = {
    5: "MANDATORY MUST-HAVE (Deal-Breaker): Rewrite as a strict, non-negotiable requirement. Use imperative phrases ('The solution MUST strictly provide...', 'Mandatory prerequisite; non-compliance disqualifies bid'). Emphasize that omission is an immediate deal-breaker.",
    4: "HIGH PRIORITY: Rewrite as a crucial core operational deliverable essential for system success and contract award.",
    3: "MEDIUM PRIORITY: Rewrite as a standard expected deliverable, typical for complete project delivery.",
    2: "LOW PRIORITY: Rewrite as a secondary feature that can be deferred, phased, or delivered via standard workarounds without penalty.",
    1: "NICE TO HAVE (Optional): Rewrite as an optional cosmetic or convenience enhancement. Explicitly state that omission or total absence will NOT penalize the vendor or lower the evaluation score.",
}

PRIORITY_LEVEL_TITLES = {
    5: "5 - Must have",
    4: "4 - High priority",
    3: "3 - Medium priority",
    2: "2 - Low priority",
    1: "1 - Nice to have",
}


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    key = (
        explicit_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    if not key:
        raise ValueError("Missing GEMINI_API_KEY in environment or argument.")
    return key.strip()


def adapt_criteria_descriptions(
    criteria_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    only_modified: bool = True,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Regenerates requirement descriptions and rationales using LITE_MODEL
    so the wording matches the assigned 1-5 priority mark.

    :param criteria_data: Either a criteria report dict with 'criteria' list, or a raw criteria list.
    :param api_key: Optional Gemini API key.
    :param model_name: Optional model override (defaults to LITE_MODEL / gemini-3.5-flash-lite).
    :param only_modified: If True, only adapts criteria where is_user_modified is True.
    :return: Updated criteria_data with regenerated descriptions and rationales.
    """
    is_dict = isinstance(criteria_data, dict)
    criteria_list = criteria_data.get("criteria", []) if is_dict else criteria_data

    if not criteria_list:
        return criteria_data

    # Identify items to adapt
    items_to_adapt = []
    for idx, c in enumerate(criteria_list):
        if not only_modified or c.get("is_user_modified", False):
            score = int(c.get("score") or c.get("priority_score") or 3)
            items_to_adapt.append({
                "index": idx,
                "id": c.get("id", f"REQ-{idx+1:02d}"),
                "title": c.get("title", ""),
                "category": c.get("category", "General"),
                "current_score": score,
                "existing_description": c.get("description", ""),
                "target_priority_instruction": PRIORITY_MARK_INSTRUCTIONS.get(score, PRIORITY_MARK_INSTRUCTIONS[3]),
            })

    if not items_to_adapt:
        print("[AI Lite] No criteria marked for description adaptation.")
        return criteria_data

    effective_api_key = _get_api_key(api_key)
    target_model = (
        model_name
        or os.getenv("LITE_MODEL")
        or os.getenv("lite_model")
        or os.getenv("MEDIUM_MODEL")
        or os.getenv("GEMINI_MODEL")
        or "gemini-3.5-flash-lite"
    )

    prompt = f"""
You are a Requirements Realignment Assistant.
The evaluator has adjusted the priority marks (1 to 5) for the following customer RFP requirements.
Rewrite each requirement's `description` and `rationale` so that the language, contractual urgency, and evaluation expectations precisely match the assigned priority mark:

Priority Scale Rules:
- Mark 5 (Must-Have): Rewrite using strict imperative language ("The solution MUST strictly provide...", "Mandatory requirement; failure to comply will disqualify proposal"). Must emphasize that omission is an immediate deal-breaker.
- Mark 4 (High Priority): Rewrite as an essential operational deliverable crucial for operational success.
- Mark 3 (Medium Priority): Rewrite as a standard expected deliverable typical for complete project delivery.
- Mark 2 (Low Priority): Rewrite as a secondary feature that can be deferred or phased without penalizing the overall bid.
- Mark 1 (Nice to Have): Rewrite as an optional enhancement; explicitly state that absence or omission will NOT penalize the vendor or lower the score in any evaluation phase.

Requirements to update:
{json.dumps(items_to_adapt, indent=2, ensure_ascii=False)}

Return ONLY a valid JSON array of objects with the exact schema:
[
  {{
    "id": "REQ-XX",
    "description": "rewritten description fitting the priority mark",
    "rationale": "rewritten rationale explaining why it has this priority level and evaluation impact",
    "priority_level": "X - Title"
  }}
]
"""

    adapted_results = {}
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=effective_api_key)
        fallback_models = [
            target_model,
            "gemini-3.5-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.8-flash",
        ]
        seen = set()
        models_to_try = [m for m in fallback_models if m and not (m in seen or seen.add(m))]

        raw_response = None
        for m in models_to_try:
            try:
                res = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    )
                )
                if res.text:
                    raw_response = res.text
                    print(f"[AI Lite] Successfully adapted descriptions with model '{m}'.")
                    break
            except Exception as exc:
                print(f"[AI Lite Warning] Model '{m}' failed: {exc}")
                continue

        if raw_response:
            parsed = json.loads(raw_response)
            if isinstance(parsed, list):
                for item in parsed:
                    if "id" in item:
                        adapted_results[item["id"]] = item

    except Exception as err:
        print(f"[AI Lite Error] Calling Gemini for description adaptation failed: {err}")

    # Merge results back or use rule-based fallback
    for item in items_to_adapt:
        req_id = item["id"]
        idx = item["index"]
        target_score = item["current_score"]

        if req_id in adapted_results:
            new_info = adapted_results[req_id]
            criteria_list[idx]["description"] = new_info.get("description") or criteria_list[idx]["description"]
            criteria_list[idx]["rationale"] = new_info.get("rationale") or criteria_list[idx]["rationale"]
            criteria_list[idx]["priority_level"] = new_info.get("priority_level") or PRIORITY_LEVEL_TITLES.get(target_score, f"{target_score} - Priority {target_score}")
            criteria_list[idx]["is_description_adapted"] = True
            criteria_list[idx]["adapted_to_score"] = target_score
        else:
            # Rule-based fallback if API was unavailable
            base_desc = item["existing_description"]
            if target_score == 5:
                criteria_list[idx]["description"] = f"CRITICAL MANDATORY REQUIREMENT (Deal-Breaker): The solution MUST strictly provide: {base_desc}. Failure to comply will disqualify the proposal."
                criteria_list[idx]["rationale"] = "Designated as a non-negotiable must-have (Mark 5). Any omission will cause immediate disqualification."
            elif target_score == 1:
                criteria_list[idx]["description"] = f"Optional enhancement: {base_desc}. The absence or omission of this feature will NOT penalize the vendor or lower the score."
                criteria_list[idx]["rationale"] = "Marked as nice-to-have (Mark 1); optional utility without impacting evaluation success."
            elif target_score == 2:
                criteria_list[idx]["description"] = f"Secondary feature: {base_desc}. May be phased or deferred to later milestones."
                criteria_list[idx]["rationale"] = "Low priority convenience feature (Mark 2)."
            elif target_score == 4:
                criteria_list[idx]["description"] = f"High-priority operational requirement: {base_desc}. Crucial for operational readiness."
                criteria_list[idx]["rationale"] = "High priority deliverable (Mark 4) strongly impacting proposal scoring."
            criteria_list[idx]["priority_level"] = PRIORITY_LEVEL_TITLES.get(target_score, f"{target_score} - Priority")
            criteria_list[idx]["is_description_adapted"] = True
            criteria_list[idx]["adapted_to_score"] = target_score

    if is_dict:
        criteria_data["criteria"] = criteria_list
        return criteria_data
    return criteria_list
