"""Step 5.2 Live Reasoning Activation & Unified Operational Run Tests (§63).

Covers all 23 backend acceptance tests:
1.  test_create_live_run_from_intent_violation
2.  test_live_run_uses_existing_operational_run_model
3.  test_live_run_preserves_existing_stage_model
4.  test_intent_violation_is_trigger_not_root_cause
5.  test_live_evidence_normalized_to_existing_contract
6.  test_live_evidence_admission_backend_owned
7.  test_duplicate_live_evidence_does_not_double_count
8.  test_live_run_attach_to_existing_incident
9.  test_live_run_create_new_when_not_correlated
10. test_live_provider_failure_is_explicit
11. test_live_nbe_retests_same_stage
12. test_live_run_blocking_preserves_current_stage
13. test_live_domain_attribution_delayed_until_supported
14. test_live_impact_starts_unknown
15. test_live_recovery_does_not_auto_confirm_root_cause
16. test_live_run_terminal_state_validated
17. test_live_run_has_no_hidden_truth
18. test_simulation_hidden_truth_still_isolated
19. test_live_and_simulation_use_same_reasoning_pipeline
20. test_live_zaki_context_scoped_to_run
21. test_live_zaki_does_not_invent_evidence
22. test_source_switch_rejects_stale_events
23. test_live_replay_does_not_requery_providers
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import (
    SimulationManager,
    SimulationRun,
    simulation_manager,
    VALID_TERMINAL_STATES,
)
from engine_stack.engines.telecom_brain.simulator.live_reasoning import (
    live_intent_registry,
    default_provider_registry,
    LGTMProvider,
    NetworkToolProvider,
    normalize_live_evidence,
    compute_evidence_fingerprint,
)



app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _reset_manager() -> SimulationManager:
    mgr = SimulationManager()
    mgr.runs.clear()
    return mgr


# ---------------------------------------------------------------------------
# 1. test_create_live_run_from_intent_violation
# ---------------------------------------------------------------------------
def test_create_live_run_from_intent_violation():
    """Activating an intent violation creates an operational run with source_mode LIVE_INTENT."""
    mgr = _reset_manager()
    run, decision = mgr.attach_or_create_live_run("INTENT-APN-001")
    assert run.run_id.startswith("RUN-LIVE-")
    assert run.source_mode == "LIVE_INTENT"
    assert run.intent_id == "INTENT-APN-001"
    assert run.status == "RUNNING"
    assert run.stage_index == 0
    assert decision.decision == "CREATE_NEW_RUN"

    # API test
    res = client.post("/api/v1/fikracore/live/intents/INTENT-APN-001/activate")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["source_mode"] == "LIVE_INTENT"
    assert data["intent_id"] == "INTENT-APN-001"


# ---------------------------------------------------------------------------
# 2. test_live_run_uses_existing_operational_run_model
# ---------------------------------------------------------------------------
def test_live_run_uses_existing_operational_run_model():
    """Live runs use the authoritative SimulationRun model without a parallel class."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-VOLTE-001")
    assert isinstance(run, SimulationRun)
    assert hasattr(run, "run_id")
    assert hasattr(run, "stage_index")
    assert hasattr(run, "snapshot_version")
    assert hasattr(run, "sequence")
    assert hasattr(run, "source_mode")
    assert hasattr(run, "admitted_evidence")


# ---------------------------------------------------------------------------
# 3. test_live_run_preserves_existing_stage_model
# ---------------------------------------------------------------------------
def test_live_run_preserves_existing_stage_model():
    """Live operational runs execute through the identical 8 authoritative stages."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    state = mgr.get_state(run_id=run.run_id)
    stages = state["stages"]
    assert len(stages) == 8
    stage_labels = [s["label"].upper() for s in stages]
    assert stage_labels == [
        "TRIGGER",
        "SIGNAL_FLOOD",
        "CORRELATION",
        "HYPOTHESIS_GENERATION",
        "HYPOTHESIS_TESTING",
        "KNOWLEDGE_GAP_CHECK",
        "LEARNING_VALIDATION",
        "ACTION",
    ]
    assert state["current_stage"] == "TRIGGER"



# ---------------------------------------------------------------------------
# 4. test_intent_violation_is_trigger_not_root_cause
# ---------------------------------------------------------------------------
def test_intent_violation_is_trigger_not_root_cause():
    """Intent violation serves as the operational scope trigger, never root cause confirmation."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    state = mgr.get_state(run_id=run.run_id)

    # Trigger event is present
    trigger_ev = state["events"][0]
    assert trigger_ev["badge"] == "ALARM"
    assert "Intent Violation" in trigger_ev["title"]

    # Hypotheses at stage 0 (TRIGGER) must NOT be confirmed as root cause
    for hyp in state["hypotheses"]:
        assert hyp["status"] != "CONFIRMED"
        assert hyp.get("lifecycle_state") != "CONFIRMED"
        assert hyp["confidence"] < 50.0


# ---------------------------------------------------------------------------
# 5. test_live_evidence_normalized_to_existing_contract
# ---------------------------------------------------------------------------
def test_live_evidence_normalized_to_existing_contract():
    """Raw operational events are normalized into canonical evidence contracts."""
    raw = {
        "source_system": "Prometheus",
        "event_id": "prom_drop_491",
        "entity_id": "APN-GW-01",
        "category": "metric",
        "title": "Egress drop rate threshold exceeded",
        "severity": "high",
        "reliability": 0.98,
    }
    normalized = normalize_live_evidence(raw, run_id="RUN-LIVE-001")
    assert normalized["id"].startswith("EV-")
    assert normalized["event_id"] == "prom_drop_491"
    assert normalized["category"] == "metric"
    assert normalized["badge"] == "METRIC"
    assert normalized["state"] == "OBSERVED"
    assert normalized["run_id"] == "RUN-LIVE-001"
    assert "fingerprint" in normalized
    assert normalized["quality"]["reliability"] == 0.98



# ---------------------------------------------------------------------------
# 6. test_live_evidence_admission_backend_owned
# ---------------------------------------------------------------------------
def test_live_evidence_admission_backend_owned():
    """A client cannot bypass backend admission by sending state ADMITTED."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")

    # Ingest degraded/unreliable telemetry
    unreliable_raw = {
        "source_system": "UntrustedProbe",
        "event_id": "probe_999",
        "entity_id": "GW-UNKNOWN",
        "category": "metric",
        "reliability": 0.05,  # below minimum threshold 0.2
        "state": "ADMITTED",  # caller attempts bypass
    }
    admission = mgr.admit_live_evidence(run.run_id, unreliable_raw)
    assert admission.admission_state == "FILTERED"
    assert "reliability threshold" in admission.reason

    # Reliable telemetry is admitted
    reliable_raw = {
        "source_system": "Prometheus-SLO",
        "event_id": "prom_101",
        "entity_id": "APN-GW-01",
        "category": "metric",
        "reliability": 0.95,
        "title": "Interface drop rate 4.2%",
    }
    adm_valid = mgr.admit_live_evidence(run.run_id, reliable_raw)
    assert adm_valid.admission_state == "ADMITTED"
    assert len(run.admitted_evidence) == 1


# ---------------------------------------------------------------------------
# 7. test_duplicate_live_evidence_does_not_double_count
# ---------------------------------------------------------------------------
def test_duplicate_live_evidence_does_not_double_count():
    """Duplicate evidence delivery is detected via fingerprint and rejected."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    raw = {
        "source_system": "Prometheus-SLO",
        "event_id": "prom_dup_001",
        "entity_id": "APN-GW-01",
        "category": "metric",
        "title": "Interface drop rate 4.2%",
    }
    adm1 = mgr.admit_live_evidence(run.run_id, raw)
    assert adm1.admission_state == "ADMITTED"
    assert len(run.admitted_evidence) == 1

    # Second delivery of identical evidence
    adm2 = mgr.admit_live_evidence(run.run_id, raw)
    assert adm2.admission_state == "REJECTED_DUPLICATE"
    assert len(run.admitted_evidence) == 1  # No double counting!


# ---------------------------------------------------------------------------
# 8. test_live_run_attach_to_existing_incident
# ---------------------------------------------------------------------------
def test_live_run_attach_to_existing_incident():
    """Subsequent intent violations on an active service attach idempotently."""
    mgr = _reset_manager()
    run1, dec1 = mgr.attach_or_create_live_run("INTENT-APN-001")
    assert dec1.decision == "CREATE_NEW_RUN"

    # Same intent / service delivered again while run1 is RUNNING
    run2, dec2 = mgr.attach_or_create_live_run("INTENT-APN-001")
    assert dec2.decision == "ATTACH_TO_EXISTING_RUN"
    assert dec2.matched_run_id == run1.run_id
    assert run2.run_id == run1.run_id


# ---------------------------------------------------------------------------
# 9. test_live_run_create_new_when_not_correlated
# ---------------------------------------------------------------------------
def test_live_run_create_new_when_not_correlated():
    """Different intent or non-correlated service creates a distinct operational run."""
    mgr = _reset_manager()
    run1, dec1 = mgr.attach_or_create_live_run("INTENT-APN-001")
    run2, dec2 = mgr.attach_or_create_live_run("INTENT-VOLTE-001")

    assert dec1.decision == "CREATE_NEW_RUN"
    assert dec2.decision == "CREATE_NEW_RUN"
    assert run1.run_id != run2.run_id
    assert run1.intent_id == "INTENT-APN-001"
    assert run2.intent_id == "INTENT-VOLTE-001"


# ---------------------------------------------------------------------------
# 10. test_live_provider_failure_is_explicit
# ---------------------------------------------------------------------------
def test_live_provider_failure_is_explicit():
    """Provider query failures produce an explicit knowledge gap, not silent omission."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")

    # Record explicit provider failure
    mgr.record_provider_failure(run.run_id, "LGTMProvider", "Prometheus query timeout after 5000ms")
    state = mgr.get_state(run_id=run.run_id)

    gaps = state["knowledge_gaps"]
    provider_gaps = [g for g in gaps if "LGTMProvider" in g.get("label", "")]
    assert len(provider_gaps) >= 1
    assert "timeout" in provider_gaps[0]["reason"]


# ---------------------------------------------------------------------------
# 11. test_live_nbe_retests_same_stage
# ---------------------------------------------------------------------------
def test_live_nbe_retests_same_stage():
    """Executing an NBE action retests the same stage and incorporates new evidence."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.stage_index = 4  # HYPOTHESIS_TESTING

    state_before = mgr.get_state(run_id=run.run_id)
    h1_before = state_before["hypotheses"][0]["confidence"]

    res = mgr.execute_action(run.run_id, "NBA-LIVE-001", advance=False)
    assert res["status"] == "SUCCESS"
    assert res["stage_retested"] is True

    state_after = mgr.get_state(run_id=run.run_id)
    assert state_after["current_stage"] == "HYPOTHESIS_TESTING"
    h1_after = state_after["hypotheses"][0]["confidence"]
    assert h1_after >= h1_before


# ---------------------------------------------------------------------------
# 12. test_live_run_blocking_preserves_current_stage
# ---------------------------------------------------------------------------
def test_live_run_blocking_preserves_current_stage():
    """A blocked live run preserves current stage without stage skipping."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.stage_index = 5  # KNOWLEDGE_GAP_CHECK
    run.status = "BLOCKED"

    state = mgr.get_state(run_id=run.run_id)
    assert state["stage_status"] == "BLOCKED"
    assert state["current_stage"] == "KNOWLEDGE_GAP_CHECK"
    assert state["blocking_reason"] is not None


# ---------------------------------------------------------------------------
# 13. test_live_domain_attribution_delayed_until_supported
# ---------------------------------------------------------------------------
def test_live_domain_attribution_delayed_until_supported():
    """Domain attribution remains PENDING / delayed during initial stages."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.stage_index = 2  # CORRELATION

    state = mgr.get_state(run_id=run.run_id)
    da = state["domain_attribution"]
    assert da["status"] == "PENDING"
    assert da["primary_domain"] is None
    roles = [d["role"] for d in da["domains"]]
    assert "PRIMARY" not in roles

    # At stage 6 (LEARNING_VALIDATION), attribution is ready
    run.stage_index = 6
    state_st6 = mgr.get_state(run_id=run.run_id)
    assert state_st6["domain_attribution"]["status"] == "READY"
    assert state_st6["domain_attribution"]["primary_domain"] == "Packet Core"


# ---------------------------------------------------------------------------
# 14. test_live_impact_starts_unknown
# ---------------------------------------------------------------------------
def test_live_impact_starts_unknown():
    """Service impact begins in UNKNOWN state and develops as evidence arrives."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.stage_index = 1  # SIGNAL_FLOOD

    state = mgr.get_state(run_id=run.run_id)
    impact = state["impact"]
    assert impact["state"] == "UNKNOWN"
    assert impact["confidence"] == "UNKNOWN"
    assert impact["throughput_impact_pct"] is None

    # Later stage (stage 4) has observed impact
    run.stage_index = 4
    state_st4 = mgr.get_state(run_id=run.run_id)
    assert state_st4["impact"]["state"] == "OBSERVED"
    assert state_st4["impact"]["throughput_impact_pct"] is not None


# ---------------------------------------------------------------------------
# 15. test_live_recovery_does_not_auto_confirm_root_cause
# ---------------------------------------------------------------------------
def test_live_recovery_does_not_auto_confirm_root_cause():
    """Recovery signals do not automatically confirm candidate root cause."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.stage_index = 3

    # Ingest recovery telemetry
    mgr.record_recovery_signal(run.run_id, metric_name="success_rate", value=99.6)
    state = mgr.get_state(run_id=run.run_id)

    # Recovery event is recorded in timeline
    recovery_events = [e for e in state["events"] if e.get("category") == "recovery"]
    assert len(recovery_events) >= 1

    # Hypotheses must NOT be auto-confirmed as root cause
    for hyp in state["hypotheses"]:
        assert hyp["status"] != "CONFIRMED"
        assert hyp["confidence"] < 95.0


# ---------------------------------------------------------------------------
# 16. test_live_run_terminal_state_validated
# ---------------------------------------------------------------------------
def test_live_run_terminal_state_validated():
    """Finalizing a live run requires an authoritative valid terminal state."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")

    # Invalid terminal state raises ValueError
    with pytest.raises(ValueError, match="Invalid terminal state"):
        mgr.finalize_run(run.run_id, "SOLVED_COMPLETELY")

    # Valid terminal state succeeds
    mgr.finalize_run(run.run_id, "PARTIALLY_EXPLAINED")
    assert run.terminal_state == "PARTIALLY_EXPLAINED"
    assert run.status == "COMPLETED"


# ---------------------------------------------------------------------------
# 17. test_live_run_has_no_hidden_truth
# ---------------------------------------------------------------------------
def test_live_run_has_no_hidden_truth():
    """Live operational run compiled state contains zero simulator hidden truth."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    state = mgr.get_state(run_id=run.run_id)

    assert "hidden_truth" not in state
    assert "hidden_truth" not in state.get("scenario", {})
    assert "hidden_truth" not in state.get("reasoning_map", {})
    assert "hidden_ground_truth" not in state


# ---------------------------------------------------------------------------
# 18. test_simulation_hidden_truth_still_isolated
# ---------------------------------------------------------------------------
def test_simulation_hidden_truth_still_isolated():
    """Existing offline simulation runs still keep hidden truth isolated from operational state."""
    mgr = _reset_manager()
    sim_run = mgr.create_run(scenario_id="SCN-001")
    state = mgr.get_state(run_id=sim_run.run_id)

    assert "hidden_truth" not in state
    assert "hidden_truth" not in state.get("scenario", {})
    assert "hidden_truth" not in state.get("reasoning_map", {})


# ---------------------------------------------------------------------------
# 19. test_live_and_simulation_use_same_reasoning_pipeline
# ---------------------------------------------------------------------------
def test_live_and_simulation_use_same_reasoning_pipeline():
    """Both modes project through the identical top-level contract keys."""
    mgr = _reset_manager()
    sim_run = mgr.create_run(scenario_id="SCN-001")
    live_run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")

    sim_state = mgr.get_state(run_id=sim_run.run_id)
    live_state = mgr.get_state(run_id=live_run.run_id)

    required_keys = {
        "scenario_id",
        "run_id",
        "status",
        "current_stage",
        "stage_status",
        "stages",
        "events",
        "topology",
        "hypotheses",
        "impact",
        "knowledge_gaps",
        "next_best_actions",
        "reasoning_map",
        "reasoning_trace",
        "zaki",
    }
    assert required_keys.issubset(set(sim_state.keys()))
    assert required_keys.issubset(set(live_state.keys()))


# ---------------------------------------------------------------------------
# 20. test_live_zaki_context_scoped_to_run
# ---------------------------------------------------------------------------
def test_live_zaki_context_scoped_to_run():
    """Zaki receives active run context, source_mode, and live intent metadata."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    simulation_manager.runs[run.run_id] = run

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "What intent was violated?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source_mode"] == "LIVE_INTENT"
    assert data["intent_id"] == "INTENT-APN-001"
    assert "Enterprise APN" in data["answer"] or "intent" in data["answer"].lower()


# ---------------------------------------------------------------------------
# 21. test_live_zaki_does_not_invent_evidence
# ---------------------------------------------------------------------------
def test_live_zaki_does_not_invent_evidence():
    """Zaki explicitly affirms it does not invent unadmitted operational evidence."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    simulation_manager.runs[run.run_id] = run

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={
            "query": "Did you invent any synthetic evidence?",
            "run_id": run.run_id,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "does not invent" in data["answer"].lower() or "strictly grounded" in data["answer"].lower()


# ---------------------------------------------------------------------------
# 22. test_source_switch_rejects_stale_events
# ---------------------------------------------------------------------------
def test_source_switch_rejects_stale_events():
    """Events with mismatched source_mode, stale revision, or non-advancing sequence are rejected."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    run.snapshot_version = 3
    run.sequence = 5

    # Event with mismatched source_mode
    assert mgr.accept_event(run.run_id, {"source_mode": "SIMULATION", "run_id": run.run_id}) is False

    # Event with stale revision
    assert mgr.accept_event(run.run_id, {"source_mode": "LIVE_INTENT", "run_id": run.run_id, "revision": 2, "sequence": 6}) is False

    # Event with non-advancing sequence
    assert mgr.accept_event(run.run_id, {"source_mode": "LIVE_INTENT", "run_id": run.run_id, "revision": 3, "sequence": 5}) is False

    # Valid advancing event
    assert mgr.accept_event(run.run_id, {"source_mode": "LIVE_INTENT", "run_id": run.run_id, "intent_id": "INTENT-APN-001", "revision": 3, "sequence": 6}) is True


# ---------------------------------------------------------------------------
# 23. test_live_replay_does_not_requery_providers
# ---------------------------------------------------------------------------
def test_live_replay_does_not_requery_providers():
    """Replay mode is strictly read-only and rejects new provider evidence ingestion."""
    mgr = _reset_manager()
    run, _ = mgr.attach_or_create_live_run("INTENT-APN-001")
    mgr.replay_run(run.run_id)
    assert run.is_replay is True

    # Ingesting evidence during replay is rejected (§51)
    raw = {
        "source_system": "Prometheus-SLO",
        "event_id": "prom_replay_01",
        "entity_id": "APN-GW-01",
        "category": "metric",
    }
    adm = mgr.admit_live_evidence(run.run_id, raw)
    assert adm.admission_state == "REJECTED"
    assert "replay mode" in adm.reason.lower()
