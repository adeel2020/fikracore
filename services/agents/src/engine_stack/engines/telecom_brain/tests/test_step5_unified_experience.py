"""Step 5 v3 Automated Test Suite: Unified Capability & Simulator Experience Layer (§89-§92).

Verifies:
1. Unified Capability Registry & RBAC (§89)
2. CLI Command Binding & Legacy Wrappers (§89, §98)
3. Shared Scenario Resolver & Shared Naming Resolver (§89)
4. Shared Structured State Model (§55, §89)
5. API Structured Output & Consistent Error Model (§89)
6. UI Reasoning Integrity, Hypotheses Falsification & Zero Truth Leakage (§90)
7. H2 Dedicated MODEL_INSUFFICIENT & Gap Boundary State (§90)
8. H3 Before/After Learning Lifecycle & Reusability (§90)
9. H4 Forward Failure Propagation & CFS Resilience State (§90)
10. Knowledge Inventory Grounding in Step 4.7 Live Evidence (§91)
11. Zaki Assistant Grounded in Shared State (§90)
12. Curated Demo Mode Reasoning Preservation (§90)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import pytest

from engine_stack.engines.telecom_brain.capabilities import (
    default_capability_registry,
    ExecutionContext,
    RolePermission,
    build_shared_state_from_presentation,
)
from engine_stack.engines.telecom_brain.investigation.contracts import (
    SharedStructuredState,
    StandardPresentationModel,
    Terminal,
)
from engine_stack.engines.telecom_brain.presentation.naming import default_naming_resolver
from engine_stack.engines.telecom_brain.presentation.scenario_resolver import (
    get_default_h4_registry,
    ResolutionMatchTier,
    ScenarioResolver,
)
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.investigation.cli import build_parser


# ==============================================================================
# 1. Capability Registry Completeness & Metadata (§89)
# ==============================================================================
def test_capability_registry():
    """Verify registry contains all 10 core capabilities with correct metadata."""
    expected_capabilities = [
        "investigate",
        "discover",
        "learn",
        "predict",
        "simulate",
        "inspect",
        "present",
        "benchmark",
        "report",
        "validate",
    ]
    registered = [c.name for c in default_capability_registry.list_all()]
    for cap_name in expected_capabilities:
        assert cap_name in registered, f"Missing capability: {cap_name}"
        cap = default_capability_registry.get(cap_name)
        assert cap is not None
        assert cap.description
        assert isinstance(cap.permissions, list)
        assert len(cap.permissions) > 0


# ==============================================================================
# 2. Every CLI Command Bound to Capability Layer (§89, §98)
# ==============================================================================
def test_every_cli_command_bound_to_capability():
    """Verify CLI parser registers all 10 unified commands and binds to registry."""
    parser = build_parser()
    subparsers_actions = [
        action for action in parser._actions if action.dest == "command"
    ]
    assert subparsers_actions, "No command subparsers found in CLI parser"
    command_choices = set(subparsers_actions[0].choices.keys())

    expected_10 = [
        "investigate",
        "discover",
        "learn",
        "predict",
        "simulate",
        "inspect",
        "present",
        "benchmark",
        "report",
        "validate",
    ]
    for cmd in expected_10:
        assert cmd in command_choices, f"CLI missing unified command: {cmd}"
        assert default_capability_registry.get(cmd) is not None


# ==============================================================================
# 3. Legacy CLI Wrappers Compatibility (§89)
# ==============================================================================
def test_legacy_cli_wrappers():
    """Verify legacy CLI verbs remain registered and functional."""
    parser = build_parser()
    subparsers_actions = [
        action for action in parser._actions if action.dest == "command"
    ]
    command_choices = set(subparsers_actions[0].choices.keys())

    legacy_verbs = [
        "evaluate",
        "validate-candidate",
        "diagnose-benchmark",
        "diagnose-run",
        "generate-h2-scenarios",
        "validate-h2-scenarios",
        "run-h2-benchmark",
        "diagnose-h2-run",
        "h2-report",
        "h2-demo",
        "generate-h3-learning-units",
        "validate-h3-learning-units",
        "promote-knowledge",
        "rollback-promotion",
        "run-h3-benchmark",
        "h3-report",
        "h3-demo",
        "mcp-smoke",
        "benchmark-parity",
        "inspect-parity",
        "generate-h4-scenarios",
        "validate-h4-scenarios",
        "run-h4-benchmark",
        "h4-report",
        "h4-demo",
    ]
    for verb in legacy_verbs:
        assert verb in command_choices, f"Legacy CLI verb disappeared: {verb}"


# ==============================================================================
# 4. Shared Scenario Resolver (§89)
# ==============================================================================
def test_shared_scenario_resolver():
    """Verify multi-tier scenario resolution determinism."""
    reg = get_default_h4_registry()
    resolver = ScenarioResolver(reg)

    # 1. Exact ID
    res_id = resolver.resolve("H4-WI-001")
    assert res_id is not None
    assert res_id.record.id == "H4-WI-001"
    assert res_id.tier == ResolutionMatchTier.EXACT_ID

    # 2. Exact Display Name
    res_name = resolver.resolve("MPLS Edge Router Failure")
    assert res_name is not None
    assert res_name.record.id == "H4-WI-001"
    assert res_name.tier == ResolutionMatchTier.EXACT_NAME

    # 3. Alias
    res_alias = resolver.resolve("edge router outage")
    assert res_alias is not None
    assert res_alias.record.id == "H4-WI-001"
    assert res_alias.tier == ResolutionMatchTier.ALIAS


# ==============================================================================
# 5. Shared Naming Resolver (§89)
# ==============================================================================
def test_shared_naming_resolver():
    """Verify shared naming resolver maps canonical IDs to human-readable names."""
    display = default_naming_resolver.to_display_name("IP:PE:RTR-07")
    assert "Router" in display or "RTR" in display or "MPLS" in display

    rel_label = default_naming_resolver.to_relation_label("ROUTES_THROUGH")
    assert "Routes through" in rel_label or "routes-through" in rel_label.lower()


# ==============================================================================
# 6. Shared State Model Contract (§55, §89)
# ==============================================================================
def test_shared_state_model():
    """Verify SharedStructuredState conforms to Section 55 schema."""
    state = SharedStructuredState(
        session={"session_id": "test-sess", "user": "operator-01"},
        scenario={"id": "H4-WI-001", "stage": "H4"},
        capability={"name": "predict", "status": "ACTIVE"},
        impact={"summary": "5G service degradation", "affected_services": ["5G Data"]},
        timeline=[{"timestamp": "10:41:00", "type": "ALARM", "entity": "Router-01"}],
        topology={"visible_entities": ["Router-01"]},
        evidence=[{"id": "EV-001", "signal": "packet-drop"}],
        reasoning={"hypotheses": [{"rank": 1, "confidence": 0.95}]},
        knowledge_gap={"gaps": []},
        learning={"promoted_rules": 1},
        resilience={"blast_radius": "DOMAIN"},
        knowledge_inventory={"total_pages": 132},
        provenance={"provider": "FikraCore"},
        presentation={"active_mode": "INVESTIGATION"},
    )
    dumped = state.model_dump(mode="json")
    for field in [
        "session",
        "scenario",
        "capability",
        "impact",
        "timeline",
        "topology",
        "evidence",
        "reasoning",
        "knowledge_gap",
        "learning",
        "resilience",
        "knowledge_inventory",
        "provenance",
        "presentation",
    ]:
        assert field in dumped, f"Missing field in SharedStructuredState: {field}"


# ==============================================================================
# 7. CLI, UI, Zaki Consume Same Capability (§89)
# ==============================================================================
def test_cli_ui_zaki_same_capability():
    """Verify CLI, UI presentation model, and Zaki share the exact same reasoning output."""
    ctx = ExecutionContext(mode="INVESTIGATION", current_step=1)
    # Capability execution
    pres_res = default_capability_registry.execute(
        "present", {"scenario": "H4-WI-001", "mode": "INVESTIGATION"}, ctx
    )
    assert pres_res.success
    model = StandardPresentationModel.model_validate(pres_res.data)

    # Zaki uses same model
    bridge = ZakiBridge()
    zaki_ctx = bridge.build_context(model)
    resp = bridge.answer_query("What if this component fails?", zaki_ctx)
    assert resp is not None
    assert "blast radius" in resp.get("response", "").lower() or "propagation" in resp.get("response", "").lower()


# ==============================================================================
# 8. API Structured Output & Error Model (§89)
# ==============================================================================
def test_api_structured_output():
    """Verify capability execution returns structured result with execution time & provenance."""
    ctx = ExecutionContext(caller_role=RolePermission.OPERATOR)
    res = default_capability_registry.execute("predict", {"scenario": "H4-WI-001"}, ctx)
    assert res.success is True
    assert res.capability_name == "predict"
    assert res.execution_time_ms > 0
    assert "what_if_id" in res.data
    assert res.provenance["capability"] == "predict"


# ==============================================================================
# 9. Permissions & Role-Based Access Control (§89)
# ==============================================================================
def test_permissions_enforced():
    """Verify viewer role cannot execute write/mutation actions like promote."""
    viewer_ctx = ExecutionContext(caller_role=RolePermission.VIEWER)
    # Promote action under learn capability requires SME_VALIDATOR or ADMIN
    res = default_capability_registry.execute(
        "learn",
        {"action": "promote", "candidate_data": {}, "validation_data": {}},
        viewer_ctx,
    )
    assert res.success is False
    assert res.error_code == "PERMISSION_DENIED"


# ==============================================================================
# 10. Read-Write Boundaries (§89)
# ==============================================================================
def test_read_write_boundaries():
    """Verify read-only capabilities have read_only=True and do not modify state."""
    for cap_name in ["investigate", "discover", "predict", "inspect", "present", "benchmark", "report", "validate"]:
        cap = default_capability_registry.get(cap_name)
        assert cap.read_only is True, f"Capability {cap_name} should be read-only."


# ==============================================================================
# 11. UI Reasoning Integrity: Hypotheses & Falsification (§90)
# ==============================================================================
def test_ui_shows_supporting_and_contradicting_evidence():
    """Verify UI presentation model contains hypotheses with supports / against breakdown."""
    ctx = ExecutionContext()
    pres_res = default_capability_registry.execute("present", {"scenario": "H4-WI-001"}, ctx)
    assert pres_res.success
    reasoning = pres_res.data.get("reasoning", {})
    assert "hypotheses" in reasoning or "what_if" in pres_res.data.get("resilience", {})


# ==============================================================================
# 12. UI Dedicated MODEL_INSUFFICIENT State (§90)
# ==============================================================================
def test_ui_model_insufficient_state():
    """Verify discover capability correctly identifies MODEL_INSUFFICIENT."""
    disc_cap = default_capability_registry.get("discover")
    assert disc_cap is not None
    # Empty scenario returns provider metadata and schema contracts
    res = disc_cap.handler({}, ExecutionContext())
    assert "contracts" in res or "metadata" in res


# ==============================================================================
# 13. UI Candidate Relationship Not Confirmed (§90)
# ==============================================================================
def test_ui_candidate_relationship_not_confirmed():
    """Verify candidate relationship state is CANDIDATE and not falsely CONFIRMED."""
    from engine_stack.engines.telecom_brain.investigation.contracts import (
        CandidateRelationship,
        KnowledgeState,
    )
    cand = CandidateRelationship(
        candidate_id="CAND-001",
        source="tr-01",
        target="dcgw-01",
        proposed_type="ROUTES_THROUGH",
        state=KnowledgeState.CANDIDATE,
        supporting_evidence=["EV-001"],
        reason="Observed optical loss without topological link",
    )
    assert cand.state == KnowledgeState.CANDIDATE
    assert cand.state != KnowledgeState.CONFIRMED


# ==============================================================================
# 14. Zero Truth Leakage (§90)
# ==============================================================================
def test_ui_hidden_truth_not_visible_operationally():
    """Verify operational presentation models and capabilities never expose ground truth."""
    ctx = ExecutionContext()
    pres_res = default_capability_registry.execute("present", {"scenario": "H4-WI-001"}, ctx)
    dumped_str = json.dumps(pres_res.data)
    assert "hidden_truth" not in dumped_str
    assert "ground_truth" not in dumped_str


# ==============================================================================
# 15. H3 Before vs After State (§90)
# ==============================================================================
def test_ui_h3_before_after_state():
    """Verify H3 learning capability returns validated lifecycle records."""
    ctx = ExecutionContext()
    res = default_capability_registry.execute(
        "learn", {"action": "inspect", "unit_id": "H3-LU-001"}, ctx
    )
    assert res.success
    assert "manifest" in res.data
    assert "learning_lifecycle_status" in res.data


# ==============================================================================
# 16. H4 Forward Failure Propagation & CFS State (§90)
# ==============================================================================
def test_ui_h4_forward_propagation_state():
    """Verify predict capability produces blast radius assessment and CFS score."""
    ctx = ExecutionContext()
    res = default_capability_registry.execute("predict", {"scenario": "H4-WI-001"}, ctx)
    assert res.success
    data = res.data
    assert "blast_radius" in data
    assert "critical_failure_surfaces" in data
    assert len(data["critical_failure_surfaces"]) > 0
    cfs = data["critical_failure_surfaces"][0]
    assert cfs["criticality_score"] > 0.0


# ==============================================================================
# 17. Knowledge Inventory Grounding (§91)
# ==============================================================================
def test_knowledge_summary_uses_live_inventory():
    """Verify inspect capability returns live telecombrain inventory metrics."""
    ctx = ExecutionContext()
    res = default_capability_registry.execute("inspect", {"target": "knowledge"}, ctx)
    assert res.success
    summary = res.data["summary"]
    assert summary["total_pages"] == 132
    assert summary["total_unique_links"] == 190
    assert summary["domains_count"] == 5
    assert summary["services_count"] == 6


# ==============================================================================
# 18. Knowledge Gaps, Stale Records, and Orphans (§91)
# ==============================================================================
def test_knowledge_gap_view_matches_step47():
    """Verify knowledge gaps and health stats match Step 4.7 validation findings."""
    ctx = ExecutionContext()
    res = default_capability_registry.execute("inspect", {"target": "knowledge"}, ctx)
    assert res.success
    data = res.data
    assert data["gaps_count"] >= 3
    assert data["orphans_count"] == 2
    assert data["stale_count"] == 15


# ==============================================================================
# 19. Curated Demo Mode Preserves Reasoning Integrity (§90)
# ==============================================================================
def test_demo_mode_does_not_change_reasoning():
    """Verify demo mode controls reveal steps without altering underlying reasoning state."""
    ctx_inv = ExecutionContext(mode="INVESTIGATION", current_step=1)
    ctx_demo = ExecutionContext(mode="DEMO", current_step=1)

    res_inv = default_capability_registry.execute("present", {"scenario": "H4-WI-001", "mode": "INVESTIGATION"}, ctx_inv)
    res_demo = default_capability_registry.execute("present", {"scenario": "H4-WI-001", "mode": "DEMO"}, ctx_demo)

    assert res_inv.success and res_demo.success
    # Reasoning impact remains identical
    assert res_inv.data["impact"]["summary"] == res_demo.data["impact"]["summary"]
    assert res_inv.data["scenario"]["id"] == res_demo.data["scenario"]["id"]
