"""
Operational Action & Safety Rules
=================================
RULE-SAFETY-001: Enforces that disruptive remediation actions (traffic rerouting,
link resets, isolation) require explicit Human-in-the-Loop (Level 4) authorization.
"""

from .base import RuntimeRuleContract


RULE_SAFETY_001 = RuntimeRuleContract(
    rule_id="RULE-SAFETY-001",
    rule_version="1.0.0",
    rule_type="SAFETY",
    name="Disruptive Action HITL Gate",
    description="Prohibits autonomous execution of traffic-affecting or configuration-altering operations without human SME signoff.",
    applies_to=["Action", "ActionContract", "NextBestAction", "Playbook"],
    trigger={
        "action_type": ["REMEDIATION", "TRAFFIC_REROUTE", "DISRUPTIVE_ACTIVE_PROBE", "WRITE_CONFIGURATION"]
    },
    scope={"domains": ["*"]},
    preconditions=[
        {
            "field": "is_autonomous_attempt",
            "operator": "is_true",
            "value": True,
        }
    ],
    checks=[
        {
            "check_id": "CHK-HITL-APPROVAL",
            "field": "has_hitl_approval",
            "operator": "is_true",
            "value": True,
            "failure_severity": "BLOCK",
            "failure_message": "Action is traffic-disruptive and requires explicit Level 4 Human SME sign-off.",
        },
        {
            "check_id": "CHK-CHANGE-WINDOW",
            "field": "within_maintenance_window",
            "operator": "is_true",
            "value": True,
            "failure_severity": "WARN",
            "failure_message": "Action is scheduled outside active maintenance window.",
        },
    ],
    decision_map={
        "PASS": "ALLOW_EXECUTION",
        "WARN": "PROCEED_WITH_MAINTENANCE_WARNING",
        "BLOCK": "REQUIRE_HITL_AUTHORIZATION",
    },
    priority=5,
    owner="telecom_governance",
    provenance="itil_change_management",
)
