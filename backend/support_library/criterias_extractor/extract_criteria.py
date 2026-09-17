"""
Criteria Extractor for Customer RFP (Request for Proposal)
-----------------------------------------------------------
Reads a markdown (.md) document containing customer requirements under `rfp/`,
sends the text to the Google Gemini API, extracts discrete requirements,
and ranks them on a scale of 1 to 5:
  1 = 'nice to have' (optional / cosmetic)
  2 = 'low priority' (minor convenience, can be deferred)
  3 = 'medium priority' (standard feature for complete workflow)
  4 = 'high priority' (crucial for operational success)
  5 = 'must-have' (critical core functionality, non-negotiable)

Outputs:
- Formatted console table or JSON
- Export to JSON file (criterias_output.json)
- Export to Markdown analysis report (criterias_analyze.md)

Supported SDKs:
- google-genai (current official SDK: from google import genai)
- google-generativeai (legacy SDK: import google.generativeai as genai)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Suppress minor SDK warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------
# Environment Setup: Load API key from .env using python-dotenv
# ---------------------------------------------------------------------
from dotenv import load_dotenv

load_dotenv()


# =====================================================================
# Prompt Template for Requirements Extraction & Scoring (1 to 5)
# =====================================================================
PROMPT_TEMPLATE = """
You are an expert Senior Business Analyst and Requirements Engineer.
Analyze the following Request for Proposal (RFP) / Customer Requirements document carefully.

Your task:
1. Extract ALL discrete requirements and evaluation criteria (both functional and non-functional).
2. Categorize each criterion (e.g., Core Functionality, Integration & Database, Security & Access Control, Deployment & Onboarding, SLA & Maintenance).
3. Score each criterion priority on a scale of 1 to 5:
   - 5 = 'must-have' (Critical, non-negotiable core functionality; the system cannot function without it)
   - 4 = 'high priority' (Crucial for operational success, high business value, major deliverable)
   - 3 = 'medium priority' (Standard expected feature, enhances workflow and usability)
   - 2 = 'low priority' (Secondary feature, minor convenience, can be deferred to later phases)
   - 1 = 'nice to have' (Optional enhancement, visual flourish, low urgency)
4. Provide a clear, convincing rationale explaining why this score was assigned.
5. Identify any key constraints, budget, timeline, and decision dates noted in the document.

### CUSTOMER RFP DOCUMENT:
---
{document_content}
---

Return your analysis strictly as a valid JSON object matching this schema:
{{
  "project_title": "string - Title of the RFP project",
  "client_name": "string - Client name or organization",
  "industry": "string - Client industry",
  "summary": "string - Brief 2-3 sentence overview of the project and core goals",
  "budget": "string - Mentioned budget or 'Not specified'",
  "timeline": "string - Mentioned timeline or 'Not specified'",
  "criteria": [
    {{
      "id": "REQ-01",
      "title": "Short title summarizing the criterion / requirement",
      "category": "Category name",
      "score": 5,
      "priority_level": "5 - Must have",
      "description": "Detailed description of what the client requires",
      "rationale": "Clear explanation justifying the priority score"
    }}
  ]
}}
Do NOT output any markdown commentary outside the JSON block.
"""


def _get_api_key(explicit_key: Optional[str] = None) -> str:
    """Retrieve Gemini API key from parameters or environment variables."""
    key = explicit_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key or key.strip() == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key is missing or unconfigured!\n"
            "Please configure your .env file with:\n"
            "  GEMINI_API_KEY=AIzaSy...\n"
            "Obtain a key at: https://aistudio.google.com/app/apikey"
        )
    return key.strip()


def _call_gemini(prompt: str, api_key: str, model_name: Optional[str] = None) -> str:
    """
    Call Google Gemini API using either google-genai (current official SDK)
    or google-generativeai (legacy SDK).
    """
    # 1. First try google-genai (current official SDK)
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        target_model = (
            model_name
            or os.getenv("MEDIUM_MODEL")
            or os.getenv("medium_model")
            or os.getenv("GEMINI_MODEL")
            or "gemini-3.6-flash"
        )

        candidate_fallbacks = [
            target_model,
            os.getenv("MEDIUM_MODEL"),
            os.getenv("medium_model"),
            "gemini-3.6-flash",
            os.getenv("LITE_MODEL"),
            os.getenv("lite_model"),
            "gemini-3.5-flash-lite",
            os.getenv("STRONG_MODEL"),
            os.getenv("strong_model"),
            "gemini-3.8-flash",
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
                        temperature=0.1,
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

    # 2. Fallback to google-generativeai (legacy SDK)
    try:
        import google.generativeai as legacy_genai

        legacy_genai.configure(api_key=api_key)
        target_model = model_name or os.getenv("MEDIUM_MODEL") or os.getenv("medium_model") or os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
        model = legacy_genai.GenerativeModel(
            model_name=target_model,
            generation_config={"response_mime_type": "application/json", "temperature": 0.1},
        )
        response = model.generate_content(prompt)
        return response.text

    except ImportError:
        raise ImportError(
            "Neither 'google-genai' nor 'google-generativeai' is installed.\n"
            "Please install the official Google library: pip install google-genai"
        )


def _clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Strip markdown formatting fences and parse string into JSON."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)

    # Normalize 'requirements' to 'criteria' if needed
    if "requirements" in data and "criteria" not in data:
        data["criteria"] = data["requirements"]

    # Ensure each item has 'score' attribute
    for item in data.get("criteria", []):
        if "score" not in item and "priority_score" in item:
            item["score"] = item["priority_score"]
        if "priority_score" not in item and "score" in item:
            item["priority_score"] = item["score"]

    return data


def export_to_json(data: Dict[str, Any], file_path: str) -> None:
    """
    Export criteria with their scores and details to a clean JSON file.
    """
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "project_title": data.get("project_title", "RFP Analysis"),
        "client_name": data.get("client_name", "N/A"),
        "industry": data.get("industry", "N/A"),
        "summary": data.get("summary", ""),
        "budget": data.get("budget", "Not specified"),
        "timeline": data.get("timeline", "Not specified"),
        "total_criteria": len(data.get("criteria", [])),
        "criteria": data.get("criteria", [])
    }

    with open(target, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"[Export JSON] Saved criteria with scores to: {target.resolve()}")


def export_to_markdown(data: Dict[str, Any], file_path: str) -> None:
    """
    Export a comprehensive RFP analysis report to a Markdown (.md) file.
    """
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    project_title = data.get("project_title", "RFP Analysis")
    client = data.get("client_name", "N/A")
    industry = data.get("industry", "N/A")
    summary = data.get("summary", "")
    budget = data.get("budget", "Not specified")
    timeline = data.get("timeline", "Not specified")
    criteria: List[Dict[str, Any]] = data.get("criteria", [])

    score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for c in criteria:
        s = c.get("score") or c.get("priority_score", 0)
        if s in score_counts:
            score_counts[s] += 1

    md_lines = [
        f"# RFP Analysis & Criteria Ranking Report: {project_title}",
        "",
        f"- **Client:** {client}",
        f"- **Industry:** {industry}",
        f"- **Budget:** {budget}",
        f"- **Expected Timeline:** {timeline}",
        "",
        f"> **Project Summary:** {summary}",
        "",
        "---",
        "",
        "## 1. Summary of Criteria & Priority Ranking (Scale 1 - 5)",
        "",
        "Priority Scoring Legend:",
        "- **5**: Must-have (Critical, non-negotiable core functionality; system cannot function without it)",
        "- **4**: High priority (Crucial for operational success, high business value)",
        "- **3**: Medium priority (Standard expected feature, enhances workflow and usability)",
        "- **2**: Low priority (Secondary feature, minor convenience, can be deferred)",
        "- **1**: Nice to have (Optional enhancement, visual flourish, low urgency)",
        "",
        "| ID | Criterion / Requirement | Category | Priority Level | Score | Ranking Rationale |",
        "|:---|:---|:---|:---|:---:|:---|"
    ]

    for c in criteria:
        c_id = c.get("id", "N/A")
        title = c.get("title", "")
        category = c.get("category", "General")
        score = c.get("score", c.get("priority_score", "-"))
        priority_level = c.get("priority_level", f"Score {score}")
        rationale = c.get("rationale", "").replace("|", "-")

        md_lines.append(
            f"| **{c_id}** | {title} | {category} | `{priority_level}` | **{score}/5** | {rationale} |"
        )

    md_lines.extend([
        "",
        "### Priority Distribution Statistics",
        f"- **[Score 5] Must-have (Critical):** {score_counts[5]} criteria",
        f"- **[Score 4] High priority:** {score_counts[4]} criteria",
        f"- **[Score 3] Medium priority:** {score_counts[3]} criteria",
        f"- **[Score 2] Low priority:** {score_counts[2]} criteria",
        f"- **[Score 1] Nice to have:** {score_counts[1]} criteria",
        f"- **==> TOTAL CRITERIA:** {len(criteria)}",
        "",
        "---",
        "",
        "## 2. Detailed Criterion Breakdown",
        ""
    ])

    for c in criteria:
        c_id = c.get("id", "N/A")
        title = c.get("title", "")
        category = c.get("category", "General")
        score = c.get("score", c.get("priority_score", "-"))
        priority_level = c.get("priority_level", f"Score {score}")
        description = c.get("description", "")
        rationale = c.get("rationale", "")

        md_lines.extend([
            f"### [{c_id}] {title}",
            f"- **Category:** {category}",
            f"- **Priority Score:** **{score}/5** (`{priority_level}`)",
            f"- **Requirement Description:** {description}",
            f"- **Ranking Rationale:** {rationale}",
            ""
        ])

    content = "\n".join(md_lines)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Export MD] Saved Markdown analysis to: {target.resolve()}")


def extract_and_rank_criteria(
    rfp_file_path: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    output_format: str = "table",
    output_json_path: Optional[str] = None,
    output_md_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Read a customer RFP markdown (.md) file, query Google Gemini API to extract
    and score all requirements from 1 to 5, and optionally export JSON and Markdown.

    :param rfp_file_path: Path to the .md RFP file (e.g. rfp/rfp_nordframe.md).
    :param api_key: Gemini API Key (optional, defaults to .env GEMINI_API_KEY).
    :param model_name: Model identifier (optional, defaults to .env GEMINI_MODEL).
    :param output_format: 'table', 'json', or 'none'.
    :param output_json_path: Path to save criteria JSON output (e.g. criterias_output.json).
    :param output_md_path: Path to save analysis markdown report (e.g. criterias_analyze.md).
    :return: Parsed dictionary containing project title, client, and criteria list with scores.
    """
    path = Path(rfp_file_path)
    if not path.is_file():
        raise FileNotFoundError(f"RFP file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        raise ValueError(f"RFP file is empty: {path}")

    effective_api_key = _get_api_key(api_key)

    prompt = PROMPT_TEMPLATE.format(document_content=content)
    raw_response = _call_gemini(prompt, api_key=effective_api_key, model_name=model_name)

    result_data = _clean_json_response(raw_response)

    if "criteria" in result_data and isinstance(result_data["criteria"], list):
        result_data["criteria"].sort(
            key=lambda item: item.get("score", item.get("priority_score", 0)), reverse=True
        )

    if output_format.lower() == "table":
        print_requirements_table(result_data)
    elif output_format.lower() == "json":
        print(json.dumps(result_data, indent=2, ensure_ascii=False))

    if output_json_path:
        export_to_json(result_data, output_json_path)

    if output_md_path:
        export_to_markdown(result_data, output_md_path)

    return result_data


def print_requirements_table(data: Dict[str, Any]) -> None:
    """Print the analyzed criteria in a formatted, readable ASCII table."""
    project_title = data.get("project_title", "RFP Requirements Analysis")
    client = data.get("client_name", "N/A")
    summary = data.get("summary", "")
    criteria: List[Dict[str, Any]] = data.get("criteria", [])

    print("\n" + "=" * 95)
    print(f"  PROJECT: {project_title}  |  CLIENT: {client}")
    print("=" * 95)
    if summary:
        print(f"  Summary: {summary}")
        print("-" * 95)

    rows = []
    for c in criteria:
        score = c.get("score", c.get("priority_score", "-"))
        level = c.get("priority_level", f"{score}")
        score_display = f"[{score}/5] {level}"
        rows.append([
            c.get("id", "N/A"),
            c.get("title", ""),
            c.get("category", "General"),
            score_display,
            c.get("rationale", "")
        ])

    headers = ["ID", "Criterion / Requirement", "Category", "Score (1-5)", "Ranking Rationale"]

    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=headers, tablefmt="grid", maxcolwidths=[8, 24, 18, 18, 30]))
    except ImportError:
        col_widths = [8, 24, 18, 18, 32]
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
        print(header_line)
        print(separator)
        for r in rows:
            line = " | ".join(str(r[i])[:col_widths[i]].ljust(col_widths[i]) for i in range(len(headers)))
            print(line)

    print("\n" + "=" * 95)
    score_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for c in criteria:
        s = c.get("score", c.get("priority_score"))
        if s in score_counts:
            score_counts[s] += 1

    print("  PRIORITY DISTRIBUTION:")
    print(f"   * [5] Must-have:       {score_counts[5]} criteria")
    print(f"   * [4] High priority:   {score_counts[4]} criteria")
    print(f"   * [3] Medium priority: {score_counts[3]} criteria")
    print(f"   * [2] Low priority:    {score_counts[2]} criteria")
    print(f"   * [1] Nice to have:    {score_counts[1]} criteria")
    print(f"   ==> TOTAL CRITERIA:    {len(criteria)}")
    print("=" * 95 + "\n")


# =====================================================================
# CLI Entrypoint
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract and rank customer RFP requirements using Google Gemini API."
    )
    default_rfp = "rfp/rfp_nordframe.md"
    if not os.path.exists(default_rfp) and os.path.exists("../rfp/rfp_nordframe.md"):
        default_rfp = "../rfp/rfp_nordframe.md"

    parser.add_argument(
        "file_path",
        nargs="?",
        default=default_rfp,
        help=f"Path to customer requirements .md file (default: {default_rfp})",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["table", "json", "none"],
        default="table",
        help="Console display format (default: table)",
    )
    parser.add_argument(
        "--output-json",
        "-j",
        default=None,
        help="Path to export criteria JSON file (e.g. criterias_output.json)",
    )
    parser.add_argument(
        "--output-md",
        "-o",
        default=None,
        help="Path to export Markdown analysis file (e.g. criterias_analyze.md)",
    )
    parser.add_argument(
        "--model",
        "-m",
        default=None,
        help="Gemini model name override (e.g. gemini-3.5-flash-lite)",
    )

    args = parser.parse_args()

    try:
        extract_and_rank_criteria(
            rfp_file_path=args.file_path,
            output_format=args.format,
            output_json_path=args.output_json,
            output_md_path=args.output_md,
            model_name=args.model,
        )
    except Exception as err:
        print(f"\n[ERROR]: {err}", file=sys.stderr)
        sys.exit(1)
