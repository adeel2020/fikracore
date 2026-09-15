# FikraCore Simulator — Step 4.3 / H3 Validated Knowledge Learning & Future-Incident Improvement

## Purpose

Step 4.3 validates **H3 — Validated Knowledge Learning & Future-Incident Improvement**.

H1 established that FikraCore can reason causally from current operational knowledge.

H2 established that FikraCore can recognize when its current operational knowledge is incomplete, localize the gap, request useful next evidence, and produce safe candidate knowledge without hallucinating topology.

H3 asks the next question:

> Does SME-validated knowledge discovered during one investigation improve FikraCore's reasoning on a different future incident?

This step validates the transition from:

```text
detecting a knowledge gap
```

to:

```text
learning safely from validated operational experience
```

The goal is not merely to store new relationships.

The goal is to prove that **validated learning produces measurable improvement on future incidents**.

---

# 1. H3 Validation Question

Validate:

> Can FikraCore take candidate knowledge discovered during H2, pass it through human / SME validation, promote only approved knowledge into `telecombrain`, and then demonstrate measurable improvement on a different future incident?

H3 is successful only if:

```text
candidate knowledge
→ human validation
→ controlled promotion
→ different future incident
→ better reasoning
```

---

# 2. Core H3 Principle

The core principle is:

```text
Learning is not:
"the simulator told us the answer"

Learning is:
"operations produced evidence,
FikraCore proposed a candidate,
an SME validated it,
and that validated knowledge improved future reasoning."
```

Hidden Truth remains evaluator-only.

---

# 3. Preserve H1 and H2

Freeze the completed H1 and H2 behavior.

Do not modify:

```text
H1 benchmark scenarios
H1 calibrated reasoning policy
H2 gap-detection semantics
H2 candidate-knowledge semantics
H2 anti-hallucination safeguards
H2 human-readable naming policy
H2 UI / Demo / Mark-Zaki integration contracts
```

All existing H1 and H2 tests must continue to pass.

H3 must be additive.

---

# 4. Epistemic Boundary

Preserve:

```text
Hidden Truth → Evaluator only
```

Forbidden:

```text
Hidden Truth → Learner
Hidden Truth → SME simulation
Hidden Truth → telecombrain promotion path
Hidden Truth → Mark / Zaki
Hidden Truth → Simulator UI
```

The system under test may only consume:

```text
Operational evidence
+
Current telecombrain knowledge
+
H2 candidate knowledge
+
SME validation decision
+
Investigation state
```

---

# 5. H3 Learning Lifecycle

The required H3 lifecycle is:

```text
Incident A
   ↓
H2 detects knowledge gap
   ↓
Candidate knowledge created
   ↓
SME / HITL reviews candidate
   ↓
ACCEPT / REJECT / MODIFY / NEED_MORE_EVIDENCE
   ↓
Approved knowledge promoted safely
   ↓
Different Incident B occurs later
   ↓
FikraCore reasons again
   ↓
Measure whether Incident B is solved better
```

---

# 6. Incident Pair Design

H3 requires **paired incidents**.

Each H3 learning unit should contain:

```text
Incident A — discovery incident
Incident B — future incident
```

Incident B must be different from Incident A.

Do not simply replay the same incident after adding the missing relation.

Good example:

```text
Incident A:
Mobile data degradation reveals a missing transport dependency.

SME validates:
Transport Router-01 routes through MPLS Edge Router-07.

Incident B:
A later enterprise VPN outage traverses the same MPLS Edge Router-07.

Question:
Does the validated relationship help FikraCore identify the shared cause faster and more accurately?
```

---

# 7. No Replay-as-Learning

Forbidden:

```text
Incident A
→ learn answer
→ replay Incident A
→ declare improvement
```

That does not prove generalization.

Incident B must differ in at least some of:

```text
service
symptoms
evidence order
affected domain
blast radius
trigger
observability noise
change context
customer impact
```

while still depending on the validated knowledge.

---

# 8. Learning Unit Structure

Recommended H3 learning unit:

```json
{
  "learning_unit_id": "H3-LU-001",
  "discovery_incident": "H2-SCN-017",
  "candidate_knowledge_ids": ["KG-001"],
  "validation_decision": "ACCEPT",
  "promoted_knowledge": [],
  "future_incident": "H3-FUT-001",
  "expected_learning_value": "Improved causal path reconstruction"
}
```

---

# 9. Candidate Knowledge Input

H3 should consume the candidate knowledge store produced by H2.

Example source:

```text
artifacts/knowledge-gaps/candidates/
```

Do not bypass H2 by directly constructing confirmed relationships from Hidden Truth.

Candidate objects should retain:

```text
candidate ID
gap type
proposed relation
supporting evidence
contradicting evidence
confidence
provenance
validation requirement
```

---

# 10. SME / HITL Validation Contract

Every candidate must pass through a structured validation decision.

Allowed decisions:

```text
ACCEPT
REJECT
MODIFY
NEED_MORE_EVIDENCE
```

Recommended object:

```json
{
  "validation_id": "VAL-001",
  "candidate_id": "KG-001",
  "decision": "ACCEPT",
  "validated_by_role": "Transport Domain SME",
  "reason": "Validated against transport inventory and MPLS path evidence.",
  "timestamp": "...",
  "evidence_refs": [],
  "modified_relation": null
}
```

---

# 11. Human Validation Is Not Ground Truth

Important:

> SME validation is trusted operational governance, not magical truth.

The evaluator may later compare SME-approved knowledge with Hidden Truth.

But runtime FikraCore must treat the SME decision as a governed operational decision.

H3 must be able to represent:

```text
correct SME approval
incorrect SME approval
partial approval
rejection
request for more evidence
```

---

# 12. Poisoning Resistance

H3 must test whether bad or incorrect validated knowledge can harm future reasoning.

Include scenarios such as:

```text
SME incorrectly accepts candidate
SME modifies relation incorrectly
stale relation remains active
conflicting SME decisions
duplicate relationship
overly broad dependency
```

The system should preserve provenance and make later correction possible.

---

# 13. Knowledge Promotion States

Use explicit lifecycle states:

```text
CANDIDATE
UNDER_REVIEW
VALIDATED
PROMOTED
REJECTED
SUPERSEDED
STALE
CONTRADICTED
REVOKED
```

Do not move directly from:

```text
CANDIDATE → CONFIRMED
```

without a validation record.

---

# 14. Safe Promotion Into telecombrain

H3 is the first phase where controlled promotion into the operational knowledge layer may be tested.

Promotion must be:

```text
auditable
reversible
idempotent
canonicalized
provenance-preserving
```

No silent graph mutation.

---

# 15. Promotion Guardrails

Before promotion validate:

```text
canonical entity resolution
duplicate relation detection
schema compatibility
relationship direction
source provenance
SME approval
conflict detection
existing relation state
rollback plan
```

If any critical check fails:

```text
BLOCK_PROMOTION
```

---

# 16. Promotion Record

Every promoted relationship should generate an immutable audit record.

Example:

```json
{
  "promotion_id": "PROM-001",
  "candidate_id": "KG-001",
  "validation_id": "VAL-001",
  "canonical_from": "topology/transport/routers/ip-rtr-01",
  "relation": "ROUTES_THROUGH",
  "canonical_to": "topology/transport/routers/mpls-pe-07",
  "display_from": "Transport Router-01",
  "display_relation": "Routes through",
  "display_to": "MPLS Edge Router-07",
  "status": "PROMOTED",
  "provenance": [],
  "rollback_supported": true
}
```

---

# 17. Canonicalization Rule

Use the existing canonical resolver.

Human-facing output should show:

```text
Transport Router-01
Routes through
MPLS Edge Router-07
```

Internal storage may use:

```text
topology/transport/routers/ip-rtr-01
ROUTES_THROUGH
topology/transport/routers/mpls-pe-07
```

---

# 18. No Duplicate Brain

All validated knowledge must ultimately belong to the existing `telecombrain`.

Do not create a second operational graph.

Allowed temporary stores:

```text
candidate store
validation store
promotion audit store
benchmark snapshot
```

But the operational knowledge destination remains:

```text
telecombrain
```

---

# 19. Controlled Live Mutation

Do not mutate live production `telecombrain` automatically during benchmark execution.

Use one of:

```text
sandbox brain
benchmark snapshot
temporary test namespace
transactional dry-run / apply flow
```

The benchmark must be reproducible.

---

# 20. Before / After Knowledge States

For each learning unit preserve:

```text
BEFORE knowledge snapshot
AFTER validated promotion snapshot
```

This enables exact comparison.

Store immutable hashes or version IDs where practical.

---

# 21. Future-Incident Evaluation

Run Incident B twice:

```text
Run 1 — BEFORE learning
Run 2 — AFTER validated learning
```

Everything except operational knowledge state should remain equivalent.

Compare:

```text
root-cause ranking
terminal state
reasoning steps
evidence requests
time / steps to useful hypothesis
explanation coverage
uncertainty
knowledge-gap detection
wrong hypotheses
```

---

# 22. H3 Improvement Metrics

Measure at least:

```text
Rank improvement of actual root cause
Strict RCA accuracy improvement
Reduction in reasoning steps
Reduction in unnecessary evidence requests
Reduction in MODEL_INSUFFICIENT
Reduction in uncertainty
Increase in explanation coverage
Increase in service-path reconstruction accuracy
Reduction in repeated knowledge-gap discovery
```

---

# 23. Learning Value Metric

Create a simple learning-value metric.

Conceptually:

```text
Learning Value =
Future performance after validated knowledge
-
Future performance before validated knowledge
```

Do not collapse all dimensions into one score unless the individual metrics remain visible.

---

# 24. Knowledge Reuse Metric

Measure:

> How often is validated knowledge actually reused by a later investigation?

Report:

```text
promoted knowledge count
reused knowledge count
useful reuse count
harmful reuse count
unused knowledge count
```

---

# 25. Transfer Across Services

Include cases where validated knowledge learned from one service improves a different service.

Example:

```text
Incident A:
Mobile Data service reveals shared MPLS dependency.

Incident B:
Enterprise VPN outage uses the same dependency.
```

This is stronger evidence of learning than replaying the same service.

---

# 26. Transfer Across Domains

Include cases such as:

```text
Mobile Core → Transport learning
later benefits IMS

RAN → Transport learning
later benefits Mobile Data

Cloud Infrastructure learning
later benefits VAS

Power / site dependency learning
later benefits multiple network domains
```

---

# 27. Transfer Across Failure Types

Validated topology should help beyond identical fault signatures.

Example:

```text
Incident A:
Hard link failure

Incident B:
Gray packet-loss condition

Same dependency knowledge,
different failure behavior.
```

---

# 28. Negative Transfer

H3 must detect harmful learning.

Example:

```text
Incorrect relation promoted
        ↓
Future incident reasoning becomes worse
```

Measure:

```text
negative transfer rate
```

Do not hide this in aggregate accuracy.

---

# 29. Stale Knowledge

Include scenarios where a once-correct relation later becomes stale.

Example:

```text
Traffic originally:
Transport Router-01
→ MPLS Edge Router-07

After network change:
Transport Router-01
→ MPLS Edge Router-09
```

The system should support:

```text
STALE
SUPERSEDED
REVOKED
```

rather than blindly trusting old learning.

---

# 30. Contradiction Detection

If future evidence contradicts promoted knowledge:

```text
do not silently force the old relation
```

Instead:

```text
flag knowledge contradiction
reduce confidence
request validation
possibly mark relation stale
```

---

# 31. Provenance Requirements

Every learned relationship must retain:

```text
discovery incident
candidate ID
supporting evidence
SME validation
promotion event
later reuse events
later contradiction events
```

This provenance should be queryable.

---

# 32. Learning Ledger

Maintain a learning ledger.

Example:

```json
{
  "knowledge_id": "KN-001",
  "display_name": "Transport Router-01 routes through MPLS Edge Router-07",
  "state": "PROMOTED",
  "discovered_in": "H2-SCN-017",
  "validated_by": "Transport Domain SME",
  "reused_in": ["H3-FUT-001", "H3-FUT-014"],
  "helpful_reuse_count": 2,
  "harmful_reuse_count": 0,
  "last_verified_at": "..."
}
```

---

# 33. Learning Confidence

Do not treat all promoted knowledge equally.

Track:

```text
validation strength
evidence strength
recency
reuse success
contradictions
```

A relationship may become:

```text
high confidence
medium confidence
stale
under review
```

---

# 34. Future Knowledge Decay

Optional but recommended:

Introduce a simple freshness model.

For example:

```text
recently validated
recently reused successfully
old but still supported
stale
contradicted
```

Do not over-engineer decay in H3.

---

# 35. H3 Scenario Design

Recommended initial benchmark:

```text
30 learning units
```

Each with:

```text
1 discovery incident
1 validation event
1 future incident
```

For stronger coverage:

```text
10 straightforward positive transfer
10 cross-domain / cross-service transfer
5 stale / changed topology
5 poisoned / incorrect validation
```

---

# 36. Positive Learning Cohort

Test cases where:

```text
validated knowledge is correct
future incident depends on it
reasoning should improve
```

Expected:

```text
positive transfer
```

---

# 37. Neutral Learning Cohort

Test cases where:

```text
validated knowledge is correct
but irrelevant to future incident
```

Expected:

```text
no material performance change
```

This prevents claiming improvement from unrelated knowledge.

---

# 38. Negative Learning Cohort

Test cases where:

```text
validated knowledge is incorrect or stale
```

Expected:

```text
harm detected
contradiction surfaced
knowledge downgraded / reviewed
```

---

# 39. H3 Baselines

Use at least:

### Baseline A — No Learning

```text
Future incident uses pre-learning telecombrain only.
```

### Baseline B — Blind Auto-Learning

```text
Candidate knowledge is auto-promoted without SME validation.
```

### Method B — FikraCore Governed Learning

```text
Candidate
→ SME validation
→ safe promotion
→ future reuse
```

H3 should show whether governed learning adds value while reducing poisoning risk.

---

# 40. H3 Success Metrics

Report:

```text
Future RCA improvement rate
Future investigation step reduction
Knowledge reuse rate
Positive transfer rate
Neutral transfer correctness
Negative transfer detection rate
Incorrect promotion rate
Stale knowledge detection rate
Contradiction detection rate
Zero Hidden Truth leakage
```

---

# 41. Human-Readable Naming Requirement

All H3 reports, UI, demos, and Mark / Zaki responses must continue using the persistent human-readable naming policy.

Example:

```text
Transport Router-01
Routes through
MPLS Edge Router-07
```

not raw slugs as the primary label.

Canonical IDs remain available for traceability.

---

# 42. Simulator UI Integration

H3 must integrate seamlessly into the existing Simulator UI.

Use the same two modes:

```text
Investigation Mode
Curated Demo Mode
```

Do not create a separate H3 application.

---

# 43. H3 Investigation Mode

Support:

```text
candidate knowledge
SME decision
promotion state
before/after knowledge graph
future incident evidence
reasoning before learning
reasoning after learning
knowledge reused
performance delta
contradictions
learning ledger
```

---

# 44. H3 Curated Demo Mode

A leadership demonstration should be able to show:

```text
Step 1 — Incident A exposes a knowledge gap
Step 2 — FikraCore proposes candidate knowledge
Step 3 — SME validates it
Step 4 — Knowledge is safely promoted
Step 5 — Different Incident B occurs
Step 6 — FikraCore reuses the validated knowledge
Step 7 — Future investigation improves
```

Final message:

> **FikraCore learns from validated operational experience.**

---

# 45. Mark / Zaki Integration

Mark and Zaki remain interchangeable names for the same assistant identity.

Mark / Zaki must consume the same structured Simulator state.

In H3, Mark / Zaki should support questions such as:

```text
What did FikraCore learn from the previous incident?
Who validated this relationship?
What evidence supported the learning?
Has this knowledge been reused before?
Show the investigation before learning.
Show the same future incident after learning.
What improved?
Is this knowledge still trusted?
Has any evidence contradicted it?
```

---

# 46. Mark / Zaki Knowledge-State Safety

Mark / Zaki must distinguish:

```text
Candidate
Validated
Promoted
Stale
Contradicted
Rejected
```

Forbidden:

```text
calling a candidate confirmed
calling rejected knowledge active
hiding contradictions
using evaluator truth as explanation
```

---

# 47. H3 UI Presentation Contract

Extend the shared UI presentation model with:

```json
{
  "learning": {
    "candidate_knowledge": [],
    "validation_decisions": [],
    "promoted_knowledge": [],
    "before_snapshot": null,
    "after_snapshot": null,
    "reused_knowledge": [],
    "performance_delta": {},
    "contradictions": [],
    "learning_ledger": []
  }
}
```

---

# 48. Curated H3 Demo Metadata

Each demo-ready learning unit may include:

```json
{
  "demo": {
    "enabled": true,
    "title": "From Unknown Dependency to Faster Future RCA",
    "audience": "leadership",
    "duration_minutes": 5,
    "steps": [
      "Discover",
      "Validate",
      "Promote",
      "Encounter Future Incident",
      "Reuse Knowledge",
      "Show Improvement"
    ],
    "final_message": "Validated experience becomes reusable operational knowledge."
  }
}
```

Presentation metadata must not affect reasoning.

---

# 49. H3 Integrity Validator

Before benchmark execution verify:

```text
Incident A and Incident B are different
candidate originates from H2-compatible discovery
validation decision exists
promotion does not use Hidden Truth
future incident genuinely depends on learned knowledge where expected
control cohorts are correctly labeled
before/after snapshots differ only by intended learning
no leakage from evaluator expectations
```

---

# 50. Promotion Sandbox

Implement a benchmark-safe promotion environment.

Recommended:

```text
telecombrain snapshot
        ↓
promotion transaction
        ↓
versioned after-snapshot
```

Do not require live production mutation for H3 validation.

---

# 51. Rollback Test

Every promotion must be reversible.

Test:

```text
promote
verify
rollback
verify original state restored
```

---

# 52. Idempotency Test

Applying the same validated promotion twice must not create duplicate relationships.

---

# 53. Conflict Test

If promoted knowledge conflicts with an existing active relation:

```text
do not silently overwrite
```

Generate a governed conflict state.

---

# 54. H3 Required Artifacts

Generate:

```text
artifacts/hypothesis/h3/
├── aggregate-report.json
├── aggregate-report.md
├── learning-units.jsonl
├── before-after-comparison.jsonl
├── positive-transfer-analysis.json
├── neutral-transfer-analysis.json
├── negative-transfer-analysis.json
├── knowledge-reuse-analysis.json
├── stale-knowledge-analysis.json
├── poisoning-resistance-analysis.json
├── promotion-audit.jsonl
├── learning-ledger.jsonl
├── baseline-comparison.json
├── integrity-report.json
└── final-h3-report.md
```

---

# 55. Candidate / Validation / Promotion Artifacts

Suggested:

```text
artifacts/knowledge-gaps/candidates/
artifacts/knowledge-validation/
artifacts/knowledge-promotions/
```

Preserve immutability of historical decisions.

---

# 56. Suggested CLI Commands

Add commands similar to:

```bash
fikracore-mvp generate-h3-learning-units
fikracore-mvp validate-h3-learning-units
fikracore-mvp review-candidate KG-001
fikracore-mvp apply-validation VAL-001
fikracore-mvp promote-knowledge PROM-001 --dry-run
fikracore-mvp promote-knowledge PROM-001 --apply
fikracore-mvp rollback-promotion PROM-001
fikracore-mvp run-h3-benchmark
fikracore-mvp diagnose-h3-unit H3-LU-001
fikracore-mvp h3-report
fikracore-mvp h3-demo H3-LU-001
```

Adapt to the existing CLI.

---

# 57. Required Tests

Add at least:

```text
test_h3_candidate_requires_validation
test_h3_rejected_candidate_not_promoted
test_h3_modified_candidate_promotes_modified_relation
test_h3_promotion_is_idempotent
test_h3_promotion_is_reversible
test_h3_hidden_truth_not_used_for_promotion
test_h3_future_incident_differs_from_discovery_incident
test_h3_positive_transfer_improves_reasoning
test_h3_neutral_transfer_does_not_fake_improvement
test_h3_negative_transfer_detected
test_h3_stale_knowledge_detected
test_h3_conflicting_knowledge_not_silently_overwritten
test_h3_learning_provenance_preserved
test_h3_mark_zaki_uses_shared_state
test_h3_demo_metadata_does_not_change_reasoning
test_h1_h2_regression_suite_still_passes
```

---

# 58. Definition of Done

H3 is complete when:

```text
[ ] H1 behavior remains unchanged
[ ] H2 behavior remains unchanged
[ ] H3 paired learning units exist
[ ] Incident A and Incident B are different
[ ] candidate knowledge comes from governed H2-compatible flow
[ ] every promotion has SME/HITL validation
[ ] safe promotion guardrails exist
[ ] promotion is idempotent
[ ] promotion is reversible
[ ] before/after knowledge snapshots exist
[ ] future incidents run before and after learning
[ ] performance deltas are measured
[ ] knowledge reuse is measured
[ ] positive transfer is measured
[ ] neutral transfer is measured
[ ] negative transfer is measured
[ ] stale knowledge handling is tested
[ ] poisoning resistance is tested
[ ] provenance is preserved
[ ] UI supports H3
[ ] Curated Demo Mode supports H3
[ ] Mark / Zaki supports H3
[ ] no Hidden Truth leakage occurs
[ ] full regression suite passes
[ ] final H3 report is generated
```

---

# 59. H3 Investment Gate

At the end answer:

> Does SME-validated operational knowledge discovered from one investigation measurably improve FikraCore's reasoning on a different future incident without introducing unacceptable learning risk?

Classify:

```text
H3_SUPPORTED
H3_PARTIALLY_SUPPORTED
H3_NOT_SUPPORTED
```

---

# 60. Recommended H3 Gate Dimensions

Evaluate:

```text
Positive Transfer
Knowledge Reuse
Future RCA Improvement
Investigation Efficiency Improvement
Negative Transfer
Poisoning Resistance
Stale Knowledge Detection
Promotion Safety
Traceability
No Hidden Truth Leakage
```

---

# 61. Suggested Gate Philosophy

Do not require every future incident to improve.

A realistic H3 result should demonstrate:

```text
relevant validated knowledge helps
irrelevant knowledge does not create fake gains
bad/stale knowledge can be detected
learning remains governed and reversible
```

That is more important than maximizing one aggregate accuracy number.

---

# 62. H3 Pitch Language

Use:

> **H3 — Learn**

> FikraCore converts validated operational experience into reusable knowledge and proves that it improves future investigations.

Avoid:

> "The AI retrains itself."

This phase is governed knowledge learning, not uncontrolled self-modification.

---

# 63. Transition to H4

Only after H3 is sufficiently supported should the project move to:

# Step 4.4 / H4 — Proactive What-If, Critical Failure Surface & Resilience Validation

H4 asks:

> Can FikraCore use its validated operational knowledge proactively to identify vulnerabilities, blast radius, and critical failure surfaces before an outage occurs?

---

# Final H1 → H4 Story

```text
H1 — REASON
Can FikraCore explain incidents using what it knows?

H2 — RECOGNIZE THE UNKNOWN
Can FikraCore detect when its knowledge is incomplete?

H3 — LEARN
Can validated operational experience improve future incidents?

H4 — PREDICT
Can the learned telecom brain identify risk before failure occurs?
```

---

# Final Principle

> Validated operational experience should become reusable knowledge — but only through governed, auditable, reversible learning.

H3 proves whether FikraCore becomes better because of what operators teach it, not because the simulator secretly gave it the answer.
