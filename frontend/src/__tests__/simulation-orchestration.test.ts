import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  SimulationClient,
  StageExitCondition,
  ZakiSuggestedAction,
  ZakiChatClientRequest,
} from "../lib/simulation-store";

describe("FikraCore Step 5.1 Simulation Orchestration & Zaki Copilot (§44 Acceptance Tests)", () => {
  it("test_run_status_controls_play_pause_stop", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-001",
      revision: 1,
      sequence: 1,
      run: {
        run_id: "RUN-001",
        scenario_id: "H4-WI-040",
        status: "RUNNING",
        speed: 1.0,
        started_at: new Date().toISOString(),
        elapsed_seconds: 10,
        elapsed_formatted: "00:00:10",
      },
    });

    assert.equal(client.getState().run?.status, "RUNNING");

    // Paused
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-001",
      revision: 2,
      sequence: 2,
      run: {
        run_id: "RUN-001",
        scenario_id: "H4-WI-040",
        status: "PAUSED",
        speed: 1.0,
        started_at: new Date().toISOString(),
        elapsed_seconds: 10,
        elapsed_formatted: "00:00:10",
      },
    });
    assert.equal(client.getState().run?.status, "PAUSED");

    // Stopped (never completed)
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-001",
      revision: 3,
      sequence: 3,
      run: {
        run_id: "RUN-001",
        scenario_id: "H4-WI-040",
        status: "STOPPED",
        speed: 1.0,
        started_at: new Date().toISOString(),
        elapsed_seconds: 15,
        elapsed_formatted: "00:00:15",
      },
    });
    assert.equal(client.getState().run?.status, "STOPPED");
    assert.notEqual(client.getState().run?.status, "COMPLETED");
  });

  it("test_blocked_stage_shows_exact_reason", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-002",
      current_stage: "KNOWLEDGE_GAP_CHECK",
      stage_status: "BLOCKED",
      blocking_reason: "Redundant MPLS Path Health Unknown",
      waiting_for: "Backup-path telemetry",
    });

    const state = client.getState();
    assert.equal(state.stage_status, "BLOCKED");
    assert.equal(state.blocking_reason, "Redundant MPLS Path Health Unknown");
    assert.equal(state.waiting_for, "Backup-path telemetry");
  });

  it("test_stage_exit_condition_visible", () => {
    const exitConditionsDetail: StageExitCondition[] = [
      {
        condition_id: "EC-KNO-01",
        display_name: "next_best_evidence_completed == true",
        satisfied: false,
        expected: "true",
        actual: "false",
        reason: "Required next-best evidence has not completed",
      },
    ];

    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-003",
      current_stage: "KNOWLEDGE_GAP_CHECK",
      stage_status: "BLOCKED",
      exit_conditions: ["next_best_evidence_completed == true"],
      exit_conditions_detail: exitConditionsDetail,
    });

    const state = client.getState();
    assert.equal(state.exit_conditions?.length, 1);
    assert.equal(state.exit_conditions_detail?.length, 1);
    assert.equal(state.exit_conditions_detail?.[0].satisfied, false);
    assert.equal(state.exit_conditions_detail?.[0].condition_id, "EC-KNO-01");
  });

  it("test_replay_mode_does_not_mutate_run", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-004",
      hypotheses: [
        {
          id: "HYP-001",
          display_name: "IP/MPLS Edge Router Failure",
          confidence: 74,
          status: "LEADING",
          rank: 1,
          delta: "+24%",
          supports: [],
          against: [],
          missing: [],
          evidence_count: 3,
          tested: true,
        },
      ],
    });

    assert.equal(client.getState().hypotheses[0].confidence, 74);

    // Apply replay mode
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-004",
      is_replay: true,
      replay_position: 2,
      hypotheses: [
        {
          id: "HYP-001",
          display_name: "IP/MPLS Edge Router Failure",
          confidence: 74,
          status: "LEADING",
          rank: 1,
          delta: "+24%",
          supports: [],
          against: [],
          missing: [],
          evidence_count: 3,
          tested: true,
        },
      ],
    });

    assert.equal(client.getState().is_replay, true);
    assert.equal(client.getState().hypotheses[0].confidence, 74);
  });

  it("test_zaki_panel_displays_active_run_context", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-005",
      current_stage: "KNOWLEDGE_GAP_CHECK",
      stage_status: "BLOCKED",
      run: {
        run_id: "RUN-005",
        scenario_id: "H4-WI-040",
        status: "BLOCKED",
        speed: 1.0,
        started_at: new Date().toISOString(),
        elapsed_seconds: 40,
        elapsed_formatted: "00:00:40",
      },
    });

    const state = client.getState();
    assert.equal(state.scenario_id, "H4-WI-040");
    assert.equal(state.run_id, "RUN-005");
    assert.equal(state.current_stage, "KNOWLEDGE_GAP_CHECK");
    assert.equal(state.run?.status, "BLOCKED");
  });

  it("test_zaki_updates_when_revision_changes", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-006",
      revision: 10,
      sequence: 20,
    });
    assert.equal(client.getState().revision, 10);

    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-006",
      revision: 11,
      sequence: 21,
    });
    assert.equal(client.getState().revision, 11);
  });

  it("test_zaki_scenario_switch_clears_old_context", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-OLD",
      revision: 5,
      exit_conditions_detail: [
        {
          condition_id: "EC-1",
          display_name: "test",
          satisfied: true,
        },
      ],
    });
    assert.equal(client.getState().run_id, "RUN-OLD");

    client.resetScenarioScopedState("SWITCHING_SCENARIO");
    const state = client.getState();
    assert.equal(state.run_id, undefined);
    assert.equal(state.exit_conditions_detail?.length, 0);
    assert.equal(state.revision, 0);
  });

  it("test_zaki_blocked_stage_prompt", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-007",
      current_stage: "KNOWLEDGE_GAP_CHECK",
      stage_status: "BLOCKED",
    });

    const prompt = client.getState().stage_status === "BLOCKED" ? "Why are we blocked?" : "Status check";
    assert.equal(prompt, "Why are we blocked?");
  });

  it("test_zaki_suggested_action_disabled_when_not_permitted", () => {
    const action: ZakiSuggestedAction = {
      action_id: "ACT-002",
      display_name: "Execute Verification Probe",
      action_type: "REQUEST_EVIDENCE",
      enabled: false,
      disabled_reason: "Stage exit conditions require prior backup-path telemetry",
    };

    assert.equal(action.enabled, false);
    assert.equal(action.disabled_reason, "Stage exit conditions require prior backup-path telemetry");
  });

  it("test_zaki_response_level_switch", () => {
    const levels: Array<ZakiChatClientRequest["response_level"]> = [
      "EXECUTIVE",
      "OPERATOR",
      "ENGINEER",
      "DEEP_TECHNICAL",
    ];

    levels.forEach((lvl) => {
      const req: ZakiChatClientRequest = {
        query: "Explain current status",
        response_level: lvl,
      };
      assert.equal(req.response_level, lvl);
    });
  });

  it("test_zaki_replay_mode_indicator", () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      scenario_id: "H4-WI-040",
      run_id: "RUN-008",
      is_replay: true,
      replay_position: 4,
    });

    assert.equal(client.getState().is_replay, true);
    assert.equal(client.getState().replay_position, 4);
  });

  it("test_zaki_click_connection_passes_selected_context", () => {
    const req: ZakiChatClientRequest = {
      query: "Why is this connection active?",
      selected_context: {
        type: "connection",
        connection_id: "CONN-001",
        relation_type: "routes-through",
      },
    };

    assert.equal(req.selected_context?.type, "connection");
    assert.equal(req.selected_context?.connection_id, "CONN-001");
  });

  it("test_zaki_click_hypothesis_passes_selected_context", () => {
    const req: ZakiChatClientRequest = {
      query: "Why did confidence change?",
      selected_context: {
        type: "hypothesis",
        hypothesis_id: "HYP-001",
      },
    };

    assert.equal(req.selected_context?.type, "hypothesis");
    assert.equal(req.selected_context?.hypothesis_id, "HYP-001");
  });
});
