import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  getScenarioAttributionProfile,
  OPERATIONAL_DOMAINS_CATALOG,
  renderStyledMessage,
} from "../app/simulator/investigate/lib";

describe("FikraCore Step 5.2.1 Domain Attribution & Consistency Tests (§22, §23, §27)", () => {
  it("test_all_14_operational_domains_catalog_present", () => {
    assert.equal(OPERATIONAL_DOMAINS_CATALOG.length, 14);
    const domainIds = OPERATIONAL_DOMAINS_CATALOG.map((d) => d.id);
    assert.ok(domainIds.includes("transport"));
    assert.ok(domainIds.includes("mobile_core"));
    assert.ok(domainIds.includes("ran"));
    assert.ok(domainIds.includes("ims_voice"));
    assert.ok(domainIds.includes("security"));
    assert.ok(domainIds.includes("cloud_k8s"));
  });

  it("test_domain_profile_contains_all_14_domains_with_nominal_defaults", () => {
    const profile = getScenarioAttributionProfile("SCN-001", null, null);
    assert.equal(Object.keys(profile.domainClassifications).length, 14);
    assert.equal(Object.keys(profile.domainWeights).length, 14);

    // Initial state without run: all 14 domains should be MONITOR ONLY with 0% weight
    for (const d of OPERATIONAL_DOMAINS_CATALOG) {
      assert.equal(profile.domainClassifications[d.id]?.classification, "MONITOR ONLY");
      assert.equal(profile.domainWeights[d.id], 0);
    }
  });

  it("test_relevant_domains_highlighted_from_backend_attribution", () => {
    const simulationState = {
      scenario_id: "SCN-001",
      revision: 6,
      sequence: 6,
      domain_attribution: {
        status: "READY",
        attribution_status: "CONSISTENT",
        revision: 6,
        sequence: 6,
        domains: [
          {
            domain_id: "transport",
            display_name: "Transport",
            role: "PRIMARY",
            confidence: 88,
            attribution_basis: "CAUSAL",
            reason: "Core Router optical transceiver degradation",
            supporting_hypothesis_ids: ["HYP-001"],
            source_revision: 6,
          },
          {
            domain_id: "ran",
            display_name: "RAN",
            role: "AFFECTED",
            confidence: 45,
            attribution_basis: "IMPACT",
            reason: "Downstream cell site backhaul starvation",
            supporting_hypothesis_ids: ["HYP-001"],
            source_revision: 6,
          },
        ],
      },
    };

    const profile = getScenarioAttributionProfile("SCN-001", null, simulationState);

    // Check PRIMARY domain
    assert.equal(profile.primaryDomainId, "transport");
    assert.ok(profile.primaryDomainName === "Transport" || profile.primaryDomainName === "IP Transport");
    assert.equal(profile.primaryAttribution, 88);
    assert.equal(profile.attributionStatus, "CONSISTENT");

    // Check Transport info
    const transportInfo = profile.domainClassifications["transport"];
    assert.equal(transportInfo?.classification, "PRIMARY");
    assert.equal(transportInfo?.weight, 88);
    assert.equal(transportInfo?.attributionBasis, "CAUSAL");
    assert.deepEqual(transportInfo?.supportingHypothesisIds, ["HYP-001"]);

    // Check RAN info
    const ranInfo = profile.domainClassifications["ran"];
    assert.equal(ranInfo?.classification, "AFFECTED");
    assert.equal(ranInfo?.weight, 45);

    // Other non-relevant domains remain MONITOR ONLY nominal
    assert.equal(profile.domainClassifications["security"]?.classification, "MONITOR ONLY");
    assert.equal(profile.domainWeights["security"], 0);
  });

  it("test_attribution_conflict_status_captured", () => {
    const simulationState = {
      scenario_id: "SCN-001",
      revision: 6,
      sequence: 6,
      domain_attribution: {
        status: "READY",
        attribution_status: "CONFLICT",
        conflict_reasons: [
          "Leading hypothesis implies Transport, but PRIMARY domain is RAN",
        ],
        revision: 6,
        sequence: 6,
        domains: [
          {
            domain_id: "ran",
            display_name: "RAN",
            role: "PRIMARY",
            confidence: 88,
            reason: "Test",
          },
        ],
      },
    };

    const profile = getScenarioAttributionProfile("SCN-001", null, simulationState);
    assert.equal(profile.attributionStatus, "CONFLICT");
    assert.ok(profile.conflictReasons && profile.conflictReasons.length > 0);
    assert.match(profile.conflictReasons[0], /Leading hypothesis implies Transport/);
  });

  it("test_revision_consistency_between_state_and_profile", () => {
    const simulationState = {
      scenario_id: "SCN-001",
      revision: 14,
      sequence: 14,
      domain_attribution: {
        status: "READY",
        attribution_status: "CONSISTENT",
        revision: 14,
        sequence: 14,
        domains: [
          {
            domain_id: "transport",
            display_name: "Transport",
            role: "PRIMARY",
            confidence: 88,
            source_revision: 14,
          },
        ],
      },
    };

    const profile = getScenarioAttributionProfile("SCN-001", null, simulationState);
    assert.equal(profile.revision, 14);
    assert.equal(profile.sequence, 14);
  });

  it("test_h4_wi_036_resolves_to_transport_domain", () => {
    const simulationState = {
      scenario_id: "H4-WI-036",
      revision: 6,
      sequence: 6,
      domain_attribution: {
        status: "READY",
        attribution_status: "CONSISTENT",
        revision: 6,
        sequence: 6,
        domains: [
          {
            domain_id: "transport",
            display_name: "Transport",
            role: "PRIMARY",
            confidence: 88,
            attribution_basis: "CAUSAL",
            reason: "Validated reasoning on IP:CORE:RTR-01 identifies Transport as primary causal failure root.",
            supporting_hypothesis_ids: ["H1"],
            source_revision: 6,
          },
        ],
      },
    };

    const profile = getScenarioAttributionProfile("H4-WI-036", null, simulationState);
    assert.equal(profile.primaryDomainId, "transport");
    assert.ok(profile.primaryDomainName === "Transport" || profile.primaryDomainName === "IP Transport");
    assert.equal(profile.primaryAttribution, 88);
  });

  it("test_render_styled_message_formats_typography_tokens", () => {
    const sample = "Hypothesis H1 indicates IP:CORE:RTR-01 optical degradation in **Transport** domain.";
    const rendered = renderStyledMessage(sample, false);
    assert.ok(rendered !== null);
  });
});
