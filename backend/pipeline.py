"""
Level 2 Evaluation Pipeline (lvl2_pipeline)
--------------------------------------------
Orchestrates the extraction of evaluation criteria from an RFP and the
evaluation of a vendor's response/proposal against those criteria.

Supports both a split 2-stage workflow and a unified 1-step pipeline:
- Stage 1: `extract_criteria_stage()` extracts criteria and ranks priorities (1-5).
- Stage 2: `evaluate_response_stage()` evaluates a response against (potentially modified) criteria.
- Combined: `lvl2_pipeline()` runs Stage 1 followed by Stage 2.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# ---------------------------------------------------------------------
# Imports with package fallback
# ---------------------------------------------------------------------
try:
    from support_library import (
        criteria_extractor,
        lvl2_feedback_response,
        adapt_criteria_descriptions,
        convert_to_markdown,
        extract_file,
    )
except ImportError:
    try:
        from .support_library import (
            criteria_extractor,
            lvl2_feedback_response,
            adapt_criteria_descriptions,
            convert_to_markdown,
            extract_file,
        )
    except ImportError:
        from backend.support_library import (
            criteria_extractor,
            lvl2_feedback_response,
            adapt_criteria_descriptions,
            convert_to_markdown,
            extract_file,
        )


# =====================================================================
# Document Preprocessing & Format Conversion Placeholder
# =====================================================================
def _convert_to_markdown_placeholder(file_path: str) -> str:
    """
    Converts any input document format (PDF, Excel, CSV, TXT, Markdown)
    to a clean Markdown (.md) format prior to downstream pipeline analysis.
    Supports Customer RFPs and Vendor Proposals (including PowerPoint PDF exports).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.resolve()}")

    ext = path.suffix.lower()

    # If it is already a markdown document, return directly
    if ext in [".md", ".markdown"]:
        return str(path)

    try:
        print(f"[Extractor] Auto-detecting & parsing '{path.name}' ({ext}) into clean Markdown...")
        output_md_path = convert_to_markdown(
            path,
            include_metadata=True,
            include_page_headers=False,
        )
        print(f"[Extractor] Successfully converted '{path.name}' -> '{output_md_path}'")
        return str(output_md_path)
    except Exception as err:
        print(f"[Extractor Warning] Conversion via extractor failed for '{path.name}': {err}")
        # Plain text fallback
        if ext in [".txt", ".log", ".text"]:
            return str(path)
        raise ValueError(f"Failed to process document '{path.name}': {err}")


# =====================================================================
# Stage 1: Extract RFP Criteria
# =====================================================================
def extract_criteria_stage(
    rfp_file: str,
    output_file: str = "criteria.json",
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Stage 1: Extract requirements from an RFP and rank them on a 1–5 priority scale.
    The output dictionary can be reviewed and edited by users before evaluating responses.

    :param rfp_file: Path to customer RFP document (.md, .txt).
    :param output_file: Destination path to save intermediate criteria.json.
    :return: Parsed criteria report dictionary.
    """
    print(f"\n[Stage 1] Extracting criteria from '{rfp_file}' -> '{output_file}'...")
    processed_rfp = _convert_to_markdown_placeholder(rfp_file)

    effective_model = (
        model_name
        or os.getenv("MEDIUM_MODEL")
        or os.getenv("medium_model")
        or os.getenv("GEMINI_MODEL")
    )
    criteria_report = criteria_extractor(
        processed_rfp,
        output_file=output_file,
        model_name=effective_model,
        api_key=api_key,
    )

    if not criteria_report and Path(output_file).exists():
        with open(output_file, "r", encoding="utf-8") as f_crit:
            criteria_report = json.load(f_crit)

    if isinstance(criteria_report, str):
        try:
            criteria_report = json.loads(criteria_report)
        except Exception:
            pass

    print(f"[Stage 1 Complete] Extracted {len(criteria_report.get('criteria', []))} criteria to '{output_file}'.")
    return criteria_report


# =====================================================================
# Stage 2: Evaluate Proposal Response against Criteria
# =====================================================================
def evaluate_response_stage(
    criteria_input: Union[Dict[str, Any], str, Path],
    response_file: str,
    output_file: Optional[str] = None,
    criteria_file: Optional[str] = None,
    rfp_file: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Stage 2: Evaluate a vendor response against criteria (which may be customized by the user).

    :param criteria_input: Criteria data dict OR path to criteria JSON file.
    :param response_file: Path to vendor proposal/response document (.md).
    :param output_file: Target path for the final unified JSON file.
    :param criteria_file: Destination path for criteria JSON if criteria_input is a dict.
    :param rfp_file: Optional path to RFP for metadata recording.
    :return: Consolidated evaluation dictionary.
    """
    processed_response = _convert_to_markdown_placeholder(response_file)
    resp_stem = Path(processed_response).stem
    final_output_path = output_file or f"lvl2_pipeline_output_{resp_stem}.json"
    if not final_output_path.endswith(".json"):
        final_output_path = f"{final_output_path}.json"

    # Prepare criteria JSON file path
    temp_criteria_dir = None
    if isinstance(criteria_input, dict):
        criteria_data = criteria_input
        if criteria_file:
            actual_criteria_file = criteria_file
        else:
            temp_criteria_dir = tempfile.mkdtemp(prefix="crit_eval_")
            actual_criteria_file = str(Path(temp_criteria_dir) / "custom_criteria.json")

        Path(actual_criteria_file).parent.mkdir(parents=True, exist_ok=True)
        with open(actual_criteria_file, "w", encoding="utf-8") as f:
            json.dump(criteria_data, f, indent=2, ensure_ascii=False)
    else:
        actual_criteria_file = str(criteria_input)
        with open(actual_criteria_file, "r", encoding="utf-8") as f:
            criteria_data = json.load(f)

    # Check if any user-modified criteria need description adaptation with LITE_MODEL
    try:
        criteria_items = criteria_data.get("criteria", []) if isinstance(criteria_data, dict) else []
        needs_adaptation = any(c.get("is_user_modified") and not c.get("is_description_adapted") for c in criteria_items)
        if needs_adaptation:
            print("[Stage 2 Pre-step] Auto-adapting requirement descriptions with LITE_MODEL to match updated marks...")
            criteria_data = adapt_criteria_descriptions(criteria_data, api_key=api_key)
            with open(actual_criteria_file, "w", encoding="utf-8") as f_upd:
                json.dump(criteria_data, f_upd, indent=2, ensure_ascii=False)
            print("[Stage 2 Pre-step] Requirement descriptions adapted successfully.")
    except Exception as adapt_err:
        print(f"[Stage 2 Pre-step Warning] Description adaptation failed: {adapt_err}")

    try:
        print(f"\n[Stage 2] Evaluating '{processed_response}' against criteria in '{actual_criteria_file}'...")
        effective_model = (
            model_name
            or os.getenv("STRONG_MODEL")
            or os.getenv("strong_model")
            or os.getenv("MEDIUM_MODEL")
            or os.getenv("medium_model")
            or os.getenv("GEMINI_MODEL")
        )
        feedback_result, correction_result = lvl2_feedback_response(
            criteria_file=actual_criteria_file,
            response_file=processed_response,
            api_key=api_key,
            model_name=effective_model,
            save_to_disk=False,
        )
        print("[Stage 2 Complete] Feedback and corrections generated.")

        consolidated_data: Dict[str, Any] = {
            "metadata": {
                "rfp_file": str(Path(rfp_file).resolve()) if rfp_file else None,
                "response_file": str(Path(response_file).resolve()),
                "criteria_file": str(Path(actual_criteria_file).resolve()),
                "executed_at": datetime.now().isoformat(),
                "is_customized_criteria": isinstance(criteria_input, dict),
            },
            "criteria_report": criteria_data,
            "criteria_output": criteria_data,
            "response_feedback": feedback_result,
            "response_correction": correction_result,
        }

        target = Path(final_output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(consolidated_data, f, indent=2, ensure_ascii=False)

        print(f"[Unified JSON Saved] -> {target.resolve()}")
        return consolidated_data

    finally:
        if temp_criteria_dir:
            import shutil
            shutil.rmtree(temp_criteria_dir, ignore_errors=True)
        # Always delete intermediate feedback/correction files from folder after each run
        for p in Path(".").glob("response_feedback_*.json"):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass
        for p in Path(".").glob("response_correction_*.json"):
            try:
                p.unlink(missing_ok=True)
            except Exception:
                pass


# =====================================================================
# Unified Pipeline (Full 2-Step Orchestration)
# =====================================================================
def lvl2_pipeline(
    rfp_file: str,
    response_file: str,
    output_file: Optional[str] = None,
    criteria_file: str = "criteria.json",
) -> Dict[str, Any]:
    """
    Orchestrates full Level 2 evaluation: extracts criteria from RFP, then evaluates proposal.
    Chains `extract_criteria_stage()` followed by `evaluate_response_stage()`.
    """
    print("\n" + "=" * 80)
    print("  EXECUTING LEVEL 2 EVALUATION PIPELINE (UNIFIED)")
    print("=" * 80)

    # Step 1: Extract criteria
    criteria_report = extract_criteria_stage(
        rfp_file=rfp_file,
        output_file=criteria_file,
    )

    # Step 2: Evaluate response against extracted criteria
    result = evaluate_response_stage(
        criteria_input=criteria_report,
        response_file=response_file,
        output_file=output_file,
        criteria_file=criteria_file,
        rfp_file=rfp_file,
    )

    print("=" * 80 + "\n")
    return result


__all__ = [
    "extract_criteria_stage",
    "evaluate_response_stage",
    "lvl2_pipeline",
    "adapt_criteria_descriptions",
    "_convert_to_markdown_placeholder",
]


# =====================================================================
# CLI Entrypoint
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Level 2 Pipeline: RFP criteria extraction and vendor response evaluation."
    )
    default_rfp = "data/rfp/rfp_nordframe.md"
    default_resp = "data/response/response_2_medium.md"

    parser.add_argument("rfp_file", nargs="?", default=default_rfp)
    parser.add_argument("response_file", nargs="?", default=default_resp)
    parser.add_argument("--output-file", "-o", default=None)
    parser.add_argument("--criteria-file", "-c", default="criteria.json")

    args = parser.parse_args()

    try:
        lvl2_pipeline(
            rfp_file=args.rfp_file,
            response_file=args.response_file,
            output_file=args.output_file,
            criteria_file=args.criteria_file,
        )
    except Exception as exc:
        print(f"\n[PIPELINE ERROR]: {exc}", file=sys.stderr)
        sys.exit(1)
