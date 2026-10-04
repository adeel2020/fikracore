"""
RCA Confirmation & Hypothesis Validation Rules (§22)
====================================================
RULE-RCA-001: Enforces that no hypothesis is confirmed as Root Cause without
active discrimination probe proof, absence of contradictory evidence, and confidence >= 70%.
"""

from .base import RuntimeRuleContract


RULE_RCA_001 = RuntimeRuleContract(
    rule_id="RULE-RCA-001",
    rule_version="1.0.0",
    rule_type="CAUSAL_VALIDATION",
    name="Root Cause Confirmation Gate",
    description="Enforces that hypothesis confirmation as Root Cause requires empirical probe proof and zero unresolved contradictions.",
    applies_to=["InvestigationHypothesis", "Hypothesis", "RankedHypothesisItem"],
    trigger={"lifecycle": ["CONFIRMED", "LEADING"]},
    scope={"domains": ["*"]},
    preconditions=[
        {
            "field": "status",
            "operator": "==",
            "value": "CONFIRMED",
        }
    ],
    checks=[
        {
            "check_id": "CHK-RCA-PROBE",
            "field": "has_supporting_probes",
            "operator": "is_true",
            "value": True,
            "failure_severity": "BLOCK",
            "failure_message": "Cannot declare Root Cause without empirical discrimination probe confirmation.",
        },
        {
            "check_id": "CHK-RCA-NO-CONTRADICTION",
            "field": "contradictory_evidence_count",
            "operator": "<=",
            "value": 0,
            "failure_severity": "BLOCK",
            "failure_message": "Cannot declare Root Cause while contradictory evidence remains unresolved.",
        },
        {
            "check_id": "CHK-RCA-CONFIDENCE",
            "field": "confidence",
            "operator": ">=",
            "value": 70.0,
            "failure_severity": "WARN",
            "failure_message": "Confidence is below 70% threshold for confirmed root cause.",
        },
    ],
    decision_map={
        "PASS": "ALLOW_CONFIRMED_FINDING",
        "WARN": "RETAIN_AS_LEADING_HYPOTHESIS",
        "BLOCK": "PREVENT_RCA_CONFIRMATION",
    },
    priority=10,
    owner="telecom_architecture",
    provenance="3gpp_root_cause_standard",
)
