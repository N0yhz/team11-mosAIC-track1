"""Deterministic Level 3 scoring over the factual Level 2 scorecard."""

from typing import Any, Dict, Iterable, List

try:
    from .models import EvaluationStatus, Level3Result, PriorityChange
except ImportError:
    from models import EvaluationStatus, Level3Result, PriorityChange


STATUS_FACTORS = {
    EvaluationStatus.ADDRESSED.value: 1.0,
    EvaluationStatus.PARTIAL.value: 0.5,
    EvaluationStatus.UNVERIFIABLE.value: 0.25,
    EvaluationStatus.MISSING.value: 0.0,
    EvaluationStatus.CONTRADICTED.value: 0.0,
}

STATUS_RISK = {
    EvaluationStatus.CONTRADICTED.value: 5,
    EvaluationStatus.MISSING.value: 4,
    EvaluationStatus.UNVERIFIABLE.value: 3,
    EvaluationStatus.PARTIAL.value: 2,
    EvaluationStatus.ADDRESSED.value: 0,
}


def validate_evidence(row: Dict[str, Any], status: str) -> List[str]:
    proposal_evidence = row.get("proposal_evidence") or {}
    proposal_quote = str(proposal_evidence.get("quote", "")).strip()
    warnings: List[str] = []
    if status == EvaluationStatus.ADDRESSED.value and not proposal_quote:
        warnings.append("ADDRESSED_WITHOUT_PROPOSAL_EVIDENCE")
    if status == EvaluationStatus.CONTRADICTED.value and not proposal_quote:
        warnings.append("CONTRADICTION_WITHOUT_PROPOSAL_EVIDENCE")
    return warnings


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", " ").replace("-", " ")
    if text in {"addressed", "compliant", "fully addressed", "fully compliant"}:
        return EvaluationStatus.ADDRESSED.value
    if "partial" in text or "mostly compliant" in text:
        return EvaluationStatus.PARTIAL.value
    if "contradict" in text:
        return EvaluationStatus.CONTRADICTED.value
    if "unverif" in text or "unclear" in text:
        return EvaluationStatus.UNVERIFIABLE.value
    if "missing" in text or "non compliant" in text or "not compliant" in text:
        return EvaluationStatus.MISSING.value
    return EvaluationStatus.UNVERIFIABLE.value


def _criteria_by_id(criteria: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("id", "")).strip().upper(): item for item in criteria}


def _validate_inputs(criteria: Dict[str, Dict[str, Any]], scorecard: List[Dict[str, Any]], changes: List[PriorityChange]) -> None:
    criterion_ids = set(criteria)
    scorecard_ids = [str(row.get("criterion_id", "")).strip().upper() for row in scorecard]
    change_ids = [change.requirement_id.strip().upper() for change in changes]

    if not scorecard:
        raise ValueError("Level 2 scorecard must contain at least one criterion.")
    if not criteria:
        raise ValueError("Criteria report must contain at least one criterion.")
    if any(not identifier for identifier in scorecard_ids):
        raise ValueError("Every scorecard row must contain criterion_id.")
    if len(set(scorecard_ids)) != len(scorecard_ids):
        raise ValueError("Level 2 scorecard contains duplicate criterion_id values.")
    if len(set(change_ids)) != len(change_ids):
        raise ValueError("Priority changes contain duplicate requirement_id values.")

    unknown_changes = set(change_ids) - criterion_ids
    unknown_scorecard = set(scorecard_ids) - criterion_ids
    missing_scorecard = criterion_ids - set(scorecard_ids)
    if unknown_changes:
        raise ValueError(f"Priority changes reference unknown criteria: {sorted(unknown_changes)}")
    if unknown_scorecard:
        raise ValueError(f"Scorecard references unknown criteria: {sorted(unknown_scorecard)}")
    if missing_scorecard:
        raise ValueError(f"Scorecard is missing criteria: {sorted(missing_scorecard)}")
    invalid_priorities = [
        identifier for identifier, criterion in criteria.items()
        if criterion.get("priority_score", criterion.get("score", 3)) not in {1, 2, 3, 4, 5}
    ]
    if invalid_priorities:
        raise ValueError(f"Criteria have priorities outside 1-5: {sorted(invalid_priorities)}")
    invalid_changes = [
        change.requirement_id for change in changes
        if change.priority is not None and change.priority not in {1, 2, 3, 4, 5}
    ]
    if invalid_changes:
        raise ValueError(f"Priority changes outside 1-5: {sorted(invalid_changes)}")


def finalize_level3(evaluation: Dict[str, Any], changes: Iterable[PriorityChange]) -> Dict[str, Any]:
    raw_criteria = evaluation.get("criteria_report", {}).get("criteria", [])
    raw_ids = [str(item.get("id", "")).strip().upper() for item in raw_criteria]
    if len(set(raw_ids)) != len(raw_ids):
        raise ValueError("Criteria report contains duplicate criterion IDs.")
    criteria = _criteria_by_id(raw_criteria)
    feedback = evaluation.get("response_feedback", {})
    scorecard = feedback.get("scorecard", [])
    changes = list(changes)
    _validate_inputs(criteria, scorecard, changes)
    confirmed = {change.requirement_id.strip().upper(): change for change in changes}
    final_rows: List[Dict[str, Any]] = []

    for row in scorecard:
        requirement_id = str(row.get("criterion_id", "")).strip().upper()
        criterion = criteria.get(requirement_id, {})
        change = confirmed.get(requirement_id)
        suggested_priority = int(criterion.get("priority_score", criterion.get("score", 3)))
        priority = change.priority if change and change.priority is not None else suggested_priority
        hard_gate = change.hard_gate if change and change.hard_gate is not None else bool(criterion.get("hard_gate", False))
        status = normalize_status(row.get("status"))
        validation_warnings = validate_evidence(row, status)
        final_rows.append({
            **row,
            "criterion_id": requirement_id,
            "status": status,
            "suggested_priority": suggested_priority,
            "confirmed_priority": int(priority),
            "priority_changed": int(priority) != suggested_priority,
            "priority_score": int(priority),
            "hard_gate": hard_gate,
            "factor": STATUS_FACTORS[status],
            "weighted_contribution": round(int(priority) * STATUS_FACTORS[status], 2),
            "validation_warnings": validation_warnings,
        })

    total_weight = sum(row["priority_score"] for row in final_rows)
    earned = sum(row["priority_score"] * row["factor"] for row in final_rows)
    score = round(earned / total_weight * 100) if total_weight else 0
    deal_breakers = [
        row for row in final_rows
        if row["hard_gate"] and row["status"] in {
            EvaluationStatus.MISSING.value,
            EvaluationStatus.CONTRADICTED.value,
        }
    ]
    hard_gate_clarifications = [
        row for row in final_rows
        if row["hard_gate"] and row["status"] in {
            EvaluationStatus.PARTIAL.value,
            EvaluationStatus.UNVERIFIABLE.value,
        }
    ]
    ranked_issues = sorted(
        [row for row in final_rows if row["status"] != EvaluationStatus.ADDRESSED.value],
        key=lambda row: (
            not row["hard_gate"],
            -row["priority_score"],
            -STATUS_RISK[row["status"]],
            row["criterion_id"],
        ),
    )

    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B+"
    elif score >= 70:
        grade = "B-"
    elif score >= 60:
        grade = "C"
    else:
        grade = "D"

    if deal_breakers:
        recommendation = "Reject or Require Critical Clarifications (Hard Gate Failed)"
        readiness = "not_ready"
    elif hard_gate_clarifications:
        recommendation = "Require Critical Clarifications (Hard Gate Evidence Pending)"
        readiness = "needs_critical_clarification"
    else:
        recommendation = (
            "Accept / Top Candidate" if score >= 90
            else "Shortlist (Strong Candidate)" if score >= 80
            else "Shortlist with Minor Clarifications" if score >= 70
            else "Marginal Candidate" if score >= 60
            else "Reject"
        )
        readiness = "ready" if score >= 90 else "conditionally_ready" if score >= 60 else "not_ready"

    return Level3Result(
        score=score,
        grade=grade,
        recommendation=recommendation,
        readiness=readiness,
        hard_gate_failed=bool(deal_breakers),
        hard_gate_pending=bool(hard_gate_clarifications),
        deal_breakers=deal_breakers,
        hard_gate_clarifications=hard_gate_clarifications,
        ranked_issues=ranked_issues,
        scorecard=final_rows,
    ).model_dump()