import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { SimulationClient } from "../lib/simulation-store";
import {
  buildPathwayItems,
  buildHypothesisItems,
  buildGapItems,
  resolveConduitTelemetry,
  HypothesisItem,
} from "../app/simulator/investigate/page";

describe("FikraCore Step 5 Frontend Store & Visual Activation (§ Acceptance Tests)", () => {
  it("test_scenario_switch_clears_previous_run", () => {
    const client = new SimulationClient(() => {});

    // Hydrate initial scenario SCN-001 run
    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-001",
      revision: 1,
      sequence: 1,
      events: [{ event_id: "ev-1", category: "alarm", title: "Alarm 1" }],
      hypotheses: [{ id: "H1", display_name: "Hypothesis 1", confidence: 50 }],
      reasoning_map: {
        scenario_id: "SCN-001",
        run_id: "RUN-001",
        revision: 1,
        sequence: 1,
        evidence: [],
        reasoning_pathways: [],
        hypotheses: [],
      },
    });

    assert.equal(client.getState().scenario_id, "SCN-001");
    assert.equal(client.getState().run_id, "RUN-001");
    assert.equal(client.getState().events.length, 1);

    // Switch scenario
    client.resetScenarioScopedState("SWITCHING_SCENARIO");

    const state = client.getState();
    assert.equal(state.run_id, undefined, "Previous run_id must be cleared");
    assert.equal(state.run, null, "Previous run meta must be cleared");
    assert.equal(state.events.length, 0, "Previous events must be cleared");
    assert.equal(state.hypotheses.length, 0, "Previous hypotheses must be cleared");
    assert.equal(state.reasoningMap, null, "Previous reasoning map must be cleared");
    assert.equal(state.revision, 0, "Revision must reset to 0");
    assert.equal(state.sequence, 0, "Sequence must reset to 0");
    assert.equal(state.syncState, "SWITCHING_SCENARIO");
  });

  it("test_snapshot_atomically_hydrates_ui", () => {
    const client = new SimulationClient(() => {});

    const snapshot = {
      scenario_id: "SCN-001",
      run_id: "RUN-100",
      revision: 4,
      sequence: 8,
      stages: [{ index: 1, key: "stage-1", label: "Stage 1", status: "ACTIVE" }],
      events: [
        { event_id: "e1", category: "alarm", title: "Alarm A", severity: "critical", state: "CONFIRMED" },
        { event_id: "e2", category: "metric", title: "Metric B", severity: "warning", state: "OBSERVED" },
      ],
      hypotheses: [
        { id: "H1", display_id: "H1", display_name: "Primary Candidate", confidence: 85, status: "LEADING" },
      ],
      reasoning_map: {
        scenario_id: "SCN-001",
        run_id: "RUN-100",
        revision: 4,
        sequence: 8,
        reasoning_pathways: [
          { display_name: "Service Dependency", status: "ACTIVE", activation_reason: "Topology match" },
        ],
        hypotheses: [
          { display_id: "H1", display_name: "Primary Candidate", confidence: 85, status: "LEADING" },
        ],
      },
      zaki: {
        phase: "REASONING",
        thought: "Analyzing failure domain",
        active_focus_entity: "Router-07",
        confidence: 85,
      },
    };

    client.applySnapshot(snapshot);

    const state = client.getState();
    assert.equal(state.scenario_id, "SCN-001");
    assert.equal(state.run_id, "RUN-100");
    assert.equal(state.revision, 4);
    assert.equal(state.sequence, 8);
    assert.equal(state.events.length, 2);
    assert.equal(state.hypotheses.length, 1);
    assert.notEqual(state.reasoningMap, null);
    assert.equal(state.reasoningMap?.reasoning_pathways.length, 1);
    assert.equal(state.zaki?.confidence, 85);
  });

  it("test_wrong_run_event_ignored", () => {
    const client = new SimulationClient(() => {});

    // Establish active run RUN-001
    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-001",
      revision: 2,
      sequence: 5,
    });

    // Delta from another run RUN-999
    client.handleLiveDelta({
      scenario_id: "SCN-001",
      run_id: "RUN-999",
      revision: 3,
      sequence: 6,
      current_stage: "STAGE_LEAK",
    });

    const state = client.getState();
    assert.equal(state.run_id, "RUN-001");
    assert.equal(state.current_stage, undefined, "Delta from wrong run must be rejected");
    assert.equal(state.revision, 2);
    assert.equal(state.sequence, 5);
  });

  it("test_stale_revision_ignored", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-001",
      revision: 5,
      sequence: 10,
    });

    // Send stale revision
    client.handleLiveDelta({
      scenario_id: "SCN-001",
      run_id: "RUN-001",
      revision: 4, // Stale!
      sequence: 11,
      current_stage: "STAGE_STALE_REV",
    });

    assert.equal(client.getState().current_stage, undefined, "Stale revision must be dropped");

    // Send non-monotonic sequence
    client.handleLiveDelta({
      scenario_id: "SCN-001",
      run_id: "RUN-001",
      revision: 5,
      sequence: 9, // Stale sequence!
      current_stage: "STAGE_STALE_SEQ",
    });

    assert.equal(client.getState().current_stage, undefined, "Stale sequence must be dropped");
  });

  it("test_dormant_pathway_dimmed", () => {
    const simulationState = {
      reasoningMap: {
        reasoning_pathways: [
          {
            display_name: "Service Dependency",
            status: "DORMANT",
            activation_reason: "Awaiting dependency telemetry",
          },
        ],
      },
    };

    const pathways = buildPathwayItems(simulationState);
    const serviceDep = pathways.find((p) => p.name.includes("Service Dependency"));
    assert.ok(serviceDep, "Service Dependency pathway must exist");
    assert.equal(serviceDep?.active, false, "Dormant pathway must have active: false for dimmed visual");
    assert.equal(serviceDep?.reason, "Awaiting dependency telemetry");
  });

  it("test_active_pathway_lit", () => {
    const simulationState = {
      reasoningMap: {
        reasoning_pathways: [
          {
            display_name: "Traffic & Capacity",
            status: "ACTIVE",
            activation_reason: "Bandwidth saturation detected on link-02",
          },
        ],
      },
    };

    const pathways = buildPathwayItems(simulationState);
    const trafficPw = pathways.find((p) => p.name.includes("Traffic & Capacity"));
    assert.ok(trafficPw, "Traffic & Capacity pathway must exist");
    assert.equal(trafficPw?.active, true, "Active pathway must have active: true for lit visual");
    assert.equal(trafficPw?.reason, "Bandwidth saturation detected on link-02");
  });

  it("test_support_connection_green", () => {
    const hypothesesList: HypothesisItem[] = [
      {
        id: "H1",
        code: "H1",
        name: "MPLS Edge Router Failure",
        confidence: 72,
        delta: "+8%",
        deltaIsPos: true,
        status: "LEADING",
        color: "#34d399",
        progressColor: "bg-emerald-400",
      },
    ];

    const telemetry = resolveConduitTelemetry(
      { type: "conduit-core-hyp", hypIdx: 0 },
      hypothesesList,
      {
        scenario_id: "SCN-001",
        run_id: "RUN-001",
        revision: 2,
        sequence: 4,
        reasoningMap: {
          synthesis: { summary: "Bayesian convergence supports H1", state: "STRONGLY_SUPPORTED" },
        },
      }
    );

    assert.ok(telemetry, "Telemetry must resolve");
    assert.equal(telemetry?.supportType, "SUPPORTS", "Support connection must be SUPPORTS (green)");
    assert.equal(telemetry?.backendReason, "Bayesian convergence supports H1");
  });

  it("test_contradiction_connection_red", () => {
    const hypothesesList: HypothesisItem[] = [
      {
        id: "H2",
        code: "H2",
        name: "SGW Overload",
        confidence: 15,
        delta: "-12%",
        deltaIsPos: false, // Contradicting
        status: "COMPETING",
        color: "#60a5fa",
        progressColor: "bg-blue-400",
      },
    ];

    const telemetry = resolveConduitTelemetry(
      { type: "conduit-core-hyp", hypIdx: 0 },
      hypothesesList,
      {
        scenario_id: "SCN-001",
        run_id: "RUN-001",
        revision: 2,
        sequence: 4,
        reasoningMap: {
          synthesis: { summary: "SGW CPU load nominal, contradicting overload", state: "CONVERGING" },
        },
      }
    );

    assert.ok(telemetry, "Telemetry must resolve");
    assert.equal(telemetry?.supportType, "CONTRADICTS", "Contradiction connection must be CONTRADICTS (red)");
  });

  it("test_gap_amber", () => {
    const simulationState = {
      reasoningMap: {
        knowledge_gaps: [
          {
            id: "gap-01",
            display_name: "Redundant MPLS Standby Path Telemetry",
            required_evidence: "SNMP poll on Router-08 standby interface",
            status: "OPEN",
          },
        ],
      },
    };

    const gaps = buildGapItems(simulationState);
    assert.equal(gaps.length, 1);
    assert.equal(gaps[0].title, "Redundant MPLS Standby Path Telemetry");
    assert.equal(gaps[0].subtitle, "SNMP poll on Router-08 standby interface");
    assert.equal(gaps[0].severity, "High"); // High severity maps to amber border/badge in UI
  });

  it("test_rejected_hypothesis_faded", () => {
    const simulationState = {
      reasoningMap: {
        hypotheses: [
          {
            display_id: "H2",
            display_name: "SGW Overload",
            state: "REJECTED",
            confidence: 5,
            delta: "-25%",
          },
        ],
      },
    };

    const hypItems = buildHypothesisItems(simulationState);
    const h2 = hypItems.find((h) => h.code === "H2");
    assert.ok(h2, "H2 must exist");
    assert.equal(h2?.status, "REJECTED", "Rejected hypothesis must have status REJECTED for faded UI rendering");
    assert.equal(h2?.confidence, 5);
  });

  it("test_h1_h4_visible", () => {
    const simulationState = {
      reasoningMap: {
        hypotheses: [
          { display_id: "H1", display_name: "MPLS Core Hardware Fault", confidence: 80, state: "LEADING" },
          { display_id: "H2", display_name: "SGW Congestion", confidence: 20, state: "COMPETING" },
          { display_id: "H3", display_name: "DNS Resolution Delay", confidence: 10, state: "COMPETING" },
          { display_id: "H4", display_name: "BGP Route Leak", confidence: 5, state: "REJECTED" },
        ],
      },
    };

    const hypItems = buildHypothesisItems(simulationState);
    assert.equal(hypItems.length, 4, "All 4 hypotheses H1-H4 must be visible");
    assert.deepEqual(
      hypItems.map((h) => h.code),
      ["H1", "H2", "H3", "H4"]
    );
    assert.equal(hypItems[0].name, "MPLS Core Hardware Fault");
    assert.equal(hypItems[3].name, "BGP Route Leak");
  });

  it("test_all_panels_share_revision", () => {
    const client = new SimulationClient(() => {});
    const sharedRevision = 7;
    const sharedSequence = 14;

    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-042",
      revision: sharedRevision,
      sequence: sharedSequence,
      reasoning_map: {
        scenario_id: "SCN-001",
        run_id: "RUN-042",
        revision: sharedRevision,
        sequence: sharedSequence,
      },
    });

    const state = client.getState();
    assert.equal(state.revision, sharedRevision, "State revision matches");
    assert.equal(state.reasoningMap?.revision, sharedRevision, "ReasoningMap revision matches");

    // Telemetry resolve for conduits also inherits the exact shared revision
    const telemetry = resolveConduitTelemetry(
      { type: "conduit-p-core", pathwayIdx: 0 },
      undefined,
      state
    );
    assert.ok(telemetry?.provenance.hash.includes(`rev:${sharedRevision}#seq:${sharedSequence}`), "Conduit shares authoritative revision and sequence");
  });

  it("test_zaki_uses_active_run", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-AUTHORITATIVE",
      revision: 3,
      sequence: 6,
      zaki: {
        phase: "RECOMMENDATION_READY",
        thought: "Authoritative recommendation based on active run evidence",
        active_focus_entity: "Router-07",
        confidence: 94,
      },
    });

    const state = client.getState();
    assert.equal(state.run_id, "RUN-AUTHORITATIVE");
    assert.equal(state.zaki?.phase, "RECOMMENDATION_READY");
    assert.equal(state.zaki?.active_focus_entity, "Router-07");
    assert.equal(state.zaki?.confidence, 94);

    // Delta from another run cannot touch active Zaki state
    client.handleLiveDelta({
      scenario_id: "SCN-001",
      run_id: "RUN-ROGUE",
      zaki: {
        phase: "OBSERVING",
        thought: "Stale run thinking",
        active_focus_entity: "Wrong-Device",
        confidence: 10,
      },
    });

    const unchangedState = client.getState();
    assert.equal(unchangedState.run_id, "RUN-AUTHORITATIVE");
    assert.equal(unchangedState.zaki?.confidence, 94);
    assert.equal(unchangedState.zaki?.active_focus_entity, "Router-07");
  });
});
