import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  SimulationClient,
  LiveIntentMeta,
} from "../lib/simulation-store";

describe("FikraCore Step 5.2 Live Reasoning Activation (§64 Frontend Tests)", () => {
  it("test_source_mode_switch", () => {
    const client = new SimulationClient(() => {});
    assert.equal(client.getState().source_mode, "SIMULATION");

    // Switch to LIVE_INTENT
    client.switchSourceMode("LIVE_INTENT");
    assert.equal(client.getState().source_mode, "LIVE_INTENT");
    assert.equal(client.getState().intent_id, null);
    assert.equal(client.getState().scenario_id, undefined);

    // Switch back to SIMULATION
    client.switchSourceMode("SIMULATION");
    assert.equal(client.getState().source_mode, "SIMULATION");
    assert.equal(client.getState().intent_id, null);
  });

  it("test_live_intent_selector_uses_backend_data", async () => {
    const client = new SimulationClient(() => {});
    const mockIntents: LiveIntentMeta[] = [
      {
        intent_id: "INTENT-APN-001",
        display_name: "Enterprise APN Success Below Target",
        service: "Enterprise APN",
        severity: "MAJOR",
        target: { metric: "attach_success_rate", operator: "<", threshold: 99.5 },
        observed: { value: 97.9, observed_at: new Date().toISOString() },
      },
      {
        intent_id: "INTENT-VOLTE-001",
        display_name: "VoLTE Call Setup Success Below Target",
        service: "VoLTE IMS",
        severity: "CRITICAL",
        target: { metric: "call_setup_success_rate", operator: "<", threshold: 98.0 },
        observed: { value: 95.2, observed_at: new Date().toISOString() },
      },
      {
        intent_id: "INTENT-5G-001",
        display_name: "5G Registration Success Below Target",
        service: "5G SA",
        severity: "MAJOR",
        target: { metric: "registration_success_rate", operator: "<", threshold: 99.0 },
        observed: { value: 96.5, observed_at: new Date().toISOString() },
      },
    ];

    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/fikracore/live/intents")) {
          return {
            ok: true,
            status: 200,
            json: async () => ({ intents: mockIntents }),
          } as unknown as Response;
        }
        return { ok: false, status: 404 } as unknown as Response;
      };

      const result = await client.loadLiveIntents();
      assert.equal(result.length, 3);
      assert.equal(client.getState().live_intents?.length, 3);
      assert.equal(client.getState().live_intents?.[0]?.intent_id, "INTENT-APN-001");
      assert.equal(client.getState().live_intents?.[1]?.intent_id, "INTENT-VOLTE-001");
      assert.equal(client.getState().live_intents?.[2]?.intent_id, "INTENT-5G-001");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("test_live_run_hydrates_existing_step5_panels", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      intent_id: "INTENT-APN-001",
      revision: 3,
      sequence: 5,
      stages: [
        { index: 1, key: "TRIGGER", label: "TRIGGER", status: "COMPLETED" },
        { index: 2, key: "SIGNAL_FLOOD", label: "SIGNAL_FLOOD", status: "ACTIVE" },
      ],
      topology: {
        domains: [],
        causal_path: [],
        confirmed_path_label: "Direct Path",
        path_confidence: 90,
      },
      hypotheses: [
        { id: "H1", display_name: "DNS Resolution Delay", confidence: 60, status: "LEADING" },
      ],
      impact: {
        service: "Enterprise APN",
        throughput_impact_pct: 12,
        regions_affected: 1,
        affected_users: 1200,
        affected_services: ["Enterprise APN"],
        affected_label: "Enterprise APN",
        trend_sparkline: [],
      },
      knowledge_gaps: [
        { id: "GAP-001", label: "Bearer Telemetry", reason: "Missing PGW session telemetry", priority: "HIGH" },
      ],
      learning: {
        status: "CANDIDATE",
        rule_id: "LRN-001",
        proposed_action: "Increase bearer query sampling",
      },
      zaki: {
        phase: "OBSERVING",
        thought: "Analyzing live intent violation",
        active_focus_entity: "PGW-01",
        confidence: 85,
      },
    });

    const state = client.getState();
    assert.equal(state.run_id, "RUN-LIVE-001");
    assert.equal(state.source_mode, "LIVE_INTENT");
    assert.equal(state.intent_id, "INTENT-APN-001");
    assert.equal(state.stages.length, 2);
    assert.ok(state.topology);
    assert.equal(state.hypotheses.length, 1);
    assert.equal(state.impact?.affected_services?.[0], "Enterprise APN");
    assert.equal(state.knowledgeGaps.length, 1);
    assert.equal(state.learning?.status, "CANDIDATE");
    assert.equal(state.zaki?.phase, "OBSERVING");
  });

  it("test_live_evidence_progressive_render", () => {
    const client = new SimulationClient(() => {});

    // Initial state: 1 alarm event
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      intent_id: "INTENT-APN-001",
      raw_events: [
        { event_id: "EV-001", title: "APN Attach Drop", category: "alarm", severity: "critical" },
      ],
      evidence_clusters: [
        { cluster_id: "C-1", label: "Access Alarms", event_ids: ["EV-001"], entity_ids: [], signal_count: 1, noise_count: 0, confidence: 90 },
      ],
    });

    assert.equal(client.getState().rawEvents?.length, 1);
    assert.equal(client.getState().evidenceClusters?.length, 1);

    // Delta update: metric event arrives progressively
    client.handleLiveDelta({
      run_id: "RUN-LIVE-001",
      raw_events: [
        { event_id: "EV-001", title: "APN Attach Drop", category: "alarm", severity: "critical" },
        { event_id: "EV-002", title: "DNS Query Latency Spike", category: "metric", severity: "warning" },
      ],
      evidence_clusters: [
        { cluster_id: "C-1", label: "Access Alarms", event_ids: ["EV-001"], entity_ids: [], signal_count: 1, noise_count: 0, confidence: 90 },
        { cluster_id: "C-2", label: "DNS Metrics", event_ids: ["EV-002"], entity_ids: [], signal_count: 1, noise_count: 0, confidence: 85 },
      ],
    });

    assert.equal(client.getState().rawEvents?.length, 2);
    assert.equal(client.getState().evidenceClusters?.length, 2);
  });

  it("test_live_pathway_activation_backend_driven", () => {
    const client = new SimulationClient(() => {});

    // Backend initially activates only Operational Evidence pathway
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      reasoning_map: {
        contract_version: 1,
        run_id: "RUN-LIVE-001",
        scenario_id: "LIVE-INTENT-APN-001",
        source_mode: "LIVE_INTENT",
        revision: 1,
        sequence: 1,
        stage: "SIGNAL_FLOOD",
        source: {
          scenario_id: "LIVE-INTENT-APN-001",
          run_id: "RUN-LIVE-001",
          source_mode: "LIVE_INTENT",
          revision: 1,
          sequence: 1,
        },
        evidence: [],
        reasoning_pathways: [
          {
            pathway_id: "PW-OP",
            index: 0,
            display_name: "Operational Evidence",
            status: "ACTIVE",
            activation_reason: "Incoming live evidence",
            active_node_count: 2,
            total_node_count: 5,
            last_transition: "ACTIVATED",
          },
          {
            pathway_id: "PW-DEP",
            index: 1,
            display_name: "Service Dependency",
            status: "DORMANT",
            activation_reason: "Awaiting topology correlation",
            active_node_count: 0,
            total_node_count: 4,
            last_transition: "DORMANT",
          },
        ],
        connections: [],
        hypotheses: [],
        knowledge_gaps: [],
        next_best_evidence: [],
        synthesis: {
          id: "SYN-1",
          display_name: "Synthesis",
          state: "INSUFFICIENT_EVIDENCE",
          summary: "Initial operational signal flood",
          dimensions: [],
          explain: {
            why_pathway_active: { "PW-OP": "Incoming live evidence" },
            why_connection_active: {},
            why_hypothesis_rank: {},
            what_unblocks_stage: [],
          },
        },
        explain: {
          why_pathway_active: { "PW-OP": "Incoming live evidence" },
          why_connection_active: {},
          why_hypothesis_rank: {},
          what_unblocks_stage: [],
        },
      },
    });

    const pathways = client.getState().reasoningMap?.reasoning_pathways || [];
    assert.equal(pathways[0]?.status, "ACTIVE");
    assert.equal(pathways[1]?.status, "DORMANT");

    // Later backend activates Service Dependency pathway
    const updatedMap = {
      ...client.getState().reasoningMap!,
      reasoning_pathways: [
        { ...pathways[0]!, status: "ACTIVE" as const },
        { ...pathways[1]!, status: "ACTIVE" as const, activation_reason: "Topology match found" },
      ],
    };
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      reasoning_map: updatedMap,
    });

    const updatedPathways = client.getState().reasoningMap?.reasoning_pathways || [];
    assert.equal(updatedPathways[0]?.status, "ACTIVE");
    assert.equal(updatedPathways[1]?.status, "ACTIVE");
  });

  it("test_live_hypotheses_progressive", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      hypotheses: [
        { id: "H1", display_name: "DNS Resolution Delay", confidence: 40, status: "CANDIDATE" },
        { id: "H2", display_name: "PGW Congestion", confidence: 30, status: "COMPETING" },
      ],
    });

    assert.equal(client.getState().hypotheses[0]?.confidence, 40);
    assert.equal(client.getState().hypotheses[0]?.status, "CANDIDATE");

    // Evolve hypotheses after evidence collection
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      hypotheses: [
        { id: "H1", display_name: "DNS Resolution Delay", confidence: 80, status: "LEADING" },
        { id: "H2", display_name: "PGW Congestion", confidence: 15, status: "COMPETING" },
      ],
    });

    assert.equal(client.getState().hypotheses[0]?.confidence, 80);
    assert.equal(client.getState().hypotheses[0]?.status, "LEADING");
    assert.equal(client.getState().hypotheses[1]?.confidence, 15);
  });

  it("test_live_gap_blocked_state", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      current_stage: "KNOWLEDGE_GAP_CHECK",
      stage_status: "BLOCKED",
      blocking_reason: "Awaiting PGW bearer telemetry from NetworkToolProvider",
      waiting_for: "KNOWLEDGE_GAP",
      knowledge_gaps: [
        { id: "GAP-LIVE-01", label: "Bearer Telemetry", reason: "Missing bearer telemetry", priority: "HIGH" },
      ],
    });

    const state = client.getState();
    assert.equal(state.current_stage, "KNOWLEDGE_GAP_CHECK");
    assert.equal(state.stage_status, "BLOCKED");
    assert.equal(state.blocking_reason, "Awaiting PGW bearer telemetry from NetworkToolProvider");
    assert.equal(state.waiting_for, "KNOWLEDGE_GAP");
    assert.equal(state.knowledgeGaps.length, 1);
    assert.equal(state.knowledgeGaps[0]?.id, "GAP-LIVE-01");
  });

  it("test_live_domain_attribution_delayed", () => {
    const client = new SimulationClient(() => {});

    // In early stage (TRIGGER), domain attribution must remain unassigned / pending
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      current_stage: "TRIGGER",
      reasoning_map: {
        contract_version: 1,
        run_id: "RUN-LIVE-001",
        scenario_id: "LIVE-INTENT-APN-001",
        source_mode: "LIVE_INTENT",
        revision: 1,
        sequence: 1,
        stage: "TRIGGER",
        source: {
          scenario_id: "LIVE-INTENT-APN-001",
          run_id: "RUN-LIVE-001",
          source_mode: "LIVE_INTENT",
          revision: 1,
          sequence: 1,
        },
        evidence: [],
        reasoning_pathways: [],
        connections: [],
        hypotheses: [],
        knowledge_gaps: [],
        next_best_evidence: [],
        synthesis: {
          id: "SYN-1",
          display_name: "Synthesis",
          state: "INSUFFICIENT_EVIDENCE",
          summary: "Trigger received",
          dimensions: [],
          explain: {
            why_pathway_active: {},
            why_connection_active: {},
            why_hypothesis_rank: {},
            what_unblocks_stage: [],
          },
        },
        domain_attribution: {
          id: "DA-1",
          status: "PENDING",
          domains: [],
          explain: {
            why_pathway_active: {},
            why_connection_active: {},
            why_hypothesis_rank: {},
            what_unblocks_stage: [],
          },
        },
        explain: {
          why_pathway_active: {},
          why_connection_active: {},
          why_hypothesis_rank: {},
          what_unblocks_stage: [],
        },
      },
    });

    assert.equal(client.getState().reasoningMap?.domain_attribution?.status, "PENDING");

    // In later stage (LEARNING_VALIDATION / ACTION), attribution emerges
    const updatedMap = {
      ...client.getState().reasoningMap!,
      stage: "ACTION",
      domain_attribution: {
        id: "DA-1",
        status: "READY" as const,
        domains: [{ display_name: "Core Network", role: "PRIMARY" as const }],
        explain: {
          why_pathway_active: {},
          why_connection_active: {},
          why_hypothesis_rank: {},
          what_unblocks_stage: [],
        },
      },
    };

    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      current_stage: "ACTION",
      reasoning_map: updatedMap,
    });

    assert.equal(client.getState().reasoningMap?.domain_attribution?.status, "READY");
    assert.equal(client.getState().reasoningMap?.domain_attribution?.domains[0]?.role, "PRIMARY");
  });

  it("test_live_zaki_context_header", async () => {
    const client = new SimulationClient(() => {});
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      intent_id: "INTENT-APN-001",
      revision: 4,
    });

    let sentPayload: Record<string, unknown> | null = null;
    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/v1/fikracore/zaki/chat")) {
          sentPayload = JSON.parse(init?.body as string);
          return {
            ok: true,
            status: 200,
            json: async () => ({
              run_id: "RUN-LIVE-001",
              response_text: "APN attach drop correlated with DNS latency.",
              phase: "RECOMMENDATION_READY",
              active_focus_entity: "DNS-01",
              confidence: 90,
            }),
          } as unknown as Response;
        }
        return { ok: false, status: 404 } as unknown as Response;
      };

      const response = await client.zakiChat({
        query: "What is the primary cause?",
        response_level: "ENGINEER",
      });

      assert.ok(sentPayload);
      assert.equal((sentPayload as Record<string, unknown>).source_mode, "LIVE_INTENT");
      assert.equal((sentPayload as Record<string, unknown>).intent_id, "INTENT-APN-001");
      assert.equal((sentPayload as Record<string, unknown>).run_id, "RUN-LIVE-001");
      assert.equal((sentPayload as Record<string, unknown>).revision, 4);
      assert.equal(response.run_id, "RUN-LIVE-001");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it("test_live_to_simulation_switch_clears_context", () => {
    const client = new SimulationClient(() => {});

    // Hydrate live state
    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      intent_id: "INTENT-APN-001",
      revision: 6,
      hypotheses: [{ id: "H1", display_name: "DNS", confidence: 50 }],
      raw_events: [{ event_id: "E1", title: "Live Alarm" }],
      knowledge_gaps: [{ id: "G1", label: "Gap 1", reason: "Missing telemetry", priority: "HIGH" }],
      zaki: {
        phase: "OBSERVING",
        thought: "Live thinking",
        active_focus_entity: "Router-1",
        confidence: 80,
      },
    });

    assert.equal(client.getState().source_mode, "LIVE_INTENT");
    assert.equal(client.getState().run_id, "RUN-LIVE-001");

    // Switch to SIMULATION
    client.switchSourceMode("SIMULATION");

    const state = client.getState();
    assert.equal(state.source_mode, "SIMULATION");
    assert.equal(state.run_id, undefined, "Live run_id must be cleared on mode switch");
    assert.equal(state.intent_id, null, "intent_id must be cleared");
    assert.equal(state.hypotheses.length, 0, "Live hypotheses must be cleared");
    assert.equal(state.rawEvents?.length, 0, "Live events must be cleared");
    assert.equal(state.knowledgeGaps.length, 0, "Live knowledge gaps must be cleared");
    assert.equal(state.zaki, null, "Live Zaki context must be cleared");
    assert.equal(state.revision, 0, "Revision must reset to 0");
  });

  it("test_simulation_to_live_switch_clears_context", () => {
    const client = new SimulationClient(() => {});

    // Hydrate simulation state
    client.applySnapshot({
      scenario_id: "SCN-001",
      run_id: "RUN-SIM-001",
      source_mode: "SIMULATION",
      revision: 8,
      hypotheses: [{ id: "H1", display_name: "Hardware Fault", confidence: 90 }],
      raw_events: [{ event_id: "E100", title: "Simulation Alarm" }],
    });

    assert.equal(client.getState().source_mode, "SIMULATION");
    assert.equal(client.getState().scenario_id, "SCN-001");
    assert.equal(client.getState().run_id, "RUN-SIM-001");

    // Switch to LIVE_INTENT
    client.switchSourceMode("LIVE_INTENT");

    const state = client.getState();
    assert.equal(state.source_mode, "LIVE_INTENT");
    assert.equal(state.scenario_id, undefined, "Simulation scenario_id must be cleared");
    assert.equal(state.run_id, undefined, "Simulation run_id must be cleared");
    assert.equal(state.hypotheses.length, 0, "Simulation hypotheses must be cleared");
    assert.equal(state.rawEvents?.length, 0, "Simulation events must be cleared");
    assert.equal(state.revision, 0, "Revision must reset to 0");
  });

  it("test_live_replay_mode_indicator", () => {
    const client = new SimulationClient(() => {});

    client.applySnapshot({
      run_id: "RUN-LIVE-001",
      scenario_id: "LIVE-INTENT-APN-001",
      source_mode: "LIVE_INTENT",
      intent_id: "INTENT-APN-001",
      is_replay: true,
      replay_position: 7,
    });

    const state = client.getState();
    assert.equal(state.source_mode, "LIVE_INTENT");
    assert.equal(state.is_replay, true);
    assert.equal(state.replay_position, 7);
  });
});
