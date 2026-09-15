"""Step 4.2 / H2 Automated Test Suite: UI Presentation Adapter, Curated Demo Mode & Zaki Bridge.

Covers the 10 required test cases from the H2 UI/Demo/Zaki specification:
1. test_same_state_drives_investigation_and_demo_modes
2. test_demo_metadata_does_not_change_reasoning
3. test_zaki_consumes_structured_investigation_state
4. test_zaki_cannot_access_hidden_truth
5. test_zaki_does_not_promote_candidate_to_confirmed
6. test_zaki_mode_awareness
7. test_demo_reset_replay_is_deterministic
8. test_ui_uses_human_readable_display_names
9. test_ui_preserves_canonical_ids_for_traceability
10. test_demo_scenario_step_order_is_presentation_only
"""

from __future__ import annotations

import copy
from pathlib import Path
import pytest
import yaml

from engine_stack.engines.telecom_brain.investigation.contracts import (
    InvestigationResult,
    StandardPresentationModel,
    ZakiContextContract,
)
from engine_stack.engines.telecom_brain.presentation.naming import PresentationNamingResolver
from engine_stack.engines.telecom_brain.presentation.ui_adapter import build_ui_presentation_model
from engine_stack.engines.telecom_brain.presentation.zaki_bridge import ZakiBridge
from engine_stack.engines.telecom_brain.tests.test_h2_gap_discovery import (
    _setup_h2_investigation,
    H2_RUNS_DIR,
)


@pytest.fixture
def sample_h2_run() -> Path:
    """Return the first available H2 run directory."""
    runs = sorted([d for d in H2_RUNS_DIR.iterdir() if d.is_dir() and d.name.startswith("RUN-H2-")])
    assert len(runs) > 0, "No H2 runs found."
    return runs[0]


@pytest.fixture
def sample_investigation(sample_h2_run) -> tuple[InvestigationResult, Path]:
    """Execute investigation and return result and run path."""
    investigator, run_input, op_dir, _ = _setup_h2_investigation(sample_h2_run)
    result = investigator.run(run_input, op_dir)
    return result, sample_h2_run


# 1. Same state drives investigation and demo modes
def test_same_state_drives_investigation_and_demo_modes(sample_investigation):
    result, run_dir = sample_investigation

    model_inv = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION", current_step=1)
    model_demo = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=1)

    # Core operational state must be identical
    assert model_inv.scenario["id"] == model_demo.scenario["id"]
    assert model_inv.impact == model_demo.impact
    assert model_inv.timeline == model_demo.timeline
    assert model_inv.topology["visible_entities"] == model_demo.topology["visible_entities"]
    assert model_inv.topology["visible_relationships"] == model_demo.topology["visible_relationships"]
    assert model_inv.reasoning["hypotheses"] == model_demo.reasoning["hypotheses"]
    assert model_inv.next_best_evidence == model_demo.next_best_evidence
    assert model_inv.candidate_knowledge == model_demo.candidate_knowledge
    assert model_inv.validation == model_demo.validation

    # Only presentation wrapper reflects active mode
    assert model_inv.presentation["active_mode"] == "INVESTIGATION"
    assert model_demo.presentation["active_mode"] == "DEMO"
    assert model_inv.presentation["headline"] != model_demo.presentation["headline"]


# 2. Demo metadata does not change reasoning
def test_demo_metadata_does_not_change_reasoning(sample_h2_run, tmp_path):
    import shutil
    isolated_run = tmp_path / "isolated_run"
    shutil.copytree(sample_h2_run, isolated_run)

    # Corrupt or delete demo_metadata.yaml in copy
    demo_file = isolated_run / "demo_metadata.yaml"
    if demo_file.exists():
        demo_file.unlink()

    investigator, run_input, op_dir, _ = _setup_h2_investigation(isolated_run)
    result = investigator.run(run_input, op_dir)

    # Reasoning must succeed and remain identical regardless of demo metadata
    assert result.terminal_state.value == "MODEL_INSUFFICIENT"
    assert len(result.diagnostics.get("knowledge_gap_records", [])) >= 1
    assert len(result.candidate_relationships) >= 1


# 3. Zaki consumes structured investigation state
def test_zaki_consumes_structured_investigation_state(sample_investigation):
    result, run_dir = sample_investigation
    ui_model = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION")
    bridge = ZakiBridge()

    zaki_ctx = bridge.build_context(ui_model)
    assert isinstance(zaki_ctx, ZakiContextContract)
    assert zaki_ctx.active_scenario == result.scenario_id
    assert zaki_ctx.current_terminal_state == result.terminal_state.value
    assert len(zaki_ctx.visible_topology.get("visible_entities", [])) > 0
    assert len(zaki_ctx.current_hypotheses) > 0
    assert zaki_ctx.validation_status == "PENDING"
    assert len(zaki_ctx.candidate_knowledge) > 0


# 4. Zaki cannot access hidden truth
def test_zaki_cannot_access_hidden_truth(sample_investigation):
    result, run_dir = sample_investigation
    ui_model = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION")
    bridge = ZakiBridge()
    zaki_ctx = bridge.build_context(ui_model)

    # Context schema contains no hidden truth fields
    ctx_dict = zaki_ctx.model_dump()
    forbidden_keys = {"hidden", "hidden_truth", "ground_truth", "evaluator_expectations"}
    for key in ctx_dict:
        assert key not in forbidden_keys

    # Response is truth-blind
    response = bridge.answer_query("What is the ground truth root cause?", zaki_ctx)
    assert response["truth_blind"] is True
    # Does not declare absolute knowledge when model is insufficient
    assert "MODEL_INSUFFICIENT" in response["response"] or "boundary" in response["response"]


# 5. Zaki does not promote candidate to confirmed
def test_zaki_does_not_promote_candidate_to_confirmed(sample_investigation):
    result, run_dir = sample_investigation
    ui_model = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=6)
    bridge = ZakiBridge()
    zaki_ctx = bridge.build_context(ui_model)

    response = bridge.answer_query("What candidate relationship was discovered? Is it confirmed?", zaki_ctx)
    assert response["candidate_status_safe"] is True
    assert "CANDIDATE" in response["response"]
    assert "SME" in response["response"]
    assert "never be automatically promoted" in response["response"]


# 6. Zaki mode awareness
def test_zaki_mode_awareness(sample_investigation):
    result, run_dir = sample_investigation
    bridge = ZakiBridge()

    ui_model_demo = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=3)
    ctx_demo = bridge.build_context(ui_model_demo, mode="DEMO")
    resp_demo = bridge.answer_query("Why is the model insufficient?", ctx_demo)

    ui_model_inv = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION", current_step=1)
    ctx_inv = bridge.build_context(ui_model_inv, mode="INVESTIGATION")
    resp_inv = bridge.answer_query("Why is the model insufficient?", ctx_inv)

    assert resp_demo["active_mode"] == "DEMO"
    assert resp_inv["active_mode"] == "INVESTIGATION"
    # Demo gives guided high-level explanation; Investigation gives technical breakdown
    assert resp_demo["response"] != resp_inv["response"]
    assert "downstream service degradation is observed" in resp_demo["response"]
    assert "residual impact clusters" in resp_inv["response"]


# 7. Demo reset replay is deterministic
def test_demo_reset_replay_is_deterministic(sample_investigation):
    result, run_dir = sample_investigation

    # Step 1
    m1 = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=1)
    # Step 4
    m4 = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=4)
    # Reset back to Step 1
    m1_reset = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=1)

    assert m1.model_dump() == m1_reset.model_dump()
    assert m1.presentation["current_step"] == 1
    assert m4.presentation["current_step"] == 4


# 8. UI uses human readable display names
def test_ui_uses_human_readable_display_names(sample_investigation):
    result, run_dir = sample_investigation
    ui_model = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION")

    # Visible entities have display_name
    for ent in ui_model.topology["visible_entities"]:
        assert "display_name" in ent
        assert not ent["display_name"].startswith("topology/")
        assert "_" not in ent["display_name"] or ":" not in ent["display_name"]

    # Relationships use human-readable relation labels
    for rel in ui_model.topology["visible_relationships"]:
        assert rel["relation"] in {
            "Depends on", "Routes through", "Carried by", "Hosted on", "Runs on",
            "Backhauled by", "Powered by", "Charges via", "Authenticates via",
            "Resolves via", "Timed by", "Uses database", "Uses cache",
            "Uses message bus", "Provisioned by", "Member of", "Monitored by",
            "Supports service", "Serves", "Connected to",
        }


# 9. UI preserves canonical IDs for traceability
def test_ui_preserves_canonical_ids_for_traceability(sample_investigation):
    result, run_dir = sample_investigation
    ui_model = build_ui_presentation_model(result, run_dir, mode="INVESTIGATION")

    for ent in ui_model.topology["visible_entities"]:
        assert "canonical_id" in ent
        assert ent["canonical_id"] != ""

    for rel in ui_model.topology["visible_relationships"]:
        assert "canonical_source" in rel
        assert "canonical_target" in rel

    for cand in ui_model.candidate_knowledge:
        assert "canonical_source" in cand
        assert "canonical_target" in cand


# 10. Demo scenario step order is presentation only
def test_demo_scenario_step_order_is_presentation_only(sample_investigation):
    result, run_dir = sample_investigation

    step1 = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=1)
    step5 = build_ui_presentation_model(result, run_dir, mode="DEMO", current_step=5)

    # Presentation step changes
    assert step1.presentation["current_step"] == 1
    assert step5.presentation["current_step"] == 5
    assert step1.presentation["headline"] != step5.presentation["headline"]

    # Underlying reasoning and data structures remain identical
    assert step1.topology["visible_entities"] == step5.topology["visible_entities"]
    assert step1.topology["visible_relationships"] == step5.topology["visible_relationships"]
    assert step1.reasoning["hypotheses"] == step5.reasoning["hypotheses"]
    assert step1.candidate_knowledge == step5.candidate_knowledge
    assert step1.next_best_evidence == step5.next_best_evidence
