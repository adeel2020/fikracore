import test from "node:test";
import assert from "node:assert/strict";
import { extractRealtimeIncidentContext } from "../components/features/agentic-qna-view/components/StorytellerVisualExplanation";

test("FikraCore Epistemic Integrity & Anti-Leakage Gate Tests", async (t) => {
  await t.test("Stage 0 (Nominal Baseline): No oracle leakage from static scenario manifest", () => {
    const rawSimulationState = {
      stage_index: 0,
      current_stage: "nominal baseline",
      scenario_id: "SCN-TRANSPORT-FAILOVER",
      scenario: {
        domains: ["TRANSPORT"],
        services: ["5G_SA_MOBILE_DATA"],
      },
      evidence_items: [],
      hypotheses: [],
    };

    const ctx = extractRealtimeIncidentContext(null, rawSimulationState, "SCN-TRANSPORT-FAILOVER", 0);

    // ZERO Oracle Leakage: manifest domains and services must never be admitted before correlation
    assert.equal(ctx.crossDomain, null, "Cross-domain discovery must be null at Stage 0");
    assert.equal(ctx.domainsCount, null, "Domains count must be null at Stage 0");
    assert.equal(ctx.servicesImpacted, null, "Services impacted must be null at Stage 0");

    // ZERO False Alarm Gates: Pre-correlation stages must be unscored (--), not 0% or fake 100%
    assert.equal(ctx.convergenceScore, null, "Convergence score must be null (not 0% false alarm) before correlation");
    assert.equal(ctx.traceabilityScore, null, "Traceability score must be null before correlation");
    assert.equal(ctx.stabilityScore, null, "Stability score must be null before correlation");
    assert.equal(ctx.coverageScore, null, "Coverage score must be null before correlation");

    // ZERO Static/Mock fallbacks
    assert.equal(ctx.knowledgeGapStatus, null, "Knowledge gap must be null before correlation assessment");
    assert.equal(ctx.ontologyGroundingScore, null, "Ontology grounding must be null before correlation");
    assert.equal(ctx.blastContainmentScore, null, "Blast containment must be null before localization");
    assert.equal(ctx.hitlAutonomyTier, null, "Autonomy gate must be null when no remediations are staged");
  });

  await t.test("Stage 1 (Signal Flood): Raw telemetry arriving does NOT trigger premature 0% convergence alarms", () => {
    const rawSimulationState = {
      stage_index: 1,
      current_stage: "signal flood",
      scenario_id: "SCN-TRANSPORT-FAILOVER",
      scenario: {
        domains: ["TRANSPORT"],
        services: ["5G_SA_MOBILE_DATA"],
      },
      evidence_items: [
        { statement: "OPTICAL_POWER_DEGRADATION", grade: "A", object_ref: "PE-RTR-01" },
        { statement: "BGP_NEIGHBOR_DOWN", grade: "B", object_ref: "PE-RTR-02" },
      ],
      hypotheses: [],
    };

    const ctx = extractRealtimeIncidentContext(null, rawSimulationState, "SCN-TRANSPORT-FAILOVER", 1);

    // Claims admitted
    assert.equal(ctx.claims.length, 2, "Raw telemetry admitted into claims");

    // Evidence convergence MUST be unscored (--), NOT 0% false alarm with critical red arrow
    assert.equal(ctx.convergenceScore, null, "Evidence convergence must NOT evaluate to 0% during signal flood");
    assert.equal(ctx.crossDomain, null, "Cross-domain discovery must remain null until correlation Stage 2");
    assert.equal(ctx.blastContainmentScore, null, "Blast containment must remain null until localization");
  });

  await t.test("Stage 2+ (Correlation): Dynamic findings bound without manifest leakage", () => {
    const correlatedState = {
      stage_index: 2,
      current_stage: "ai correlation",
      scenario_id: "SCN-TRANSPORT-FAILOVER",
      scenario: {
        domains: ["TRANSPORT"], // Leaked single domain in manifest
      },
      reasoningMap: {
        domain_attribution: {
          attributed_domains: ["TRANSPORT", "CORE"], // Correlated across 2 domains
        },
        hypotheses: [
          { title: "Transport Fiber Degraded", confidence: 0.92, status: "validated" },
        ],
        evidence: [
          { statement: "OPTICAL_POWER_DEGRADATION", confidence: 0.88, object_ref: "PE-RTR-01" },
          { statement: "BGP_NEIGHBOR_DOWN", confidence: 0.82, object_ref: "PE-RTR-02" },
        ],
      },
    };

    const ctx = extractRealtimeIncidentContext(null, correlatedState, "SCN-TRANSPORT-FAILOVER", 2);

    // Cross-domain discovery requires >= 2 domains
    assert.equal(ctx.crossDomain, "TRANSPORT ↔ CORE", "Cross-domain discovery requires >= 2 operational domains");
    assert.equal(ctx.domainsCount, 2, "Domains count reflects dynamic attributed domains");

    // Evidence convergence computes actual high-confidence claim ratio
    assert.equal(ctx.convergenceScore, 100, "100% convergence when all claims exceed 0.75 confidence");
    assert.equal(ctx.stabilityScore, 92, "Stability score reflects leading validated hypothesis");
    assert.equal(ctx.knowledgeGapStatus, "0 Gaps (Nominal)", "Zero gaps nominal when assessed in Stage 2+");
  });
});
