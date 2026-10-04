"""
Unit Tests for FikraCore Declarative Runtime Rules Engine
=========================================================
Tests:
1. Rule registration, priority ordering, and query in RuleRegistry.
2. Context-aware rule filtering in RuleSelector.
3. Expression check evaluation in GenericRuleEvaluator.
4. Precedence resolution: BLOCK > WARN > PASS.
5. RULE-RCA-001 Root Cause Confirmation Gate.
6. RULE-SAFETY-001 Disruptive Action HITL Gate.
"""

import pytest

from engine_stack.engines.telecom_brain.investigation.runtime_rules import (
    RuleDecision,
    RuleEvaluationResult,
    RuntimeRuleContract,
    RuleRegistry,
    RuleSelector,
    GenericRuleEvaluator,
    RULE_RCA_001,
    RULE_SAFETY_001,
)


def test_rule_registry_and_ordering():
    """Verify registry stores rules and sorts by priority."""
    reg = RuleRegistry()
    r1 = RuntimeRuleContract(
        rule_id="R-LOW",
        rule_type="GENERAL",
        name="Low Priority Rule",
        description="test",
        priority=100,
    )
    r2 = RuntimeRuleContract(
        rule_id="R-HIGH",
        rule_type="GENERAL",
        name="High Priority Rule",
        description="test",
        priority=10,
    )
    reg.register_rule(r1)
    reg.register_rule(r2)

    rules = reg.list_rules()
    assert len(rules) == 2
    assert rules[0].rule_id == "R-HIGH"
    assert rules[1].rule_id == "R-LOW"


def test_rule_selector_filters_by_lifecycle_and_domain():
    """Verify selector filters rules based on target contract, domain, and lifecycle."""
    reg = RuleRegistry()
    reg.register_rule(RULE_RCA_001)
    reg.register_rule(RULE_SAFETY_001)

    selector = RuleSelector(reg)

    # Hypothesis with CONFIRMED status should match RULE_RCA_001
    matched = selector.select_rules(
        contract_type="InvestigationHypothesis",
        lifecycle_state="CONFIRMED",
    )
    assert any(r.rule_id == "RULE-RCA-001" for r in matched)
    assert not any(r.rule_id == "RULE-SAFETY-001" for r in matched)

    # Action with REMEDIATION should match RULE_SAFETY_001
    matched_action = selector.select_rules(
        contract_type="Action",
        action_type="REMEDIATION",
    )
    assert any(r.rule_id == "RULE-SAFETY-001" for r in matched_action)
    assert not any(r.rule_id == "RULE-RCA-001" for r in matched_action)


def test_rca_rule_blocks_without_probe():
    """Verify RULE-RCA-001 blocks hypothesis confirmation without discrimination probe proof."""
    evaluator = GenericRuleEvaluator()

    hyp_untested = {
        "hypothesis_id": "HYP-001",
        "status": "CONFIRMED",
        "has_supporting_probes": False,
        "contradictory_evidence_count": 0,
        "confidence": 85.0,
    }

    res = evaluator.evaluate_rule(
        rule=RULE_RCA_001,
        subject_id="HYP-001",
        subject_type="InvestigationHypothesis",
        subject_data=hyp_untested,
    )
    assert res.decision == RuleDecision.BLOCK
    assert "CHK-RCA-PROBE" in res.structured_reason_codes


def test_rca_rule_passes_with_probe_and_high_confidence():
    """Verify RULE-RCA-001 passes when probe is confirmed and no contradictions exist."""
    evaluator = GenericRuleEvaluator()

    hyp_validated = {
        "hypothesis_id": "HYP-001",
        "status": "CONFIRMED",
        "has_supporting_probes": True,
        "contradictory_evidence_count": 0,
        "confidence": 88.0,
    }

    res = evaluator.evaluate_rule(
        rule=RULE_RCA_001,
        subject_id="HYP-001",
        subject_type="InvestigationHypothesis",
        subject_data=hyp_validated,
    )
    assert res.decision == RuleDecision.PASS
    assert "ALL_CHECKS_PASSED" in res.structured_reason_codes


def test_safety_rule_blocks_autonomous_disruptive_action():
    """Verify RULE-SAFETY-001 blocks autonomous disruptive action without HITL approval."""
    evaluator = GenericRuleEvaluator()

    action = {
        "id": "ACT-001",
        "action_type": "REMEDIATION",
        "is_autonomous_attempt": True,
        "has_hitl_approval": False,
        "within_maintenance_window": True,
    }

    res = evaluator.evaluate_rule(
        rule=RULE_SAFETY_001,
        subject_id="ACT-001",
        subject_type="Action",
        subject_data=action,
    )
    assert res.decision == RuleDecision.BLOCK
    assert "CHK-HITL-APPROVAL" in res.structured_reason_codes


def test_evaluator_precedence_block_overrides_warn_and_pass():
    """Verify deterministic conflict resolution: if one rule blocks, overall decision is BLOCK."""
    reg = RuleRegistry()
    r_pass = RuntimeRuleContract(
        rule_id="R-PASS",
        rule_type="TEST",
        name="Passing Rule",
        description="test",
        applies_to=["Action"],
        checks=[{"field": "foo", "operator": "==", "value": 1, "failure_severity": "BLOCK"}],
    )
    r_warn = RuntimeRuleContract(
        rule_id="R-WARN",
        rule_type="TEST",
        name="Warning Rule",
        description="test",
        applies_to=["Action"],
        checks=[{"field": "bar", "operator": "==", "value": 99, "failure_severity": "WARN"}],
    )
    r_block = RuntimeRuleContract(
        rule_id="R-BLOCK",
        rule_type="TEST",
        name="Blocking Rule",
        description="test",
        applies_to=["Action"],
        checks=[{"field": "baz", "operator": "==", "value": 99, "failure_severity": "BLOCK"}],
    )
    reg.register_rule(r_pass)
    reg.register_rule(r_warn)
    reg.register_rule(r_block)

    evaluator = GenericRuleEvaluator(RuleSelector(reg))
    subject = {"foo": 1, "bar": 0, "baz": 0}  # r_pass passes, r_warn warns, r_block blocks

    decision, evals = evaluator.evaluate_all(
        subject_id="ACT-001",
        subject_type="Action",
        subject=subject,
    )
    assert decision == RuleDecision.BLOCK
    assert len(evals) == 3
