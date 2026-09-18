"""
support_library package
Unified support modules for RFP criteria extraction, description adaptation, and proposal feedback evaluation.
"""

from .criterias_extractor import (
    criteria_extractor,
    extract_and_rank_criteria,
    adapt_criteria_descriptions,
    print_requirements_table,
    export_to_json,
    export_to_markdown,
)
from .lvl2_feedback_response import (
    lvl2_feedback_response,
)

__all__ = [
    "criteria_extractor",
    "extract_and_rank_criteria",
    "adapt_criteria_descriptions",
    "print_requirements_table",
    "export_to_json",
    "export_to_markdown",
    "lvl2_feedback_response",
]

from .extractors import (
    DocumentSection,
    ExtractedDocument,
    convert_to_markdown,
    extract_csv,
    extract_excel,
    extract_file,
    extract_markdown,
    extract_pdf,
    extract_text,
)


from .rubric_evaluator import evaluate_rubric_score, DEFAULT_RUBRIC_CRITERIA, ScoringResult, CriterionScore
