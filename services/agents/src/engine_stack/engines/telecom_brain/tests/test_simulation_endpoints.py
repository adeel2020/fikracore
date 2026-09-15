"""Tests for FikraCore Live Simulator Endpoints & Lifecycle (§25, §26, §50)."""

import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import SimulationManager, simulation_manager
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_list_and_get_scenarios():
    """Verify listing scenarios includes SCN-001 and resolves details."""
    res = client.get("/api/v1/fikracore/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    sc_ids = [s["id"] for s in data["scenarios"]]
    assert "SCN-001" in sc_ids

    res_single = client.get("/api/v1/fikracore/scenarios/SCN-001")
    assert res_single.status_code == 200
    assert res_single.json()["scenario"]["id"] == "SCN-001"


def test_simulation_lifecycle_and_actions():
    """Verify starting, pausing, resuming, stopping, actions, and state retrieval."""
    # 1. Start simulation
    res_start = client.post("/api/v1/fikracore/simulations", json={"scenario_id": "SCN-001", "speed": 1.0, "mode": "live"})
    assert res_start.status_code == 200
    run_data = res_start.json()
    run_id = run_data["run_id"]
    assert run_id.startswith("RUN-")
    assert run_data["simulation_status"] == "RUNNING"

    # 2. Get full state (Initial Trigger phase)
    res_state = client.get(f"/api/v1/fikracore/simulations/{run_id}")
    assert res_state.status_code == 200
    state = res_state.json()
    assert len(state["stages"]) == 8
    assert len(state["events"]) >= 1
    assert state["current_stage"] == "TRIGGER"
    assert state["stage_status"] in {"READY_TO_ADVANCE", "BLOCKED"}
    assert state["impact"]["impact_state"] == "UNKNOWN"
    assert state["impact"]["throughput_impact_pct"] is None
    assert state["impact"]["affected_users"] is None
    assert len(state["topology"]["domains"]) >= 1
    assert state["topology"]["causal_path"] == []
    assert state["hypotheses"] == []
    assert state["knowledge_gaps"] == []
    assert state["next_best_actions"] == []
    assert state["learning"] is None

    # 3. Pause
    res_pause = client.post(f"/api/v1/fikracore/simulations/{run_id}/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["simulation_status"] == "PAUSED"

    # 4. Resume
    res_resume = client.post(f"/api/v1/fikracore/simulations/{run_id}/resume")
    assert res_resume.status_code == 200
    assert res_resume.json()["simulation_status"] == "RUNNING"

    # 5. Execute action NBA-001 -> Advances one stage; confirmation is not skipped.
    res_act = client.post(f"/api/v1/fikracore/simulations/{run_id}/actions", json={"action_id": "NBA-001"})
    assert res_act.status_code == 200
    assert res_act.json()["action_status"] == "COMPLETED"

    res_after_action = client.get(f"/api/v1/fikracore/simulations/{run_id}")
    state_after_action = res_after_action.json()
    assert state_after_action["current_stage"] == "SIGNAL_FLOOD"
    assert state_after_action["impact"]["impact_state"] == "OBSERVED"
    assert state_after_action["impact"]["affected_users"] is None
    assert state_after_action["hypotheses"] == []

    # 6. Stop
    res_stop = client.post(f"/api/v1/fikracore/simulations/{run_id}/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["simulation_status"] == "STOPPED"


def test_simulation_trace_contract_and_endpoint():
    """Expose separate raw evidence and reasoning traces on the backend contract."""
    res_start = client.post("/api/v1/fikracore/simulations", json={"scenario_id": "SCN-001", "speed": 1.0, "mode": "live"})
    assert res_start.status_code == 200
    run_id = res_start.json()["run_id"]

    res_state = client.get(f"/api/v1/fikracore/simulations/{run_id}")
    assert res_state.status_code == 200
    state = res_state.json()
    assert "raw_events" in state
    assert "reasoning_trace" in state
    assert state["raw_events"]
    assert all(event.get("category") not in {"action", "hypothesis"} for event in state["raw_events"])
    assert state["reasoning_trace"][0]["stage"] in {"TRIGGER", "SIGNAL_FLOOD", "CORRELATION", "HYPOTHESIS_GENERATION", "HYPOTHESIS_TESTING", "KNOWLEDGE_GAP_CHECK", "LEARNING_VALIDATION", "ACTION"}

    res_trace = client.get(f"/api/v1/fikracore/simulations/{run_id}/trace", params={"level": "verbose"})
    assert res_trace.status_code == 200
    body = res_trace.json()
    assert body["status"] == "SUCCESS"
    assert body["records"]
    assert body["records"][0]["scenario_id"] == "SCN-001"
    assert body["records"][0]["run_id"] == run_id


def test_clean_run_contract_keeps_hidden_truth_out_of_initial_operational_state():
    """A fresh scenario run starts epistemically empty and does not expose final incident values."""
    res_run = client.post(
        "/api/v1/fikracore/scenarios/SCN-001/run",
        json={"speed": 1.0, "mode": "live", "fresh": True},
    )
    assert res_run.status_code == 200
    first_run_id = res_run.json()["run_id"]

    res_state = client.get(f"/api/v1/fikracore/simulations/{first_run_id}/state")
    assert res_state.status_code == 200
    state = res_state.json()

    assert state["current_stage"] == "TRIGGER"
    assert state["impact"]["impact_state"] == "UNKNOWN"
    assert state["impact"]["throughput_impact_pct"] is None
    assert state["impact"]["affected_users"] is None
    assert state["impact"]["regions_affected"] is None
    assert state["hypotheses"] == []
    assert state["knowledge_gaps"] == []
    assert state["next_best_actions"] == []
    assert state["learning"] is None
    assert state["topology"]["causal_path"] == []
    assert state["topology"]["path_confidence"] == 0
    assert "CUSTOMER IMPACT" not in {domain["name"] for domain in state["topology"]["domains"]}

    trace_types = {record["event_type"] for record in state["reasoning_trace"]}
    assert {"run_created", "run_state_initialized"}.issubset(trace_types)
    assert any(record["event_type"] in {"stage_enter", "stage_blocked"} for record in state["reasoning_trace"])

    res_second_run = client.post(
        "/api/v1/fikracore/scenarios/SCN-001/run",
        json={"speed": 1.0, "mode": "live", "fresh": True},
    )
    assert res_second_run.status_code == 200
    assert res_second_run.json()["run_id"] != first_run_id


def test_stage_machine_does_not_advance_on_resume_and_fresh_start_creates_clean_run():
    """Resume should only change status, while explicit fresh start creates a clean run."""
    manager = SimulationManager()

    stale_run = manager.create_run(scenario_id="SCN-001", speed=1.0, mode="live")
    stale_run.status = "STOPPED"
    stale_run.stage_index = 7

    active_run = manager.resolve_run_for_scenario("SCN-001")
    assert active_run.run_id != stale_run.run_id
    active_run.status = "PAUSED"
    active_run.stage_index = 0

    resumed = manager.resume_run(active_run.run_id)
    assert resumed.status == "RUNNING"
    assert resumed.stage_index == 0

    fresh_run = manager.start_clean_run_for_scenario("SCN-001")
    assert fresh_run.run_id != active_run.run_id
    assert fresh_run.stage_index == 0
    assert fresh_run.tested_hypotheses == []
    assert fresh_run.executed_actions == []


def test_live_stream_does_not_advance_stage_without_state_change():
    """The live stream should not auto-drive the stage machine using elapsed time or a synthetic loop."""
    manager = SimulationManager()
    run = manager.create_run(scenario_id="SCN-001", speed=1.0, mode="live")

    async def read_first_event() -> dict:
        stream = manager.stream_live_events(run.run_id)
        first = await asyncio.wait_for(anext(stream), timeout=0.5)
        payload = json.loads(first.removeprefix("data: ").strip())
        return payload

    payload = asyncio.run(read_first_event())

    assert payload["run_id"] == run.run_id
    assert payload["sequence"] == 0
    assert payload["stages"][0]["status"] == "ACTIVE"


def test_live_stream_includes_reasoning_trace_and_raw_events_for_realtime_trace_view():
    """The SSE payload must expose the live reasoning trace and raw event burst used by the frontend trace panel."""
    manager = SimulationManager()
    run = manager.create_run(scenario_id="SCN-001", speed=1.0, mode="live")

    async def read_first_event() -> dict:
        stream = manager.stream_live_events(run.run_id)
        first = await asyncio.wait_for(anext(stream), timeout=0.5)
        return json.loads(first.removeprefix("data: ").strip())

    payload = asyncio.run(read_first_event())

    assert "current_stage" in payload
    assert "reasoning_trace" in payload
    assert "raw_events" in payload
    assert payload["reasoning_trace"]
    assert payload["raw_events"]
    assert payload["current_stage"] == "TRIGGER"


def test_snapshot_scoped_to_run():
    res_run = client.post(
        "/api/v1/fikracore/scenarios/H4-WI-001/run",
        json={"speed": 1.0, "mode": "live", "fresh": True},
    )
    assert res_run.status_code == 200
    run_id = res_run.json()["run_id"]

    res_snapshot = client.get(f"/api/v1/fikracore/runs/{run_id}/snapshot")
    assert res_snapshot.status_code == 200
    snapshot = res_snapshot.json()

    assert snapshot["scenario_id"] == "H4-WI-001"
    assert snapshot["run_id"] == run_id
    assert snapshot["revision"] == snapshot["snapshot_version"]
    assert snapshot["reasoning_map"]["run_id"] == run_id
    for collection in ("evidence", "reasoning_pathways", "connections", "hypotheses", "knowledge_gaps"):
        assert all(item["scenario_id"] == "H4-WI-001" for item in snapshot["reasoning_map"][collection])
        assert all(item["run_id"] == run_id for item in snapshot["reasoning_map"][collection])


def test_events_scoped_to_scenario_and_run():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")

    async def read_first_event() -> dict:
        stream = manager.stream_live_events(run.run_id)
        first = await asyncio.wait_for(anext(stream), timeout=0.5)
        return json.loads(first.removeprefix("data: ").strip())

    payload = asyncio.run(read_first_event())

    assert payload["scenario_id"] == "H4-WI-001"
    assert payload["run_id"] == run.run_id
    assert payload["revision"] == run.snapshot_version
    assert payload["event_type"] == "stage_changed"


def test_pathway_activation_backend_owned():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.stage_index = 0
    early_state = manager.get_state(run_id=run.run_id)
    pathways = early_state["reasoning_map"]["reasoning_pathways"]
    assert pathways
    allowed_states = {"DORMANT", "DISCOVERED", "ACTIVE", "RESOLVED", "REJECTED"}
    for p in pathways:
        assert p["state"] in allowed_states
        assert p["display_name"]
        if p["state"] == "ACTIVE":
            assert p["activation_reason"]

    # In early stage, Resilience & Failover is DORMANT
    resilience_early = next(p for p in pathways if p["display_name"] == "Resilience & Failover")
    assert resilience_early["state"] == "DORMANT"

    # In later stage (stage 5), Resilience & Failover activates from backend
    run.stage_index = 5
    later_state = manager.get_state(run_id=run.run_id)
    resilience_later = next(p for p in later_state["reasoning_map"]["reasoning_pathways"] if p["display_name"] == "Resilience & Failover")
    assert resilience_later["state"] == "ACTIVE"
    assert resilience_later["activation_reason"]


def test_connection_reason_present():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.stage_index = 5
    run.sequence = 5
    state = manager.get_state(run_id=run.run_id)

    connections = state["reasoning_map"]["connections"]
    allowed_relations = {"CONTRIBUTES_TO", "SUPPORTS", "CONTRADICTS", "REQUIRES", "RESOLVES", "ATTRIBUTES_TO"}
    allowed_states = {"DORMANT", "ACTIVE", "SUPPORTING", "CONTRADICTING", "BLOCKED", "REJECTED", "CONFIRMED", "RESOLVED"}

    assert connections
    assert all(conn["reason"] for conn in connections)
    assert {conn["relation_type"] for conn in connections}.issubset(allowed_relations)
    assert {conn["state"] for conn in connections}.issubset(allowed_states)


def test_hypothesis_confidence_backend_owned():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.stage_index = 3
    state = manager.get_state(run_id=run.run_id)

    hypotheses = state["reasoning_map"]["hypotheses"]
    assert [hyp["display_id"] for hyp in hypotheses] == ["H1", "H2", "H3", "H4"]
    assert all(hyp["confidence"] is None for hyp in hypotheses)
    assert all(hyp["state"] == "CANDIDATE" for hyp in hypotheses)


def test_gap_exact_display_name():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.stage_index = 5
    state = manager.get_state(run_id=run.run_id)

    gaps = state["reasoning_map"]["knowledge_gaps"]
    assert gaps
    for gap in gaps:
        assert gap["display_name"]
        assert len(gap["display_name"]) > 5
        # Must be human-readable, not just an ID
        assert not gap["display_name"].startswith("GAP-")
        assert gap["state"] in {"OPEN", "NEEDS_EVIDENCE", "IN_PROGRESS", "RESOLVED"}
        assert "affected_hypothesis_ids" in gap


def test_validation_exact_display_name():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.stage_index = 6
    state = manager.get_state(run_id=run.run_id)

    val = state["reasoning_map"]["validation"]
    assert val
    assert val["display_name"]
    # Must describe validated fact or review, not generic ID
    assert not val["display_name"].startswith("VAL-")
    assert val["state"] in {"NOT_STARTED", "PENDING", "ACCEPTED", "REJECTED", "MODIFIED", "NEED_MORE_EVIDENCE"}
    assert val["reviewer_role"]


def test_domain_attribution_delayed_until_supported():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")

    early = manager.get_state(run_id=run.run_id)
    early_roles = [domain["role"] for domain in early["reasoning_map"]["domain_attribution"]["domains"]]
    assert "PRIMARY" not in early_roles

    run.stage_index = 6
    supported = manager.get_state(run_id=run.run_id)
    supported_roles = [domain["role"] for domain in supported["reasoning_map"]["domain_attribution"]["domains"]]
    assert "PRIMARY" in supported_roles


def test_duplicate_event_rejected():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.sequence = 3

    # An event with sequence <= run.sequence must be rejected
    dup_event = {
        "scenario_id": "H4-WI-001",
        "run_id": run.run_id,
        "revision": run.snapshot_version,
        "sequence": 3,
    }
    assert manager.accept_event(run.run_id, dup_event) is False

    past_event = {
        "scenario_id": "H4-WI-001",
        "run_id": run.run_id,
        "revision": run.snapshot_version,
        "sequence": 2,
    }
    assert manager.accept_event(run.run_id, past_event) is False

    valid_event = {
        "scenario_id": "H4-WI-001",
        "run_id": run.run_id,
        "revision": run.snapshot_version,
        "sequence": 4,
    }
    assert manager.accept_event(run.run_id, valid_event) is True


def test_stale_revision_rejected():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run.snapshot_version = 4
    run.sequence = 2

    # Stale revision must be rejected
    stale_event = {
        "scenario_id": "H4-WI-001",
        "run_id": run.run_id,
        "revision": 3,
        "sequence": 3,
    }
    assert manager.accept_event(run.run_id, stale_event) is False

    # Wrong run_id must be rejected
    wrong_run_event = {
        "scenario_id": "H4-WI-001",
        "run_id": "RUN-OTHER",
        "revision": 4,
        "sequence": 3,
    }
    assert manager.accept_event(run.run_id, wrong_run_event) is False

    # Current revision and advanced sequence must be accepted
    fresh_event = {
        "scenario_id": "H4-WI-001",
        "run_id": run.run_id,
        "revision": 4,
        "sequence": 3,
    }
    assert manager.accept_event(run.run_id, fresh_event) is True


def test_two_subscribers_do_not_advance_run():
    manager = SimulationManager()
    run = manager.create_run(scenario_id="H4-WI-001", speed=10.0, mode="live")
    initial_stage = run.stage_index

    async def run_subscribers():
        stream1 = manager.stream_live_events(run.run_id)
        stream2 = manager.stream_live_events(run.run_id)
        ev1 = await asyncio.wait_for(anext(stream1), timeout=0.5)
        ev2 = await asyncio.wait_for(anext(stream2), timeout=0.5)
        return ev1, ev2

    asyncio.run(run_subscribers())
    # Two subscribers must not double-advance the stage index
    assert run.stage_index <= initial_stage + 1


def test_next_best_evidence_dynamic_and_stage_synced():
    """Verify Next Best Evidence is dynamic, stage-synced, and executes cleanly."""
    manager = simulation_manager
    run = manager.create_run(scenario_id="SCN-001", speed=1.0, mode="live")
    # Advance run to KNOWLEDGE_GAP_CHECK (stage 5)
    run.stage_index = 5
    state_stage5 = manager.get_state(scenario_id="SCN-001", run_id=run.run_id)

    assert state_stage5["current_stage"] == "KNOWLEDGE_GAP_CHECK"
    assert state_stage5["stage_status"] == "BLOCKED"
    assert "next_best_evidence" in state_stage5
    assert len(state_stage5["next_best_evidence"]) >= 2
    assert state_stage5["next_best_evidence"][0]["id"] == "NBA-001"
    assert state_stage5["next_best_evidence"][0]["status"] == "READY"
    assert state_stage5["next_best_evidence"][1]["status"] == "PENDING"

    # Verify reasoning map has next_best_evidence nodes and connections
    reasoning_map = state_stage5["reasoning_map"]
    assert "next_best_evidence" in reasoning_map
    assert any(c.get("target_id") == "NBA-001" for c in reasoning_map.get("connections", []))

    # Execute action using alias "nba-1"
    res = client.post(f"/api/v1/fikracore/simulations/{run.run_id}/actions", json={"action_id": "nba-1"})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "SUCCESS"
    assert body["action_status"] == "COMPLETED"

    # Verify run advanced to LEARNING_VALIDATION
    state_after = manager.get_state(scenario_id="SCN-001", run_id=run.run_id)
    assert state_after["current_stage"] == "LEARNING_VALIDATION"
    assert state_after["next_best_evidence"][0]["status"] == "COMPLETED"
    assert state_after["next_best_evidence"][1]["status"] == "READY"

    # Verify another scenario has scenario-specific trigger in action display_name
    run_h4 = manager.create_run(scenario_id="H4-WI-001", speed=1.0, mode="live")
    run_h4.stage_index = 5
    state_h4 = manager.get_state(scenario_id="H4-WI-001", run_id=run_h4.run_id)
    assert state_h4["next_best_evidence"][0]["id"] == "NBA-001"
    assert "Router" in state_h4["next_best_evidence"][0]["display_name"] or "Edge" in state_h4["next_best_evidence"][0]["display_name"]


