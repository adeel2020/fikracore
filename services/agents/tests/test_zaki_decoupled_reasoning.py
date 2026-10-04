"""Tests for Task-Agnostic Zaki NOC SME Reasoning & 3-Tier Progressive Disclosure.

Verifies:
1. Hub-and-Spoke Delegation Manager & DelegationRequest lifecycle.
2. 3-Tier Progressive Disclosure Presentation (Headline -> Telecom Rationale -> Collapsible Audit Trace).
3. Cognitive Ledger Integration (OperationalContext scaffolding, TaskEpisode runtime_evaluations).
4. Simulation Action Execution with Dynamic Safety Rule Enforcement.
"""

from pathlib import Path
from typing import Any, Dict

import pytest

from zaki.operations.delegation import DelegationManager, DelegationRequest
from zaki.storyteller.presentation import format_rule_explanation_for_operator
from engine_stack.engines.telecom_brain.investigation.runtime_rules import (
    RuleDecision,
    RuleEvaluationResult,
    GenericRuleEvaluator,
)
from engine_stack.engines.telecom_brain.simulator.story_compiler import compile_story_context
from engine_stack.engines.telecom_brain.simulator.simulation_manager import SimulationManager


# ----------------------------------------------------------------------
# 1. Delegation Manager & Hub-and-Spoke Tests
# ----------------------------------------------------------------------

def test_delegation_lifecycle():
    """Verify Zaki NOC Lead can dispatch, track, and complete structured delegations."""
    mgr = DelegationManager()

    # 1. Dispatch delegation to spoke domain agent
    req = mgr.create_delegation_request(
        delegation_id="DEL-TEST-001",
        target_domain="IP_TRANSPORT",
        target_entity="PE21",
        objective="Execute optical power level check and interface flapping diagnostic",
        originating_task_id="TASK-RUN-001",
        safety_ceiling="READ_ONLY_DIAGNOSTIC",
    )

    assert req.delegation_id == "DEL-TEST-001"
    assert req.target_domain == "IP_TRANSPORT"
    assert req.status == "ACTIVE"

    # 2. Retrieve delegation
    fetched = mgr.get_delegation("DEL-TEST-001")
    assert fetched is not None
    assert fetched.target_entity == "PE21"

    # 3. List delegations by task
    task_dels = mgr.list_delegations(originating_task_id="TASK-RUN-001")
    assert len(task_dels) == 1
    assert task_dels[0].delegation_id == "DEL-TEST-001"

    # 4. Complete delegation with spoke findings
    completed = mgr.complete_delegation(
        delegation_id="DEL-TEST-001",
        result_summary="Rx optical power degraded to -28.4 dBm on TenGigE0/0/0/1; high FEC uncorrectable count.",
    )
    assert completed is not None
    assert completed.status == "COMPLETED"
    assert "optical power" in (completed.result_summary or "")


# ----------------------------------------------------------------------
# 2. 3-Tier Progressive Disclosure Presentation Tests
# ----------------------------------------------------------------------

def test_3tier_presentation_block_decision():
    """Verify 3-Tier Progressive Presentation produces human NOC rationale and collapsible audit."""
    eval_result = RuleEvaluationResult(
        rule_id="RULE-SAFETY-001",
        rule_version="1.0.0",
        subject_id="ACT-001",
        subject_type="AgentActionContract",
        episode_id="EPISODE-101",
        decision=RuleDecision.BLOCK,
        reason="Autonomous execution of disruptive action ACT-001 is prohibited without Level 4 HITL operator authorization.",
        structured_reason_codes=["SAFETY_TIER_VIOLATION"],
        checks_evaluated=[
            {
                "check_id": "CHK-SAFETY-001A",
                "passed": False,
                "actual": "DISRUPTIVE_ACTIVE_PROBE",
                "expected": ["READ_ONLY_DIAGNOSTIC", "PASSIVE_TELEMETRY"],
            }
        ],
    )

    presentation = format_rule_explanation_for_operator(eval_result)

    # Tier 1: Actionable Headline badge
    assert presentation["tier_1_headline"] == "[ 🛡️ Operator Authorization Required ]"

    # Tier 2: Natural Telecom SME Rationale (not robotic code dump)
    assert "Level 4 SME authorization" in presentation["tier_2_rationale"]
    assert "ACT-001" in presentation["tier_2_rationale"]

    # Tier 3: Collapsible Technical Audit Trace
    audit = presentation["tier_3_audit"]
    assert audit["rule_id"] == "RULE-SAFETY-001"
    assert audit["decision"] == "BLOCK"
    assert audit["checks_count"] == 1
    assert audit["checks"][0]["actual"] == "DISRUPTIVE_ACTIVE_PROBE"


def test_3tier_presentation_rca_block():
    """Verify 3-Tier Progressive Presentation for RCA confirmation block."""
    eval_result = RuleEvaluationResult(
        rule_id="RULE-RCA-001",
        rule_version="1.0.0",
        subject_id="HYP-001",
        subject_type="HypothesisRankingContract",
        episode_id="EPISODE-102",
        decision=RuleDecision.BLOCK,
        reason="Hypothesis HYP-001 cannot be confirmed without discrimination probe.",
        checks_evaluated=[
            {
                "check_id": "CHK-RCA-001B",
                "passed": False,
                "actual": 0,
                "expected": 1,
            }
        ],
    )

    presentation = format_rule_explanation_for_operator(eval_result)
    assert presentation["tier_1_headline"] == "[ 🛡️ Operator Authorization Required ]"
    assert "cannot be promoted to Confirmed Root Cause without empirical proof" in presentation["tier_2_rationale"]
    assert presentation["tier_3_audit"]["rule_id"] == "RULE-RCA-001"


def test_3tier_presentation_pass_decision():
    """Verify 3-Tier Progressive Presentation for passed rules."""
    eval_result = RuleEvaluationResult(
        rule_id="RULE-SAFETY-001",
        rule_version="1.0.0",
        subject_id="ACT-001",
        subject_type="AgentActionContract",
        decision=RuleDecision.PASS,
        reason="Safety checks passed with Level 4 HITL sign-off.",
    )

    presentation = format_rule_explanation_for_operator(eval_result)
    assert presentation["tier_1_headline"] == "[ ✅ Policy Evaluation Verified ]"
    assert "Safety verification confirmed" in presentation["tier_2_rationale"]
    assert presentation["tier_3_audit"]["decision"] == "PASS"


# ----------------------------------------------------------------------
# 3. Cognitive Ledger & Operational Scaffolding Integration Tests
# ----------------------------------------------------------------------

def test_story_compiler_populates_cognitive_ledger():
    """Verify compile_story_context populates delegations, approvals, impact, and runtime_evaluations."""
    runs_dir = Path(__file__).parent.parent / "src/engine_stack/engines/telecom_brain/simulator/runs"
    matches = list(runs_dir.glob("RUN-SCN-001*"))
    assert len(matches) > 0, "Expected at least one SCN-001 run directory"
    run_dir = matches[0]

    # Test at Stage 6 (Validation / HITL gate)
    story = compile_story_context(run_dir, stage_index=6)

    # 1. Operational Context Envelope verification
    op_ctx = story.get("operational_context")
    assert op_ctx is not None

    # Delegations across domain spoke agents
    assert "active_delegations" in op_ctx
    assert len(op_ctx["active_delegations"]) >= 1
    assert op_ctx["active_delegations"][0]["target_domain"] in {"IP_TRANSPORT", "TRANSPORT"}

    # Pending approvals for Level 4 HITL
    assert "pending_approvals" in op_ctx
    assert len(op_ctx["pending_approvals"]) >= 1
    assert op_ctx["pending_approvals"][0]["required_authority"] == "LEVEL_4_HITL"
    assert op_ctx["pending_approvals"][0]["status"] == "PENDING"

    # Impact summary (telecom business & network impact)
    assert "impact_summary" in op_ctx
    assert "affected_nodes" in op_ctx["impact_summary"]
    assert op_ctx["impact_summary"]["severity"] == "CRITICAL"

    # 2. Task Episode Cognitive Ledger verification
    task_ep = story.get("task_episode")
    assert task_ep is not None

    # Finding references
    assert "finding_refs" in task_ep
    assert len(task_ep["finding_refs"]) >= 1

    # Delegated task references
    assert "delegated_task_refs" in task_ep
    assert len(task_ep["delegated_task_refs"]) >= 1

    # Runtime evaluations ledger
    assert "runtime_evaluations" in task_ep
    evals = task_ep["runtime_evaluations"]
    assert len(evals) >= 1
    rule_ids = {e.get("rule_id") for e in evals}
    assert "RULE-SAFETY-001" in rule_ids


# ----------------------------------------------------------------------
# 4. Action Execution with Dynamic Safety Gating
# ----------------------------------------------------------------------

def test_simulation_manager_action_safety_audit():
    """Verify execute_action runs RULE-SAFETY-001 and records rule_evaluation."""
    mgr = SimulationManager()
    run = mgr.create_run(scenario_id="SCN-001")

    # Execute a diagnostic probe
    res = mgr.execute_action(run.run_id, "NBA-001", advance=False)
    assert res["status"] == "SUCCESS"
    assert "rule_evaluation" in res
    eval_dict = res["rule_evaluation"]
    assert eval_dict["rule_id"] == "RULE-SAFETY-001"
    assert eval_dict["decision"] == "PASS"  # NBA-001 is diagnostic, passes safety check
