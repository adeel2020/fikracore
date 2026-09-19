# FikraCore — Step 4.6 Live MCP Parity & Benchmark Validation

## Purpose

Step 4.6 validates that the already-supported H1–H4 reasoning capabilities behave correctly when operational knowledge is sourced from the real live gbrain MCP-backed `telecombrain`, rather than only from frozen snapshot or in-memory providers.

Step 4.5 proves that the live MCP integration path works.

Step 4.6 asks the next question:

> Does the FikraCore reasoning stack preserve its expected behavior, accuracy, epistemic safety, and explainability when the KnowledgeProvider is switched to the real live gbrain MCP?

This is a **parity and benchmark validation step**.

It is not a redesign of H1–H4.

It is not a topology migration step.

It is not a live mutation step.

---

# 1. Validation Question

Validate:

> Can FikraCore run H1–H4 reasoning through the live gbrain MCP-backed `telecombrain` with results that are equivalent to, or explainably different from, the already-validated snapshot/in-memory knowledge path?

The key comparison is:

```text
Snapshot / Frozen KnowledgeProvider
        vs
Live gbrain MCP KnowledgeProvider
```

---

# 2. Relationship to Previous Steps

The validation sequence is:

```text
H1 — Reason
H2 — Recognize the Unknown
H3 — Learn
H4 — Predict
        ↓
Step 4.5 — Live MCP Smoke Test
        ↓
Step 4.6 — Live MCP Parity & Benchmark Validation
        ↓
Step 5 — Unified Capability & Experience Layer
```

Step 4.6 should begin only after Step 4.5 is sufficiently supported.

---

# 3. What Step 4.6 Proves

Step 4.6 should prove:

```text
live entity resolution works at scale
live graph traversal is compatible
canonicalization behaves consistently
reasoning outcomes remain stable
knowledge gaps are detected correctly
learned knowledge is reusable through MCP
what-if propagation remains explainable
blast radius remains accurate
Mark / Zaki consumes the same live state
Hidden Truth remains segregated
```

---

# 4. What Step 4.6 Does NOT Prove

This step does not prove:

```text
production readiness
high availability
large-scale concurrency
real-time Kafka ingestion
Grafana LGTM integration
full ITSM integration
automatic live knowledge mutation
autonomous remediation
```

Those belong to later product/integration phases.

---

# 5. Core Architecture

```text
                   FikraCore Reasoning Stack
                            │
                     KnowledgeProvider
                      ┌─────┴─────┐
                      │           │
               Snapshot Path   Live MCP Path
                      │           │
                Frozen Graph   gbrain MCP
                                  │
                              telecombrain
```

Both paths must expose equivalent logical provider contracts to the reasoning engine.

---

# 6. Provider Abstraction Requirement

The reasoning engine must not contain provider-specific branching such as:

```text
if live_mcp:
    use different RCA logic
```

The provider abstraction should normalize:

```text
entity lookup
canonical identity
relationship lookup
backlinks
graph traversal
provenance
knowledge state
```

The reasoning engine should operate on the same internal contracts regardless of source.

---

# 7. Validation Modes

Step 4.6 should run in three stages:

```text
Stage A — Selected Parity Scenarios
Stage B — Cohort Parity Benchmark
Stage C — Full MCP-Backed Benchmark
```

Do not jump directly to the full benchmark unless selected parity runs are stable.

---

# 8. Stage A — Selected Parity Scenarios

Choose a small representative set across H1–H4.

Recommended minimum:

```text
H1: 5 scenarios
H2: 5 scenarios
H3: 5 learning units
H4: 5 what-if scenarios
```

Total:

```text
20 selected parity runs
```

Select scenarios that cover:

```text
single-domain
cross-domain
shared dependency
knowledge gap
stale knowledge
validated learning reuse
failover
capacity
change risk
model insufficiency
```

---

# 9. Same Input, Different Provider

For each selected run execute:

```text
Run A:
KnowledgeProvider = frozen snapshot/in-memory provider

Run B:
KnowledgeProvider = live gbrain MCP provider
```

Keep constant:

```text
scenario
evidence
reasoning policy
thresholds
canonical resolver
evaluator
random seed
presentation mode
```

Only the provider should change.

---

# 10. Parity Comparison Dimensions

Compare:

```text
resolved entities
canonical IDs
display names
direct relationships
relationship direction
graph paths
hypothesis candidates
root-cause ranking
terminal state
knowledge-gap decision
next-best evidence
learning reuse
what-if propagation
blast radius
critical failure surface
confidence
provenance
```

---

# 11. Parity Result Classes

Each comparison should be classified as:

```text
EXACT_PARITY
SEMANTIC_PARITY
EXPLAINED_DELTA
UNEXPLAINED_DELTA
INTEGRATION_FAILURE
```

Definitions:

### EXACT_PARITY

```text
same logical output
same canonical entities
same decision
```

### SEMANTIC_PARITY

```text
same operational conclusion
minor ordering / metadata / provenance differences
```

### EXPLAINED_DELTA

```text
live telecombrain contains newer or additional knowledge
difference is traceable and operationally justified
```

### UNEXPLAINED_DELTA

```text
behavior differs with no valid knowledge explanation
```

### INTEGRATION_FAILURE

```text
provider, MCP, traversal, canonicalization, or response handling failed
```

---

# 12. Exact Parity Is Not Always Required

Do not require byte-for-byte identical results.

Live `telecombrain` may legitimately differ from a frozen snapshot.

The important question is:

> Is the delta explainable by real knowledge differences?

Example:

```text
Snapshot:
Transport Router-01 has one known downstream path.

Live MCP:
Transport Router-01 has an additional validated path.

Result:
H4 blast radius changes.

Classification:
EXPLAINED_DELTA
```

---

# 13. Unexplained Delta Investigation

For every `UNEXPLAINED_DELTA`, capture:

```text
provider inputs
MCP calls
entity resolution
canonical mapping
relationship set
traversal result
reasoning candidates
score contributions
terminal-state logic
```

Do not patch the scenario immediately.

First identify whether the cause is:

```text
MCP transport
provider normalization
canonical mismatch
relationship direction
missing relation
duplicate relation
stale relation
reasoning bug
evaluator mismatch
```

---

# 14. Live MCP Read-Only Rule

Step 4.6 should remain read-only by default.

Do not automatically call:

```text
add_link
schema_apply_mutations
delete
overwrite
promotion apply
```

For H3 parity, use:

```text
approved test snapshot
sandbox namespace
or temporary provider overlay
```

if promoted knowledge must be simulated.

Do not mutate the live operational brain solely for benchmark purposes.

---

# 15. H1 Live Parity Validation

For H1 compare:

```text
candidate hypotheses
actual root rank
terminal state
explanation
provenance
reasoning steps
```

Key question:

> Does live MCP knowledge preserve the H1 causal reasoning outcome?

---

# 16. H1 Metrics

Report:

```text
Rank #1 parity
Root-cause decision parity
Terminal-state parity
Explanation-path parity
Provider-induced divergence count
```

---

# 17. H2 Live Parity Validation

For H2 compare:

```text
MODEL_INSUFFICIENT decision
gap boundary
gap type
next-best evidence
candidate relationship
hallucinated topology
```

Key question:

> Does the live graph help or harm unknown-unknown detection?

---

# 18. H2 Metrics

Report:

```text
Model-insufficiency parity
Gap-boundary parity
Gap-type parity
Next-best-evidence parity
Hallucinated topology count
False model-gap count
```

---

# 19. H3 Live Parity Validation

H3 requires special care because live mutation should not be used casually.

Use:

```text
frozen before-state
validated promotion overlay
future incident
```

or a temporary benchmark-safe knowledge overlay.

Compare:

```text
knowledge reuse
future root cause
reasoning steps
knowledge provenance
stale detection
poisoning resistance
```

---

# 20. H3 Metrics

Report:

```text
Validated knowledge reuse parity
Positive transfer parity
Cross-domain transfer parity
Stale-knowledge parity
Poisoning-resistance parity
Promotion provenance parity
```

---

# 21. H4 Live Parity Validation

For H4 compare:

```text
forward propagation
blast radius
affected services
critical failure surface
shared dependency
failover risk
capacity risk
change risk
mitigation
confidence
```

---

# 22. H4 Metrics

Report:

```text
Blast-radius precision parity
Blast-radius recall parity
Affected-service parity
Critical-failure-surface parity
Shared-dependency parity
Failover-risk parity
Capacity-risk parity
Change-risk parity
Hallucinated path count
Mitigation usefulness parity
```

---

# 23. Provider-Level Metrics

Measure live MCP provider behavior directly:

```text
MCP request count
MCP failures
retry count
average request latency
P95 request latency
entity cache hit rate
canonical-resolution failures
missing-page rate
traversal failures
provider normalization errors
```

These are integration metrics, not reasoning metrics.

---

# 24. Reasoning Metrics vs Integration Metrics

Keep them separate.

### Reasoning metrics

```text
RCA correctness
knowledge-gap correctness
learning reuse
blast radius
critical failure surface
confidence
```

### Integration metrics

```text
MCP connectivity
latency
tool success
canonicalization
provider errors
response normalization
```

Do not let transport failures distort reasoning conclusions.

---

# 25. Canonical Resolution Validation

For every benchmark run capture:

```text
requested entity
source-native slug
resolved canonical slug
MCP-returned slug
internal provider identity
evaluator identity
```

Any mismatch should be explicitly classified.

---

# 26. Relationship Direction Validation

Because relationship direction has already proven important in earlier work, compare:

```text
snapshot edge direction
live MCP edge direction
normalized provider direction
reasoning traversal direction
```

Track mismatches for relations such as:

```text
MEMBER_OF
MONITORED_BY
SUPPORTS_SERVICE
SERVES
DEPENDS_ON
ROUTES_THROUGH
FAILS_OVER_TO
```

---

# 27. Live Knowledge Freshness

Capture:

```text
knowledge version
schema version
page updated time
relationship updated time
validation state
```

where available.

An explained delta should identify whether freshness caused the behavior difference.

---

# 28. Snapshot Versioning

Freeze the comparison snapshot used by Step 4.6.

Store:

```text
snapshot ID
snapshot hash
creation time
schema version
scenario benchmark version
```

This makes parity analysis reproducible.

---

# 29. MCP Session Stability

During cohort and full benchmark runs validate:

```text
session reuse
session expiry handling
token refresh behavior
retry behavior
request ordering
```

Do not silently convert session failures into empty knowledge responses.

---

# 30. Empty Result Safety

A failed MCP request must not be normalized into:

```text
no relationships exist
```

Distinguish:

```text
EMPTY_VALID_RESULT
MCP_REQUEST_FAILED
PAGE_NOT_FOUND
PERMISSION_DENIED
```

This is critical for H2 and H4.

---

# 31. Timeout Safety

If MCP times out:

```text
do not continue reasoning as though knowledge is complete
```

Return an explicit integration limitation.

Example:

```text
KNOWLEDGE_PROVIDER_UNAVAILABLE
```

or equivalent.

---

# 32. Live Provider Provenance

Every live knowledge item passed into reasoning should retain:

```text
provider = gbrain-mcp
MCP tool
source slug
canonical slug
relationship type
retrieval time
```

This should be available for technical inspection.

---

# 33. Mark / Zaki Parity

For selected runs compare:

```text
snapshot-backed explanation
live-MCP-backed explanation
```

Mark / Zaki should reflect the current provider-backed structured state.

Do not let Mark / Zaki independently query a different state and contradict the Simulator.

---

# 34. Simulator UI Parity

The Simulator UI should show which provider is active:

```text
Knowledge Source:
Live telecombrain via gbrain MCP
```

or:

```text
Knowledge Source:
Frozen Benchmark Snapshot
```

This is useful during demonstrations and debugging.

---

# 35. Provider Toggle

For engineering and parity validation, support a controlled provider toggle.

Example:

```text
Snapshot
Live MCP
```

This should be available in technical mode, not necessarily leadership demo mode.

---

# 36. Suggested CLI Commands

Use the existing `fikracore` root command.

Recommended:

```bash
fikracore inspect live-knowledge
fikracore benchmark parity --stage h1
fikracore benchmark parity --stage h2
fikracore benchmark parity --stage h3
fikracore benchmark parity --stage h4
fikracore benchmark parity --all
```

For one scenario:

```bash
fikracore inspect parity "MPLS Edge Router Failure"
```

The exact subcommand structure may adapt to the existing parser.

---

# 37. Selected-Parity Artifact

Generate:

```text
artifacts/integration/mcp-parity/selected-runs.jsonl
```

Each record should include:

```json
{
  "scenario": "H4-WI-001",
  "display_name": "MPLS Edge Router Failure",
  "snapshot_result": {},
  "live_mcp_result": {},
  "classification": "SEMANTIC_PARITY",
  "delta_reason": null
}
```

---

# 38. Full Parity Summary

Generate:

```text
artifacts/integration/mcp-parity/aggregate-report.json
artifacts/integration/mcp-parity/aggregate-report.md
```

Report:

```text
Exact parity count
Semantic parity count
Explained delta count
Unexplained delta count
Integration failure count
```

---

# 39. H1–H4 Parity Reports

Generate:

```text
artifacts/integration/mcp-parity/h1-parity.json
artifacts/integration/mcp-parity/h2-parity.json
artifacts/integration/mcp-parity/h3-parity.json
artifacts/integration/mcp-parity/h4-parity.json
```

---

# 40. Provider Diagnostics

Generate:

```text
artifacts/integration/mcp-parity/provider-diagnostics.json
```

Include:

```text
request count
success rate
latency
tool usage
errors
timeouts
canonical failures
traversal failures
```

---

# 41. Unexplained Delta Report

Generate:

```text
artifacts/integration/mcp-parity/unexplained-deltas.md
```

For every unexplained delta include:

```text
scenario
stage
expected behavior
snapshot result
live result
entity/relationship differences
reasoning difference
suspected cause
recommended investigation
```

---

# 42. Full MCP-Backed Benchmark

Only after selected parity and cohort parity are stable, run the full benchmark suites through the live MCP provider.

Recommended full coverage:

```text
H1 full benchmark
H2 60 scenarios
H3 30 learning units
H4 40 scenarios
```

Use the currently frozen benchmark definitions.

---

# 43. Full Benchmark Rules

Do not:

```text
regenerate scenarios
modify Hidden Truth
change thresholds specifically for MCP
change evaluator expectations
tune live provider per scenario
```

The provider is the variable under test.

---

# 44. Full Benchmark Comparison

For each H-stage compare:

```text
previous validated benchmark result
vs
live MCP-backed result
```

Report both.

Do not overwrite the original H1–H4 benchmark artifacts.

---

# 45. Reasoning Regression Gate

Define acceptable regression explicitly.

Suggested initial rule:

```text
No unexplained critical regression
No Hidden Truth leakage
No hallucinated topology increase
No provider-induced false MODEL_INSUFFICIENT spike
No material loss in H1/H4 core accuracy without explained knowledge delta
```

Avoid using one arbitrary percentage until the first live benchmark reveals realistic variation.

---

# 46. Live Knowledge Advantage

Also measure improvements caused by newer live knowledge.

Examples:

```text
better root-cause ranking
fewer model-insufficient outcomes
better blast-radius recall
more complete service impact
better topology explanation
```

Parity is not only about preventing regression.

Live knowledge may improve reasoning.

---

# 47. Drift Classification

Classify live-vs-snapshot knowledge drift as:

```text
NEW_KNOWLEDGE
UPDATED_KNOWLEDGE
REMOVED_KNOWLEDGE
STALE_SNAPSHOT
CANONICALIZATION_CHANGE
SCHEMA_CHANGE
UNEXPECTED_DRIFT
```

---

# 48. Schema Compatibility

Compare:

```text
snapshot schema assumptions
live active schema
provider normalization rules
```

If the live schema evolves, verify the provider still presents a compatible internal model.

---

# 49. Read-Only Benchmark Safety

The full Step 4.6 benchmark should remain read-only against live gbrain.

For H3 learning validation, use:

```text
overlay
sandbox
or versioned benchmark provider
```

rather than mutating live `telecombrain`.

---

# 50. Test Requirements

Add tests for at least:

```text
test_live_provider_contract_matches_snapshot_provider
test_parity_exact_match_classification
test_parity_semantic_match_classification
test_explained_delta_classification
test_unexplained_delta_classification
test_mcp_failure_not_treated_as_empty_graph
test_timeout_marks_provider_unavailable
test_live_canonical_resolution
test_live_relationship_direction_normalization
test_live_provider_provenance
test_mark_zaki_uses_active_provider_state
test_hidden_truth_not_sent_to_mcp
test_h1_live_parity
test_h2_live_parity
test_h3_live_parity
test_h4_live_parity
```

---

# 51. Definition of Done

Step 4.6 is complete when:

```text
[ ] Step 4.5 smoke test is supported
[ ] frozen comparison snapshot exists
[ ] selected H1 parity runs complete
[ ] selected H2 parity runs complete
[ ] selected H3 parity runs complete
[ ] selected H4 parity runs complete
[ ] every delta is classified
[ ] unexplained deltas are investigated
[ ] canonical-resolution parity is measured
[ ] relationship-direction parity is measured
[ ] provider metrics are captured
[ ] Mark / Zaki parity is verified
[ ] Simulator provider source is visible in technical mode
[ ] Hidden Truth leakage remains zero
[ ] full MCP-backed H1 benchmark completes
[ ] full MCP-backed H2 benchmark completes
[ ] full MCP-backed H3 benchmark completes
[ ] full MCP-backed H4 benchmark completes
[ ] original benchmark artifacts remain unchanged
[ ] final parity report is generated
```

---

# 52. Step 4.6 Decision

Classify:

```text
LIVE_MCP_PARITY_SUPPORTED
LIVE_MCP_PARITY_PARTIALLY_SUPPORTED
LIVE_MCP_PARITY_NOT_SUPPORTED
```

---

# 53. Suggested Decision Logic

### LIVE_MCP_PARITY_SUPPORTED

Use when:

```text
integration remains stable
reasoning outcomes are equivalent or explainably different
no unexplained critical regressions remain
no Hidden Truth leakage occurs
no hallucination safety regression occurs
```

### LIVE_MCP_PARITY_PARTIALLY_SUPPORTED

Use when:

```text
core reasoning works
but some provider/schema/canonicalization deltas remain unresolved
```

### LIVE_MCP_PARITY_NOT_SUPPORTED

Use when:

```text
live provider causes material unexplained reasoning failures
or epistemic/safety guarantees are broken
```

---

# 54. Final Report Questions

The final Step 4.6 report must answer:

```text
1. Does the live MCP provider satisfy the same KnowledgeProvider contract?
2. How many runs achieved exact parity?
3. How many achieved semantic parity?
4. How many differences were explained by newer live knowledge?
5. How many unexplained deltas remain?
6. Did canonicalization cause any differences?
7. Did relationship direction cause any differences?
8. Did MCP failures ever appear as empty knowledge?
9. Did H1 accuracy materially change?
10. Did H2 unknown-unknown behavior materially change?
11. Did H3 learning reuse materially change?
12. Did H4 blast-radius/resilience behavior materially change?
13. Did Mark / Zaki remain grounded in the active provider state?
14. Was Hidden Truth leakage zero?
15. Is live MCP reasoning safe enough to proceed into Step 5?
```

---

# 55. Transition to Step 5

If Step 4.6 is sufficiently supported:

```text
Validated H1–H4 Reasoning
        +
Validated Live MCP Knowledge Path
        ↓
Step 5 — Unified FikraCore Capability & Experience Layer
```

Step 5 can then confidently expose:

```text
CLI
Simulator UI
Curated Demo Mode
Mark / Zaki
API / Automation
```

against the real operational `telecombrain` integration path.

---

# Final Principle

> **The reasoning engine should not care whether knowledge came from a snapshot or live gbrain MCP — only whether the knowledge is valid, canonical, traceable, and complete enough for the decision.**

Step 4.6 proves that the validated FikraCore reasoning stack survives the transition from controlled benchmark knowledge to the real live `telecombrain` access path.
