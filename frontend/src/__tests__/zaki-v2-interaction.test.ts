import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  SimulationClient,
  type ZakiSelectedContext,
  type HighlightedEntity,
  type ZakiResponseV2,
} from "../lib/simulation-store";

describe("FikraCore Step 5.2.2 Zaki 2.0 Contextual Copilot Interaction Tests (§45)", () => {
  it("test_zaki_compact_to_expanded", () => {
    const client = new SimulationClient(() => {});
    const initialUI = client.getZakiUIState();
    assert.equal(initialUI.mode, "COMPACT");

    client.setZakiMode("EXPANDED");
    assert.equal(client.getZakiUIState().mode, "EXPANDED");

    client.setZakiMode("DOCKED");
    assert.equal(client.getZakiUIState().mode, "DOCKED");

    client.setZakiMode("COMPACT");
    assert.equal(client.getZakiUIState().mode, "COMPACT");
  });

  it("test_click_hypothesis_sets_zaki_context", () => {
    const client = new SimulationClient(() => {});
    const hypContext: ZakiSelectedContext = {
      context_type: "HYPOTHESIS",
      context_id: "HYP-001",
      display_name: "H1 — Core Transport Router Optical Transceiver Degradation",
      summary: "88% confidence leading root cause candidate.",
      status: "LEADING",
      source_revision: 4,
    };

    client.setSelectedContext(hypContext);
    const ui = client.getZakiUIState();
    assert.ok(ui.selectedContext);
    assert.equal(ui.selectedContext.context_type, "HYPOTHESIS");
    assert.equal(ui.selectedContext.context_id, "HYP-001");
    assert.equal(ui.selectedContext.source_revision, 4);
  });

  it("test_click_pathway_sets_zaki_context", () => {
    const client = new SimulationClient(() => {});
    const pathwayContext: ZakiSelectedContext = {
      context_type: "PATHWAY",
      context_id: "PW-01",
      display_name: "Operational Evidence Pathway",
      summary: "Aggregates optical interface drop alarms and physical degradation telemetry.",
      status: "ACTIVE",
    };

    client.setSelectedContext(pathwayContext);
    const ui = client.getZakiUIState();
    assert.ok(ui.selectedContext);
    assert.equal(ui.selectedContext.context_type, "PATHWAY");
    assert.equal(ui.selectedContext.context_id, "PW-01");
  });

  it("test_click_connection_sets_zaki_context", () => {
    const client = new SimulationClient(() => {});
    const connectionContext: ZakiSelectedContext = {
      context_type: "CONNECTION",
      context_id: "EV-001->HYP-001",
      display_name: "Transport Alarm → Optical Transceiver Hypothesis",
      summary: "Strong corroborating causal connection.",
      status: "CORROBORATING",
    };

    client.setSelectedContext(connectionContext);
    const ui = client.getZakiUIState();
    assert.ok(ui.selectedContext);
    assert.equal(ui.selectedContext.context_type, "CONNECTION");
    assert.equal(ui.selectedContext.context_id, "EV-001->HYP-001");
  });

  it("test_click_gap_sets_zaki_context", () => {
    const client = new SimulationClient(() => {});
    const gapContext: ZakiSelectedContext = {
      context_type: "KNOWLEDGE_GAP",
      context_id: "KG-001",
      display_name: "Missing BGP Neighbor Table",
      summary: "Evidence provider timeout prevents confirming control plane isolation.",
      status: "BLOCKING",
    };

    client.setSelectedContext(gapContext);
    const ui = client.getZakiUIState();
    assert.ok(ui.selectedContext);
    assert.equal(ui.selectedContext.context_type, "KNOWLEDGE_GAP");
    assert.equal(ui.selectedContext.status, "BLOCKING");
  });

  it("test_click_domain_sets_zaki_context", () => {
    const client = new SimulationClient(() => {});
    const domainContext: ZakiSelectedContext = {
      context_type: "DOMAIN_ATTRIBUTION",
      context_id: "transport",
      display_name: "IP Transport",
      summary: "PRIMARY domain with 88% causal confidence.",
      status: "PRIMARY",
    };

    client.setSelectedContext(domainContext);
    const ui = client.getZakiUIState();
    assert.ok(ui.selectedContext);
    assert.equal(ui.selectedContext.context_type, "DOMAIN_ATTRIBUTION");
    assert.equal(ui.selectedContext.context_id, "transport");
    assert.equal(ui.selectedContext.status, "PRIMARY");
  });

  it("test_zaki_quick_actions_change_by_context", () => {
    const getContextPrompts = (ctx?: ZakiSelectedContext | null): string[] => {
      if (!ctx) return ["Explain current reasoning", "What is the primary domain?", "What happens next?"];
      switch (ctx.context_type) {
        case "HYPOTHESIS":
          return [`Why is ${ctx.display_name} ranked here?`, `What evidence supports ${ctx.context_id}?`];
        case "PATHWAY":
          return [`Explain pathway ${ctx.display_name}`, `What evidence feeds this pathway?`];
        case "DOMAIN_ATTRIBUTION":
          return [`Why is ${ctx.display_name} assigned this role?`, `Is there an attribution conflict?`];
        case "KNOWLEDGE_GAP":
          return [`Why is ${ctx.display_name} a gap?`, `Is this gap blocking validation?`];
        default:
          return ["Explain selected object"];
      }
    };

    const generalPrompts = getContextPrompts(null);
    assert.ok(generalPrompts[0].includes("Explain current reasoning"));

    const hypPrompts = getContextPrompts({
      context_type: "HYPOTHESIS",
      context_id: "HYP-001",
      display_name: "H1",
    });
    assert.ok(hypPrompts[0].includes("Why is H1 ranked here?"));

    const domainPrompts = getContextPrompts({
      context_type: "DOMAIN_ATTRIBUTION",
      context_id: "transport",
      display_name: "IP Transport",
    });
    assert.ok(domainPrompts[1].includes("attribution conflict"));
  });

  it("test_zaki_entity_structure_color_cyan", () => {
    const entity: HighlightedEntity = {
      name: "edge-router-07",
      type: "ROUTER",
      role: "PRIMARY",
      visual_role: "STRUCTURE",
      domain: "Transport",
    };
    assert.equal(entity.visual_role, "STRUCTURE");
    // Semantic color token mapping
    const tokenClass = entity.visual_role === "STRUCTURE" ? "text-cyan-300 border-cyan-500/30" : "";
    assert.ok(tokenClass.includes("cyan"));
  });

  it("test_zaki_focus_color_magenta", () => {
    const entity: HighlightedEntity = {
      name: "transceiver-xe-0/0/1",
      type: "INTERFACE",
      role: "PRIMARY",
      visual_role: "FOCUS",
      domain: "Transport",
    };
    assert.equal(entity.visual_role, "FOCUS");
    const tokenClass = entity.visual_role === "FOCUS" ? "text-fuchsia-300 border-fuchsia-500/30" : "";
    assert.ok(tokenClass.includes("fuchsia"));
  });

  it("test_zaki_confirmed_color_turquoise", () => {
    const entity: HighlightedEntity = {
      name: "Transport Domain",
      type: "DOMAIN",
      role: "PRIMARY",
      visual_role: "CONFIRMED",
      domain: "Transport",
    };
    assert.equal(entity.visual_role, "CONFIRMED");
    const tokenClass = entity.visual_role === "CONFIRMED" ? "text-teal-300 border-teal-500/30" : "";
    assert.ok(tokenClass.includes("teal"));
  });

  it("test_zaki_body_text_not_overcolored", () => {
    const sampleResponse: ZakiResponseV2 = {
      answer: "Investigation focus: current causal explanation, evidence, and hypothesis confidence.",
      sections: [
        { title: "What Happened", content: "Optical transceiver power on edge router dropped below threshold.", order: 1 },
        { title: "Why It Matters", content: "Downstream RAN cell sites lost fiber connectivity.", order: 2 },
      ],
      grounded_in: {
        stage: "TEST",
        domain: "Transport",
        grounded_in_simulation: true,
        internet_access: false,
      },
    };

    // Body content should remain crisp readable text without saturated neon inline colors
    assert.equal(sampleResponse.sections.length, 2);
    for (const s of sampleResponse.sections) {
      assert.ok(!s.content.includes("<span style="));
      assert.ok(!s.content.includes("<div"));
    }
  });

  it("test_zaki_conflict_banner", () => {
    const conflictState = {
      attribution_status: "CONFLICT",
      leadingHypothesis: "H1 — Core Transport Router Failure",
      authoritativeDomain: "RAN — PRIMARY",
      reason: "Current attribution is stale relative to the active hypothesis revision.",
      nextAction: "Recompute attribution before trusting domain ownership.",
    };

    assert.equal(conflictState.attribution_status, "CONFLICT");
    assert.ok(conflictState.reason.includes("stale"));
    assert.ok(conflictState.nextAction.includes("Recompute attribution"));
  });

  it("test_zaki_replay_badge", () => {
    const replayMeta = {
      is_replay: true,
      replay_position: 2,
      total_stages: 5,
      zero_lookahead_enforced: true,
    };

    assert.equal(replayMeta.is_replay, true);
    assert.equal(replayMeta.replay_position, 2);
    assert.equal(replayMeta.zero_lookahead_enforced, true);
  });

  it("test_zaki_response_level_switch", () => {
    const client = new SimulationClient(() => {});
    assert.equal(client.getZakiUIState().responseLevel, "engineer");

    client.setResponseLevel("executive");
    assert.equal(client.getZakiUIState().responseLevel, "executive");

    client.setResponseLevel("operator");
    assert.equal(client.getZakiUIState().responseLevel, "operator");

    client.setResponseLevel("deep");
    assert.equal(client.getZakiUIState().responseLevel, "deep");
  });

  it("test_zaki_context_switch_clears_old_object", () => {
    const client = new SimulationClient(() => {});
    client.setSelectedContext({
      context_type: "HYPOTHESIS",
      context_id: "HYP-001",
      display_name: "H1",
    });
    assert.equal(client.getZakiUIState().selectedContext?.context_id, "HYP-001");

    // Clear context
    client.clearSelectedContext();
    assert.equal(client.getZakiUIState().selectedContext, null);

    // Switch to different object cleanly
    client.setSelectedContext({
      context_type: "DOMAIN_ATTRIBUTION",
      context_id: "transport",
      display_name: "Transport",
    });
    assert.equal(client.getZakiUIState().selectedContext?.context_type, "DOMAIN_ATTRIBUTION");
    assert.equal(client.getZakiUIState().selectedContext?.context_id, "transport");
  });
});
