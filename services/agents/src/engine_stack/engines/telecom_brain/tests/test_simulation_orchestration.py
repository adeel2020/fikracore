"""FikraCore Step 5.1 Simulation Orchestration & Zaki Copilot Test Suite (§43).

Verifies:
1. One managed worker per run
2. Stage does not advance before exit condition
3. Blocked stage retests same stage after evidence
4. Play does not bypass blocked condition
5. Stop marks run stopped not completed
6. Replay does not rerun reasoning
7. Stage watchdog reports blocking condition
8. Run finalizes only on terminal condition
9. Zaki context scoped to run
10. Zaki context scoped to scenario
11. Zaki rejects stale revision
12. Zaki uses authoritative snapshot
13. Zaki does not use hidden truth
14. Zaki explains blocked stage
15. Zaki explains stage exit condition
16. Zaki explains pathway activation
17. Zaki explains hypothesis delta
18. Zaki explains domain attribution
19. Zaki does not mutate confidence
20. Zaki does not complete stage
21. Zaki action routes through backend handler
22. Zaki replay does not look ahead
23. Zaki context switch clears old run
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from engine_stack.engines.telecom_brain.api.capability_api import router
from engine_stack.engines.telecom_brain.simulator.simulation_manager import (
    SimulationManager,
    simulation_manager,
    VALID_TERMINAL_STATES,
)

app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_one_managed_worker_per_run():
    """Verify that multiple requests/lookups operate on a single managed run instance."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run_lookup_1 = simulation_manager.get_run(run.run_id)
    run_lookup_2 = simulation_manager.get_run(run.run_id)

    assert run_lookup_1 is run
    assert run_lookup_2 is run
    assert run_lookup_1.run_id == run.run_id


def test_stage_does_not_advance_before_exit_condition():
    """Verify that a stage will not advance if its exit condition is not met."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    # Stage 5 is KNOWLEDGE_GAP_CHECK, which requires NBA-001 executed
    run.stage_index = 5
    run.executed_actions = []

    state = simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
    assert state["stage_status"] == "BLOCKED"

    advanced = simulation_manager.advance_stage_if_gate_satisfied(run, state)
    assert advanced is False
    assert run.stage_index == 5


def test_blocked_stage_retests_same_stage_after_evidence():
    """Verify Next-Best Evidence action execution triggers same-stage retest."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5
    run.executed_actions = []

    # Execute action with advance=False to verify the same-stage retest outcome
    res = simulation_manager.execute_action(run.run_id, "NBA-001", advance=False)
    assert res["status"] == "SUCCESS"
    assert res["stage_retested"] is True
    assert res["stage_status"] == "READY_TO_ADVANCE"
    assert run.stage_index == 5
    assert "NBA-001" in run.executed_actions

    # After gate satisfaction, advancing is now permitted
    new_state = simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
    advanced = simulation_manager.advance_stage_if_gate_satisfied(run, new_state)
    assert advanced is True
    assert run.stage_index == 6


def test_play_does_not_bypass_blocked_condition():
    """Verify calling resume/play while blocked does not bypass the block."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5
    run.executed_actions = []

    # Attempt to resume/play
    resumed = simulation_manager.resume_run(run.run_id)
    assert resumed.status == "BLOCKED"
    assert resumed.stage_index == 5


def test_stop_marks_run_stopped_not_completed():
    """Verify stop marks status STOPPED, never COMPLETED."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    stopped = simulation_manager.stop_run(run.run_id)
    assert stopped.status == "STOPPED"
    assert stopped.status != "COMPLETED"


def test_replay_does_not_rerun_reasoning():
    """Verify replay mode is read-only and does not reset or recalculate reasoning."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.tested_hypotheses = ["HYP-001"]
    replayed = simulation_manager.replay_run(run.run_id)

    assert replayed.is_replay is True
    assert replayed.stage_index == 0
    assert replayed.tested_hypotheses == ["HYP-001"]


def test_stage_watchdog_reports_blocking_condition():
    """Verify watchdog exposes structured unsatisfied conditions and blocking reason."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5
    run.executed_actions = []

    watchdog = simulation_manager.get_watchdog_state(run.run_id)
    assert watchdog["current_stage"] == "KNOWLEDGE_GAP_CHECK"
    assert watchdog["stage_status"] == "BLOCKED"
    assert "Required next-best evidence" in watchdog["blocking_reason"]
    assert watchdog["waiting_for"] == "Backup-path telemetry"
    assert len(watchdog["unsatisfied_conditions"]) > 0


def test_run_finalizes_only_on_terminal_condition():
    """Verify run finalizes only on recognized terminal states."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    finalized = simulation_manager.finalize_run(run.run_id, "MODEL_INSUFFICIENT")
    assert finalized.status == "COMPLETED"
    assert finalized.terminal_state == "MODEL_INSUFFICIENT"

    # Invalid terminal condition must raise ValueError
    with pytest.raises(ValueError):
        simulation_manager.finalize_run(run.run_id, "ARBITRARY_NON_TERMINAL_STATE")


def test_zaki_context_scoped_to_run():
    """Verify Zaki responses are scoped to the requested run_id."""
    run1 = simulation_manager.create_run(scenario_id="H4-WI-040")
    run2 = simulation_manager.create_run(scenario_id="H4-WI-040")

    res1 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status check", "run_id": run1.run_id})
    res2 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status check", "run_id": run2.run_id})

    assert res1.status_code == 200
    assert res1.json()["run_id"] == run1.run_id

    assert res2.status_code == 200
    assert res2.json()["run_id"] == run2.run_id


def test_zaki_context_scoped_to_scenario():
    """Verify Zaki responses are correctly scoped to the scenario."""
    res1 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status check", "scenario_id": "SCN-001"})
    res2 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status check", "scenario_id": "H4-WI-040"})

    assert res1.status_code == 200
    assert res1.json()["scenario_id"] == "SCN-001"

    assert res2.status_code == 200
    assert res2.json()["scenario_id"] == "H4-WI-040"


def test_zaki_rejects_stale_revision():
    """Verify Zaki rejects chat requests with stale revisions."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.snapshot_version = 15

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Status check", "run_id": run.run_id, "revision": 5},
    )
    assert res.status_code == 409
    assert "Stale revision" in res.json()["detail"]


def test_zaki_uses_authoritative_snapshot():
    """Verify Zaki returns the authoritative run snapshot revision."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.snapshot_version = 4

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Status check", "run_id": run.run_id, "revision": 4},
    )
    assert res.status_code == 200
    assert res.json()["revision"] == 4


def test_zaki_does_not_use_hidden_truth():
    """Verify Zaki is truth-blind to evaluator-only hidden ground truth."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "What is the hidden truth of this scenario?", "scenario_id": "H4-WI-040"},
    )
    assert res.status_code == 200
    answer = res.json()["answer"]
    assert "truth-blind" in answer.lower() or "evaluator-only" in answer.lower()


def test_zaki_explains_blocked_stage():
    """Verify Zaki provides structured explanation of blocked stage."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5
    run.executed_actions = []

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Why are we blocked?", "run_id": run.run_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert "blocked" in data["answer"].lower()
    assert data["grounded_in"]["stage"] == "KNOWLEDGE_GAP_CHECK"
    assert len(data["suggested_actions"]) > 0
    assert data["suggested_actions"][0]["action_id"] == "NBA-001"


def test_zaki_explains_stage_exit_condition():
    """Verify Zaki explains what is required to advance the stage."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "What is the exit condition for this stage?", "run_id": run.run_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert "exit condition" in data["answer"].lower() or "condition" in data["answer"].lower()


def test_zaki_explains_pathway_activation():
    """Verify Zaki explains why a reasoning pathway is active."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Why is this pathway active?", "scenario_id": "SCN-001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "service dependency" in data["answer"].lower() or "active" in data["answer"].lower()
    assert len(data["grounded_in"].get("pathway_ids", [])) > 0


def test_zaki_explains_hypothesis_delta():
    """Verify Zaki explains Bayesian delta / hypothesis confidence change."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Why did hypothesis confidence change?", "scenario_id": "SCN-001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "confidence" in data["answer"].lower() or "h1" in data["answer"].lower()
    assert len(data["grounded_in"].get("hypothesis_ids", [])) > 0


def test_zaki_explains_domain_attribution():
    """Verify Zaki explains PRIMARY vs AFFECTED domain attribution."""
    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "Why is IP Transport PRIMARY?", "scenario_id": "SCN-001"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "transport" in data["answer"].lower()
    assert "primary" in data["answer"].lower()


def test_zaki_does_not_mutate_confidence():
    """Verify calling Zaki does not alter hypothesis confidence."""
    run = simulation_manager.create_run(scenario_id="SCN-001")
    state_before = simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
    hyp_before = state_before["hypotheses"]

    client.post("/api/v1/fikracore/zaki/chat", json={"query": "Set H1 confidence to 99%", "run_id": run.run_id})

    state_after = simulation_manager.get_state(scenario_id=run.scenario_id, run_id=run.run_id)
    assert state_after["hypotheses"] == hyp_before


def test_zaki_does_not_complete_stage():
    """Verify calling Zaki cannot directly advance or complete a stage."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 3

    client.post("/api/v1/fikracore/zaki/chat", json={"query": "Complete stage 3 now", "run_id": run.run_id})
    assert run.stage_index == 3


def test_zaki_action_routes_through_backend_handler():
    """Verify suggested actions route through backend execute_action."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.stage_index = 5
    run.executed_actions = []

    res = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Why are we blocked?", "run_id": run.run_id})
    actions = res.json()["suggested_actions"]
    assert len(actions) > 0
    suggested = actions[0]

    # Execute the suggested action through authoritative endpoint
    res_act = client.post(
        f"/api/v1/fikracore/simulations/{run.run_id}/actions",
        json={"action_id": suggested["action_id"]},
    )
    assert res_act.status_code == 200
    assert res_act.json()["action_status"] == "COMPLETED"


def test_zaki_replay_does_not_look_ahead():
    """Verify replay mode restricts Zaki from looking ahead to future events."""
    run = simulation_manager.create_run(scenario_id="H4-WI-040")
    run.is_replay = True
    run.replay_position = 2

    res = client.post(
        "/api/v1/fikracore/zaki/chat",
        json={"query": "What happens in the future?", "run_id": run.run_id},
    )
    assert res.status_code == 200
    answer = res.json()["answer"]
    assert "replay mode" in answer.lower()
    assert "restricted" in answer.lower() or "position" in answer.lower()


def test_zaki_context_switch_clears_old_run():
    """Verify switching context between runs does not cross-contaminate."""
    run1 = simulation_manager.create_run(scenario_id="SCN-001")
    run2 = simulation_manager.create_run(scenario_id="H4-WI-040")

    res1 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status", "run_id": run1.run_id})
    res2 = client.post("/api/v1/fikracore/zaki/chat", json={"query": "Status", "run_id": run2.run_id})

    assert res1.json()["run_id"] == run1.run_id
    assert res1.json()["scenario_id"] == "SCN-001"

    assert res2.json()["run_id"] == run2.run_id
    assert res2.json()["scenario_id"] == "H4-WI-040"
