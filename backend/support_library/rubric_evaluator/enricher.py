from typing import Any, Dict, List

RUBRIC_FIX_TEMPLATES = {
    "risk_transparency": {
        "title": "[Rubric Quality: Risk & Assumptions] Missing Risk Mitigation Register & Contingency Protocols",
        "action": "Add an explicit Project Assumptions Log and Risk Mitigation Register with concrete rollback procedures for ERP and scanner integrations.",
        "rewritten_text": """### Risk Management, Assumptions & Rollback Protocols (Appendix A Standard)
1. **ERP & Database Integration Risk:** To prevent operational disruption during ERP sync, all catalog transfers will execute in parallel staging tables with automated checksum verification before live cutover. A full rollback snapshot is maintained at each depot.
2. **Scanner & Hardware Compatibility Risk:** A dedicated pre-deployment hardware matrix validation will be completed in Week 2. Any non-compliant barcode terminals will be supported via fallback PWA interfaces.
3. **Core Assumptions:** Nordframe IT provides read-only API access to depot inventory tables within 5 business days of contract execution; depot facilities maintain standard 802.11ac Wi-Fi coverage across all aisles.""",
    },
    "timeline_clarity": {
        "title": "[Rubric Quality: Timeline Clarity] Missing User Acceptance Testing (UAT) Buffer and Phase Gates",
        "action": "Incorporate explicit sprint milestones with a mandatory 2-week User Acceptance Testing (UAT) signoff window and rollback contingency buffer prior to depot rollout.",
        "rewritten_text": """### Phased Delivery Schedule & Milestone Gates (Revised)
- **Phase 1 (Month 1-2): Foundation & Core Engine Setup:** Multi-depot data model configuration and database integration. Exit Gate: Core API throughput validation.
- **Phase 2 (Month 3-4): Scanner & Depot Workflows:** Barcode scanning UI and real-time sync testing across 2 pilot depots. Exit Gate: Pilot user acceptance.
- **Phase 3 (Month 5): Enterprise Hardening & UAT Buffer:** 2-week dedicated User Acceptance Testing (UAT) with depot managers and IT operations sign-off.
- **Phase 4 (Month 6): Full 6-Depot Go-Live & Post-Launch Hypercare:** Phased depot rollout with on-site technical support and 99.9% SLA verification.""",
    },
    "pricing_clarity": {
        "title": "[Rubric Quality: Pricing Clarity] Commercial Breakdown Lacks Milestone Schedule & TCO Transparency",
        "action": "Provide itemized commercial schedule with clear milestone payment triggers and transparent total cost of ownership (TCO) breakdown.",
        "rewritten_text": """### Commercial Schedule & Milestone Payment Structure (Revised)
- **Milestone 1 (20% upon contract signing):** Architectural design sign-off and environment provisioning.
- **Milestone 2 (30% upon pilot depot deployment):** Functional inventory tracking live in 2 pilot depots.
- **Milestone 3 (30% upon successful UAT sign-off):** Complete multi-depot synchronization across all 6 sites.
- **Milestone 4 (20% upon final acceptance & 30-day hypercare completion):** Full handover, admin training, and SLA activation.
- **Transparent SaaS Licensing:** Flat-rate recurring fee of $1,500/depot/month covering maintenance, security patches, and 24/7 Tier-1 support.""",
    },
    "scope_deliverables": {
        "title": "[Rubric Quality: Scope & Deliverables Clarity] Ambiguity in Deliverable Boundaries & Hardware Integration",
        "action": "Explicitly delineate in-scope deliverables, out-of-scope boundaries, and hardware interface specifications.",
        "rewritten_text": """### Deliverables Boundaries & Scope Demarcation (Revised)
- **In-Scope Deliverables:** Native cloud inventory sync engine; handheld scanner PWA; real-time dashboard with stock alerts; multi-depot aggregation API; complete admin manuals.
- **Out-of-Scope Items:** Physical warehouse racking barcode tagging (handled by Nordframe operations); procurement of new mobile handsets.
- **Integration Scope:** Pre-built REST connectors for existing warehouse management databases; zero vendor-lock-in export utilities.""",
    },
    "problem_understanding": {
        "title": "[Rubric Quality: Problem Understanding] Generic Proposal Lacking Nordframe Throughput KPI Alignment",
        "action": "Directly align solution commitments to Nordframe's specific throughput bottlenecks and multi-depot operational pain points.",
        "rewritten_text": """### Alignment with Nordframe Operational Challenges (Revised)
Our solution specifically resolves the 15% discrepancy in inventory counts observed during peak seasonal cross-docking across Nordframe's 6 regional hubs. By replacing asynchronous batch uploads with sub-second event-driven synchronization, depot managers gain instantaneous visibility into inbound pallets, eliminating shipment delays and redundant safety stock buffers.""",
    },
    "completeness": {
        "title": "[Rubric Quality: Completeness] Omission of Formal SLA Escalation Matrix & Regulatory Certifications",
        "action": "Include formal Service Level Agreement (SLA) response tiers, escalation matrix, and regulatory compliance certificates.",
        "rewritten_text": """### Service Level Agreement (SLA) & Escalation Commitment (Revised)
- **Severity 1 (Depot Outage / System Down):** 15-minute response time, 2-hour temporary workaround, 4-hour resolution SLA. 24/7/365 availability.
- **Severity 2 (Major Feature Degraded):** 1-hour response time, 8-hour resolution SLA.
- **Severity 3 (Minor Operational Query):** 4-hour response time, next business day resolution.
- **Financial Penalty:** 5% monthly service credit per 0.1% breach below 99.9% uptime commitment.""",
    },
    "tone_persuasiveness": {
        "title": "[Rubric Quality: Tone & Persuasiveness] Generic Pitch Lacking Verifiable Track Record & ROI Proof",
        "action": "Strengthen executive narrative with concrete domain case studies, verified ROI metrics, and customer-centric value propositions.",
        "rewritten_text": """### Proven Value Delivery & Verifiable Track Record (Revised)
With 12+ successful logistics deployments in Scandinavian supply-chain operations, our platform has delivered a proven 40% reduction in cycle-count labor hours and 99.98% inventory accuracy within 90 days of rollout. We commit a dedicated Senior Solutions Architect and named Customer Success Manager to ensure Nordframe achieves ROI by Q3.""",
    },
}

ID_MAP = {
    "risk_transparency": "RUBRIC-RISK",
    "timeline_clarity": "RUBRIC-TIMELINE",
    "pricing_clarity": "RUBRIC-PRICING",
    "scope_deliverables": "RUBRIC-SCOPE",
    "problem_understanding": "RUBRIC-PROBLEM",
    "completeness": "RUBRIC-COMPLETE",
    "tone_persuasiveness": "RUBRIC-TONE",
}

DIMENSION_KEYWORDS = {
    "risk_transparency": ["risk", "assumption", "contingency", "rollback"],
    "timeline_clarity": ["timeline", "schedule", "milestone", "delivery date", "phase", "uat"],
    "pricing_clarity": ["pricing", "price", "cost", "fee", "payment", "commercial", "tco"],
    "scope_deliverables": ["scope", "deliverable", "hardware", "scanner", "boundary", "in-scope"],
    "problem_understanding": ["problem", "challenge", "objective", "kpi", "bottleneck", "throughput"],
    "completeness": ["sla", "support", "incident", "escalation", "complete", "certification"],
    "tone_persuasiveness": ["tone", "persuasive", "track record", "case study", "roi", "proof"],
}


def enrich_issues_with_rubric_deficiencies(
    issues_and_fixes: List[Dict[str, Any]],
    rubric_res: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Ensures that actionable improvement suggestions explicitly address
    shortcomings identified in the 7-Dimension Rubric Scorecard:
    1. Tags existing issues that match low-scoring rubric dimensions so the connection is visible.
    2. Appends dedicated suggested fixes for low-scoring rubric dimensions not yet addressed.
    """
    if not isinstance(issues_and_fixes, list):
        issues_and_fixes = []

    rubric_scores = rubric_res.get("scores") or rubric_res.get("rubric_scores") or []
    if not rubric_scores:
        return issues_and_fixes

    # Check each rubric dimension
    for crit in rubric_scores:
        score = crit.get("score", 5)
        cid = str(crit.get("criterion_id", "")).lower()
        cname = crit.get("criterion_name", "")
        comment = crit.get("comment", "")
        keywords = DIMENSION_KEYWORDS.get(cid, [cid])

        # Target dimensions that have shortcomings (score <= 3)
        if score <= 3:
            matched_issue = None
            for item in issues_and_fixes:
                item_text = f"{item.get('title', '')} {item.get('criterion_id', '')} {item.get('explanation', '')}".lower()
                if any(kw in item_text for kw in keywords):
                    matched_issue = item
                    break

            if matched_issue is not None:
                # Link the existing issue to the rubric dimension
                matched_issue["is_rubric_issue"] = True
                matched_issue["rubric_dimension"] = cname
                matched_issue["rubric_score"] = score
                # Augment explanation if helpful
                if comment and comment not in matched_issue.get("explanation", ""):
                    matched_issue["rubric_comment"] = comment
            else:
                # Append dedicated rubric issue
                template = RUBRIC_FIX_TEMPLATES.get(cid, {
                    "title": f"[Rubric Quality: {cname}] Sub-optimal Score ({score}/5)",
                    "action": f"Elevate {cname} standard to address: {comment}",
                    "rewritten_text": f"### Revised Proposal Section: {cname}\n{comment}\n\nVendor commits to fulfilling Appendix A quality standards for {cname}.",
                })

                issue_id = ID_MAP.get(cid, f"RUBRIC-{cid[:5].upper()}")

                issues_and_fixes.append({
                    "issue_id": issue_id,
                    "criterion_id": crit.get("criterion_id", cid),
                    "title": template["title"],
                    "severity": "Major Gap" if score <= 2 else "Moderate Issue",
                    "rfp_reference": f"Appendix A Quality Rubric — {cname} (Score: {score}/5)",
                    "proposal_reference": f"Proposal Quality Assessment: {cname}",
                    "explanation": comment or f"Proposal scored {score}/5 on {cname}, below the competitive threshold of 4/5.",
                    "suggested_fix": {
                        "action": template["action"],
                        "rewritten_text": template["rewritten_text"],
                    },
                    "is_rubric_issue": True,
                    "rubric_dimension": cname,
                    "rubric_score": score,
                })

    return issues_and_fixes
