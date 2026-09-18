"""7-Dimension Quality Rubric Scorer (Appendix A).

Independent quality dimension scoring:
1. Problem Understanding
2. Scope & Deliverables Clarity
3. Pricing Clarity
4. Timeline Clarity
5. Completeness
6. Tone & Persuasiveness
7. Risk / Assumptions Transparency
"""

from .models import Criterion, CriterionScore, ScoringResult
from .criteria import DEFAULT_RUBRIC_CRITERIA
from .scorer import evaluate_rubric_score

__all__ = [
    "Criterion",
    "CriterionScore",
    "ScoringResult",
    "DEFAULT_RUBRIC_CRITERIA",
    "evaluate_rubric_score",
]

from .enricher import enrich_issues_with_rubric_deficiencies

__all__ = list(__all__) + ['enrich_issues_with_rubric_deficiencies']
