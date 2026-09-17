"""
criterias_extractor package
Extract and rank RFP criteria using Google Gemini API.
"""

from typing import Optional
from .extract_criteria import (
    extract_and_rank_criteria,
    print_requirements_table,
    export_to_json,
    export_to_markdown,
)
from .adapt_descriptions import adapt_criteria_descriptions

def criteria_extractor(
    rfp_file: str,
    output_file: str = "criteria.json",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
):
    """Alias function: extracts criteria from an RFP and saves to a JSON file."""
    return extract_and_rank_criteria(
        rfp_file_path=rfp_file,
        output_format="none",
        output_json_path=output_file,
        model_name=model_name,
        api_key=api_key,
    )

__all__ = [
    "extract_and_rank_criteria",
    "criteria_extractor",
    "print_requirements_table",
    "export_to_json",
    "export_to_markdown",
    "adapt_criteria_descriptions",
]
