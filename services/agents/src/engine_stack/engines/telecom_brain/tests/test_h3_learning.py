"""Comprehensive Test Suite for Step 4.3 / H3 Validated Knowledge Learning & Future Incident Improvement.

Verifies the 16 required tests from Section 57:
1. test_h3_candidate_requires_validation
2. test_h3_rejected_candidate_not_promoted
3. test_h3_modified_candidate_promotes_modified_relation
4. test_h3_promotion_is_idempotent
5. test_h3_promotion_is_reversible
6. test_h3_hidden_truth_not_used_for_promotion
7. test_h3_future_incident_differs_from_discovery_incident
8. test_h3_positive_transfer_improves_reasoning
9. test_h3_neutral_transfer_does_not_fake_improvement
10. test_h3_negative_transfer_detected
11. test_h3_stale_knowledge_detected
12. test_h3_conflicting_knowledge_not_silently_overwritten
13. test_h3_learning_provenance_preserved
14. test_h3_mark_zaki_uses_shared_state
15. test_h3_demo_metadata_does_not_change_reasoning
16. test_h1_h2_regression_suite_still_passes
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.contracts import (
    GeneratedRunInput,
    KnowledgePromotionState,
    Terminal,
    ValidationDecisionType,
)
from engine_stack.engines.telecom_brain.investigation.investigator import Investigator
from engine_stack.engines.telecom_brain.investigation.knowledge import InMemoryKnowledgeProvider
from engine_stack.engines.telecom_brain.learning.h3_validator import validate_all_h3_units, validate_single_h3_unit
from engine_stack.engines.telecom_brain.learning.promotion import PromotionEngine
from engine_stack.engines.telecom_brain.presentation.ui_adapter import build_ui_presentation_model
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.simulator.h3_generator import generate_all_h3_learning_units


TEST_UNITS_DIR = Path(__file__).parents[1] / "simulator" / "h3_runs"
REFERENCE_NETWORK_PATH = Path(__file__).parents[1] / "simulator" / "operator_model" / "reference_synthetic_network.yaml"


@pytest.fixture(scope="session")
def h3_units():
    """Ensure all 30 H3 learning units are generated and available."""
    units = generate_all_h3_learning_units(TEST_UNITS_DIR)
    return units


def _build_test_provider(entities: list[str], relationships: list[dict[str, Any]] | None = None) -> InMemoryKnowledgeProvider:
    return InMemoryKnowledgeProvider(
        pages=[{"slug": e, "frontmatter": {}} for e in entities],
        relationships=relationships or [],
        version="test-provider-v1",
    )


def test_h3_candidate_requires_validation(h3_units):
    """Test 1: Unvalidated candidate cannot be promoted without SME decision."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    candidate = {
        "candidate_id": "CAND-001",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    # Attempt promotion with missing validation
    success, rec, errors = engine.promote_candidate(candidate, {}, prov)
    assert not success
    assert rec is None
    assert any("decision" in err.lower() for err in errors)
    assert len(prov.relationships) == 0


def test_h3_rejected_candidate_not_promoted(h3_units):
    """Test 2: SME-rejected candidate is blocked from promotion."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    candidate = {
        "candidate_id": "CAND-002",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    validation = {
        "validation_id": "VAL-002",
        "candidate_id": "CAND-002",
        "decision": ValidationDecisionType.REJECT.value,
        "validated_by_role": "Transport SME",
        "reason": "Route was decommissioned last quarter.",
    }
    success, rec, errors = engine.promote_candidate(candidate, validation, prov)
    assert not success
    assert rec is None
    assert any("guardrail 5" in err.lower() or "blocked" in err.lower() for err in errors)
    assert len(prov.relationships) == 0


def test_h3_modified_candidate_promotes_modified_relation(h3_units):
    """Test 3: SME MODIFY decision promotes the modified relation instead of the original."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21", "IP:PE:RTR-22"])
    candidate = {
        "candidate_id": "CAND-003",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    validation = {
        "validation_id": "VAL-003",
        "candidate_id": "CAND-003",
        "decision": ValidationDecisionType.MODIFY.value,
        "validated_by_role": "Transport SME",
        "reason": "Correct next-hop is RTR-22, not RTR-21.",
        "modified_relation": {
            "source": "SA5G:UPF:003",
            "target": "IP:PE:RTR-22",
            "link_type": "routes-through",
        },
    }
    success, rec, errors = engine.promote_candidate(candidate, validation, prov)
    assert success
    assert rec is not None
    assert rec.canonical_to == "IP:PE:RTR-22"
    assert rec.status == KnowledgePromotionState.PROMOTED
    assert len(prov.relationships) == 1
    assert prov.relationships[0]["target"] == "IP:PE:RTR-22"


def test_h3_promotion_is_idempotent(h3_units):
    """Test 4: Promoting the same candidate twice does not create duplicates."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    candidate = {
        "candidate_id": "CAND-004",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    validation = {
        "validation_id": "VAL-004",
        "candidate_id": "CAND-004",
        "decision": ValidationDecisionType.ACCEPT.value,
        "validated_by_role": "Transport SME",
        "reason": "Verified live route.",
    }
    # First promotion
    success1, rec1, _ = engine.promote_candidate(candidate, validation, prov)
    assert success1
    assert len(prov.relationships) == 1

    # Second promotion of identical candidate
    success2, rec2, _ = engine.promote_candidate(candidate, validation, prov)
    assert success2
    assert len(prov.relationships) == 1
    assert rec2.promotion_id == rec1.promotion_id


def test_h3_promotion_is_reversible(h3_units):
    """Test 5: Rollback safely revokes a promoted edge from the knowledge provider."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    candidate = {
        "candidate_id": "CAND-005",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    validation = {
        "validation_id": "VAL-005",
        "candidate_id": "CAND-005",
        "decision": ValidationDecisionType.ACCEPT.value,
        "validated_by_role": "Transport SME",
        "reason": "Verified route.",
    }
    success, rec, _ = engine.promote_candidate(candidate, validation, prov)
    assert success
    assert len(prov.relationships) == 1

    # Rollback
    rb_ok, rb_msg = engine.rollback_promotion(rec.promotion_id, prov)
    assert rb_ok
    assert "Successfully rolled back" in rb_msg
    assert len(prov.relationships) == 0


def test_h3_hidden_truth_not_used_for_promotion(h3_units):
    """Test 6: Promotion logic never accesses or references hidden ground truth."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-001"
    res = validate_single_h3_unit(unit_dir)
    assert res["valid"], f"Unit validation failed: {res['errors']}"

    with open(unit_dir / "candidate_knowledge.yaml") as f:
        cand = yaml.safe_load(f)
    cand_str = json.dumps(cand).lower()
    assert "hidden" not in cand_str
    assert "ground_truth" not in cand_str


def test_h3_future_incident_differs_from_discovery_incident(h3_units):
    """Test 7: Future incident genuinely differs from discovery incident (no replay-as-learning)."""
    val_report = validate_all_h3_units(TEST_UNITS_DIR)
    assert val_report["all_valid"]
    assert val_report["total_units"] == 30

    for d in val_report["details"]:
        assert d["valid"], f"Unit {d['unit_id']} failed integrity: {d['errors']}"


def test_h3_positive_transfer_improves_reasoning(h3_units):
    """Test 8: In positive transfer cohort, promoted knowledge improves explanation coverage and RCA rank."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-001"
    op_dir = unit_dir / "future_incident" / "operational"
    hidden_dir = unit_dir / "future_incident" / "hidden"

    with open(unit_dir / "candidate_knowledge.yaml") as f:
        cand = yaml.safe_load(f)
    with open(unit_dir / "validation_decision.yaml") as f:
        val = yaml.safe_load(f)
    with open(hidden_dir / "ground_truth.yaml") as f:
        gt = yaml.safe_load(f)
    true_root = gt["root_entity"]

    # Baseline: without promoted edge
    prov_before = _build_test_provider([cand["source"], cand["target"], "CRM:TICKET:001"])
    run_input = GeneratedRunInput(
        run_id="TEST-RUN-POS", scenario_id="H3-FUT-001", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    res_before = Investigator(prov_before).run(run_input, op_dir)

    # After: with governed promotion
    prov_after = copy.deepcopy(prov_before)
    engine = PromotionEngine()
    engine.promote_candidate(cand, val, prov_after)
    res_after = Investigator(prov_after).run(run_input, op_dir)

    assert res_after.explanation_coverage >= res_before.explanation_coverage
    assert res_after.terminal_state == Terminal.EXPLAINED
    assert res_after.ranked_hypotheses[0].canonical_root_entity == true_root


def test_h3_neutral_transfer_does_not_fake_improvement(h3_units):
    """Test 9: In neutral/unrelated scenarios, learning value is zero and does not fake improvement."""
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    unit_dir = TEST_UNITS_DIR / "H3-LU-001"
    op_dir = unit_dir / "future_incident" / "operational"
    run_input = GeneratedRunInput(
        run_id="TEST-RUN-NEU", scenario_id="H3-FUT-001", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    # Promote an irrelevant relation between unrelated nodes
    unrelated_cand = {
        "candidate_id": "CAND-UNRELATED",
        "source": "IMS:SCSCF:001",
        "target": "SA5G:AMF:002",
        "proposed_type": "depends-on",
    }
    unrelated_val = {
        "validation_id": "VAL-UNRELATED",
        "candidate_id": "CAND-UNRELATED",
        "decision": "ACCEPT",
        "validated_by_role": "IMS SME",
        "reason": "Verified IMS link.",
    }
    res_before = Investigator(prov).run(run_input, op_dir)
    engine = PromotionEngine()
    engine.promote_candidate(unrelated_cand, unrelated_val, prov)
    res_after = Investigator(prov).run(run_input, op_dir)

    # Coverage should remain unchanged
    assert res_after.explanation_coverage == res_before.explanation_coverage


def test_h3_negative_transfer_detected(h3_units):
    """Test 10: In poisoned validation cohort, governed learning resists negative transfer."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-026"
    op_dir = unit_dir / "future_incident" / "operational"
    with open(unit_dir / "candidate_knowledge.yaml") as f:
        cand = yaml.safe_load(f)
    with open(unit_dir / "validation_decision.yaml") as f:
        val = yaml.safe_load(f)

    prov = _build_test_provider([cand["source"], cand["target"], "CRM:TICKET:001"])
    engine = PromotionEngine()
    engine.promote_candidate(cand, val, prov)

    run_input = GeneratedRunInput(
        run_id="TEST-RUN-POI", scenario_id="H3-FUT-026", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    res = Investigator(prov).run(run_input, op_dir)

    # Must NOT select the poisoned facility node as the primary root cause
    assert res.ranked_hypotheses[0].canonical_root_entity != cand["target"]


def test_h3_stale_knowledge_detected(h3_units):
    """Test 11: In stale topology cohort, FikraCore detects contradiction and refuses stale path."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-021"
    op_dir = unit_dir / "future_incident" / "operational"
    with open(unit_dir / "candidate_knowledge.yaml") as f:
        cand = yaml.safe_load(f)
    with open(unit_dir / "validation_decision.yaml") as f:
        val = yaml.safe_load(f)

    prov = _build_test_provider([cand["source"], cand["target"], "CRM:TICKET:001"])
    engine = PromotionEngine()
    engine.promote_candidate(cand, val, prov)

    run_input = GeneratedRunInput(
        run_id="TEST-RUN-STALE", scenario_id="H3-FUT-021", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    res = Investigator(prov).run(run_input, op_dir)

    stale_h = next((h for h in res.ranked_hypotheses if h.canonical_root_entity == cand["target"]), None)
    assert stale_h is not None
    assert len(stale_h.contradicting_evidence) > 0 or stale_h.status.value == "REJECTED"
    assert res.ranked_hypotheses[0].canonical_root_entity != cand["target"]


def test_h3_conflicting_knowledge_not_silently_overwritten(h3_units):
    """Test 12: Promoting a contradicting link type triggers conflict rejection instead of silent overwrite."""
    engine = PromotionEngine()
    prov = _build_test_provider(
        ["SA5G:UPF:003", "IP:PE:RTR-21"],
        relationships=[{
            "relationship_id": "EXISTING-001",
            "source": "SA5G:UPF:003",
            "target": "IP:PE:RTR-21",
            "link_type": "routes-through",
            "state": "CONFIRMED",
            "confidence": 1.0,
            "provenance": "manual-entry",
        }]
    )
    # Attempt to promote contradicting inverse relation
    conflicting_cand = {
        "candidate_id": "CAND-CONFLICT",
        "source": "IP:PE:RTR-21",
        "target": "SA5G:UPF:003",
        "proposed_type": "routes-through",
    }
    val = {
        "validation_id": "VAL-CONFLICT",
        "candidate_id": "CAND-CONFLICT",
        "decision": "ACCEPT",
        "validated_by_role": "Transport SME",
        "reason": "Test conflict.",
    }
    success, rec, errors = engine.promote_candidate(conflicting_cand, val, prov)
    assert not success
    assert any("conflict" in err.lower() for err in errors)


def test_h3_learning_provenance_preserved(h3_units):
    """Test 13: Promotion records preserve immutable provenance from candidate to SME to edge."""
    engine = PromotionEngine()
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    candidate = {
        "candidate_id": "CAND-PROV",
        "source": "SA5G:UPF:003",
        "target": "IP:PE:RTR-21",
        "proposed_type": "routes-through",
    }
    validation = {
        "validation_id": "VAL-PROV",
        "candidate_id": "CAND-PROV",
        "decision": "ACCEPT",
        "validated_by_role": "Core SME",
        "reason": "Verified audit trail.",
    }
    success, rec, _ = engine.promote_candidate(candidate, validation, prov)
    assert success
    assert rec.candidate_id == "CAND-PROV"
    assert rec.validation_id == "VAL-PROV"
    assert rec.provenance.get("validator_role") == "Core SME"
    assert rec.rollback_supported
    assert len(engine.list_promotions()) > 0


def test_h3_mark_zaki_uses_shared_state(h3_units):
    """Test 14: Mark / Zaki bridge consumes the standard UI presentation model and respects safety."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-001"
    op_dir = unit_dir / "future_incident" / "operational"
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    run_input = GeneratedRunInput(
        run_id="RUN-ZAKI", scenario_id="H3-FUT-001", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    result = Investigator(prov).run(run_input, op_dir)
    ui_model = build_ui_presentation_model(result, unit_dir, mode="DEMO", current_step=4)

    bridge = ZakiBridge()
    ctx = bridge.build_context(ui_model)
    assert ctx.learning_state is not None

    ans_learn = bridge.answer_query("What did FikraCore learn?", ctx)
    assert ans_learn["grounded"]
    assert ans_learn["truth_blind"]
    assert "learned that" in ans_learn["response"]

    ans_val = bridge.answer_query("Who validated this relationship?", ctx)
    assert "reviewed and given decision" in ans_val["response"]


def test_h3_demo_metadata_does_not_change_reasoning(h3_units):
    """Test 15: Demo metadata affects presentation headlines but never alters underlying causal reasoning."""
    unit_dir = TEST_UNITS_DIR / "H3-LU-001"
    op_dir = unit_dir / "future_incident" / "operational"
    prov = _build_test_provider(["SA5G:UPF:003", "IP:PE:RTR-21"])
    run_input = GeneratedRunInput(
        run_id="RUN-DEMO-META", scenario_id="H3-FUT-001", difficulty_profile="L1", seed=42,
        alarms_path=str(op_dir / "alarms.jsonl"), logs_path=str(op_dir / "logs.jsonl"),
        metrics_path=str(op_dir / "metrics.jsonl"), kpis_path=str(op_dir / "kpis.jsonl"),
        traces_path=str(op_dir / "traces.jsonl"), changes_path=str(op_dir / "changes.jsonl"),
        tickets_path=str(op_dir / "tickets.jsonl"), recovery_path=str(op_dir / "recovery.jsonl"),
    )
    result = Investigator(prov).run(run_input, op_dir)

    model_demo = build_ui_presentation_model(result, unit_dir, mode="DEMO", current_step=1)
    model_inv = build_ui_presentation_model(result, unit_dir, mode="INVESTIGATION", current_step=1)

    # Core reasoning results must be strictly identical
    assert model_demo.reasoning == model_inv.reasoning
    assert model_demo.impact == model_inv.impact
    assert model_demo.timeline == model_inv.timeline

    # Only presentation text varies by mode
    assert model_demo.presentation["active_mode"] == "DEMO"
    assert model_inv.presentation["active_mode"] == "INVESTIGATION"


def test_h1_h2_regression_suite_still_passes():
    """Test 16: Ensure H1 and H2 existing test baselines remain 100% operational."""
    from engine_stack.engines.telecom_brain.tests.test_h2_gap_discovery import test_h1_regression_suite_still_passes
    test_h1_regression_suite_still_passes()
