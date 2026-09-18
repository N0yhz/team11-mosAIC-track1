from __future__ import annotations
from typing import List
from .models import Criterion


DEFAULT_RUBRIC_CRITERIA: List[Criterion] = [
    Criterion(
        id="problem_understanding",
        name="Problem Understanding",
        definition="Does the proposal demonstrate a clear understanding of the customer's problem?",
        anchor_low="Generic boilerplate phrases, no reference to the specific problem",
        anchor_high="Precise description of the specific customer context and problem",
    ),
    Criterion(
        id="scope_deliverables",
        name="Scope & Deliverables Clarity",
        definition="Are services and deliverables concretely defined?",
        anchor_low="Vague feature list without substance",
        anchor_high="Clearly delineated, tangible deliverables",
    ),
    Criterion(
        id="pricing_clarity",
        name="Pricing Clarity",
        definition="Is pricing clearly communicated and structured?",
        anchor_low="Completely deferred or omitted",
        anchor_high="Clear figures, breakdown, or pricing structure",
    ),
    Criterion(
        id="timeline_clarity",
        name="Timeline Clarity",
        definition="Are schedules, deadlines, and milestones concretely specified?",
        anchor_low="No dates, schedule, or milestones provided",
        anchor_high="Concrete timelines, phases, and milestones",
    ),
    Criterion(
        id="completeness",
        name="Completeness",
        definition="Does the proposal appear complete and comprehensive?",
        anchor_low="Obvious gaps, missing sections, or unresolved points",
        anchor_high="Comprehensive and covers all required aspects",
    ),
    Criterion(
        id="tone_persuasiveness",
        name="Tone & Persuasiveness",
        definition="Is the tone persuasive, professional, and tailored to the client?",
        anchor_low="Generic boilerplate with little relevance",
        anchor_high="Tailored, engaging, and highly persuasive",
    ),
    Criterion(
        id="risk_transparency",
        name="Risk/Assumptions Transparency",
        definition="Are project risks, dependencies, and assumptions transparently disclosed?",
        anchor_low="Nothing disclosed; ignores potential risks",
        anchor_high="Risks and assumptions are clearly identified and mitigated",
    ),
]
