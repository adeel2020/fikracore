# FikraCore Simulator — Step 4.2 / H2 Operational Knowledge-Gap Discovery & Unknown-Unknown Validation

## Revision v1.4

Clarifies that **Mark and Zaki are interchangeable names for the same voice/chat assistant identity**. No H2 reasoning, benchmark, simulator, UI, or validation semantics are changed.

## Revision v1.3

Adds persistent Simulator UI readiness, seamlessly integrated Curated Demo Mode, and shared Mark/Zaki voice/chat integration requirements. H2 reasoning semantics remain unchanged.

## Purpose

Step 4.2 validates **H2 — Knowledge-Gap Discovery**.

H1 established that FikraCore can perform useful causal RCA reasoning and rank the actual root cause #1 in identifiable-root scenarios without access to hidden truth.

H2 asks the next, harder question:

> Can FikraCore recognize when its own operational knowledge is incomplete, distinguish that from missing evidence or a wrong hypothesis, and safely propose what knowledge may be missing without hallucinating topology?

This step is specifically designed to test **unknown unknowns**.

The goal is not to make the engine always find a root cause.

The goal is to make it know when the current `telecombrain` cannot adequately explain the observed network behavior.


---

# Presentation Naming Convention

For all examples, reports, visuals, and leadership material, use **human-readable network names**.

Preferred:

```text
Packet Gateway-01
Transport Router-01
MPLS Edge Router-07
Data Center Gateway-01
Firewall-01
Database Cluster-01
```

Avoid presentation-only abbreviations such as:

```text
IP-RTR-01
MPLS-PE7
DC-GW
```

Canonical machine IDs may still be retained internally in JSON, code, and `telecombrain` slugs.

Recommended display pattern when both are needed:

```text
Transport Router-01
(canonical: topology/transport/routers/ip-rtr-01)
```

This convention changes presentation only. It does not change topology semantics, canonicalization, or runtime behavior.

---

# Global Human-Readable Naming Requirement

This requirement applies **persistently across the entire H2 implementation**, not only to the examples in this document.

For every network, cloud, IT, OSS/BSS, database, protocol, service, infrastructure, topology, evidence, and operational term that is exposed to a human user, the system must provide a clear human-readable display name.

This applies to:

```text
CLI output
Markdown reports
JSON reports intended for human review
diagnostic reports
benchmark summaries
incident stories
knowledge-gap reports
candidate relationship reports
next-best-evidence requests
HITL / SME validation screens
leadership presentations
visualizations
Mark / Zaki responses
future UI/API presentation fields
```

Internal canonical IDs, slugs, protocol-standard abbreviations, vendor object names, and machine identifiers may remain unchanged for runtime compatibility.

The presentation layer must translate them into readable terminology.

## Required Display-Name Pattern

Every human-facing entity should support both:

```text
display_name
canonical_id
```

Example:

```json
{
  "display_name": "Transport Router-01",
  "canonical_id": "topology/transport/routers/ip-rtr-01"
}
```

Human-facing output should prefer:

```text
Transport Router-01
```

rather than:

```text
ip-rtr-01
```

When technical traceability is required, show:

```text
Transport Router-01
Canonical ID: topology/transport/routers/ip-rtr-01
```

## Acronym and Abbreviation Rule

Do not assume the audience understands telecom abbreviations.

On first human-facing use, render the expanded term with the standard acronym in parentheses when the acronym is useful.

Examples:

```text
User Plane Function (UPF)
Packet Gateway (PGW)
Mobility Management Entity (MME)
Data Network Name (DNN)
Access Point Name (APN)
IP Multimedia Subsystem (IMS)
Online Charging System (OCS)
Policy Control Function (PCF)
Diameter Routing Agent (DRA)
Session Border Controller (SBC)
Operations Support System (OSS)
Business Support System (BSS)
Provider Edge Router (PE Router)
Data Center Gateway
Network Function Virtualization Infrastructure (NFVI)
Kubernetes Cluster
Database Cluster
Load Balancer
Firewall
```

After the first expansion in the same report or view, the standard acronym may be used where it improves readability.

## Vendor and Protocol Terms

Do not rename standardized protocol names or vendor-native objects incorrectly.

Instead use:

```text
Human-readable description (standard/vendor term)
```

Examples:

```text
Diameter Credit-Control Interface (Gy)
GPRS Tunnelling Protocol (GTP)
Stream Control Transmission Protocol (SCTP)
Border Gateway Protocol (BGP)
Multiprotocol Label Switching (MPLS)
Huawei User Gateway (UGW)
```

The system must preserve technical correctness while improving readability.

## Relationship Display Names

Machine relationship types must also have human-readable labels.

Examples:

```text
DEPENDS_ON       → Depends on
ROUTES_THROUGH   → Routes through
HOSTED_ON        → Hosted on
RUNS_ON          → Runs on
MEMBER_OF        → Member of
MONITORED_BY     → Monitored by
SUPPORTS_SERVICE → Supports service
SERVES           → Serves
FAILS_OVER_TO    → Fails over to
POWERED_BY       → Powered by
```

Human-facing reports should not expose raw relationship enums unless explicitly requested.

## Evidence Display Names

Evidence sources should also be translated.

Examples:

```text
prometheus_metric     → Performance Metric
loki_log              → Network / Application Log
grafana_alert         → Monitoring Alert
tempo_trace           → Distributed Trace
change_record         → Change Record
customer_ticket       → Customer Ticket
topology_neighbor     → Topology Neighbor Information
routing_table         → Routing Table
```

## Persistence Requirement

This naming behavior must be implemented as a reusable presentation policy, not manually rewritten inside individual scenarios.

Recommended approach:

```text
Canonical object
      ↓
Display-name / terminology resolver
      ↓
Human-facing output
```

Create a reusable component such as:

```text
presentation/naming.py
```

or equivalent.

It should resolve:

```text
canonical entity ID → human-readable entity name
raw relation enum   → human-readable relation
evidence type       → human-readable evidence label
known acronym       → expanded display form
```

Do not create scenario-specific naming mappings.

## Fallback Rule

If no friendly name exists:

1. derive a readable label from structured metadata;
2. preserve the original canonical identifier for traceability;
3. never invent the technical meaning of an unknown abbreviation.

Example:

```text
Unknown technical ID: vendor-x/abc-17
Display: ABC-17
Canonical ID: vendor-x/abc-17
```

Do not fabricate an expansion for `ABC`.

## H2 Test Requirement

Add tests verifying that:

```text
human-facing reports do not expose raw canonical slugs as primary labels
known acronyms are expanded on first use
relationship enums have readable labels
canonical IDs remain available for traceability
unknown abbreviations are not falsely expanded
the naming resolver works across all H2 scenario types
```

Suggested tests:

```text
test_human_readable_entity_names
test_human_readable_relationship_names
test_acronym_expansion_on_first_use
test_canonical_id_preserved_for_traceability
test_unknown_acronym_not_invented
test_naming_policy_applies_to_all_h2_reports
```

This requirement must carry forward into H3, H4, Zaki, incident storytelling, customer-ticket journey, and leadership visualizations unless a technical/raw-output mode is explicitly requested.

---

# 1. H2 Validation Question

Validate:

> Can FikraCore detect that the operational knowledge model is insufficient, localize the likely knowledge gap, request the next-best evidence, and produce a candidate topology/relationship hypothesis without promoting it to fact?

H2 is successful only if the engine distinguishes among:

```text
KNOWN ROOT CAUSE
MISSING OPERATIONAL KNOWLEDGE
MISSING EVIDENCE
CONFLICTING EVIDENCE
WRONG CURRENT HYPOTHESIS
```

---

# 2. Key Principle

The core principle is:

```text
Unknown-unknown discovery
≠
guessing the hidden answer
```

The engine must never infer a missing relation merely because the evaluator knows one exists.

Instead:

```text
Observed evidence
        ↓
Current telecombrain model
        ↓
Expected propagation does not match observations
        ↓
Unexplained residual
        ↓
Model-insufficiency hypothesis
        ↓
Localize likely missing knowledge
        ↓
Request next-best evidence
        ↓
Candidate relationship
        ↓
Human / SME validation
```

---

# 3. Preserve H1 Baseline

Freeze all H1 outputs and regression gates.

Do not modify:

```text
H1 benchmark scenarios
H1 evaluator truth
H1 calibrated scoring policy
H1 terminal-state policy
H1 canonicalization behavior
H1 reference operator model
```

All existing H1 tests must continue to pass.

The H2 implementation must be additive.

---

# 4. Preserve the Epistemic Boundary

This boundary remains mandatory:

```text
Hidden Truth → Evaluator only
```

Forbidden:

```text
Hidden Truth → Hypothesis Engine
Hidden Truth → Knowledge-Gap Detector
Hidden Truth → telecombrain
Hidden Truth → Next-Best-Evidence Planner
Hidden Truth → candidate topology generator
```

The system under test must only see:

```text
Operational evidence
+
Operational telecombrain knowledge
+
Investigation state
```

---

# 5. H2 Simulator Design

Create H2 scenarios where the Hidden Truth contains a valid dependency or entity that the operational `telecombrain` view intentionally does not contain.

Example hidden reality:

```text
User Plane Function-01
 ↓
Transport Router-01
 ↓
MPLS Edge Router-07
 ↓
Data Center Gateway-01
```

Operational telecombrain view:

```text
User Plane Function-01
 ↓
Transport Router-01
 ↓
[knowledge gap]
 ↓
Data Center Gateway-01
```

Evidence should remain causally coherent with the hidden reality.

FikraCore must not be shown:

```text
MPLS-PE7
```

as operational knowledge if that entity or relationship is intentionally hidden for the scenario.

---

# 6. Unknown-Unknown Scenario Types

Add a dedicated H2 scenario set.

Include at least these knowledge-gap classes:

```text
1. Missing dependency edge
2. Missing intermediate node
3. Missing shared dependency
4. Missing service-to-function relationship
5. Missing failure-domain membership
6. Missing hosting/container relationship
7. Missing transport path
8. Missing external dependency
9. Stale topology relationship
10. Wrong topology direction
11. Incorrectly merged entities
12. Alias/canonical identity ambiguity
13. Missing redundancy/failover path
14. Missing monitoring dependency
15. Missing database/cache/message-bus dependency
16. Missing power/environment dependency
17. Missing roaming/interconnect dependency
18. Missing provisioning/BSS dependency
19. Missing security/control dependency
20. Multiple simultaneous knowledge gaps
```

---

# 7. Difficulty Levels

Use H2-specific difficulty levels:

```text
K1 — obvious single missing relationship
K2 — noisy evidence around one missing relationship
K3 — multi-domain hidden dependency
K4 — incomplete + stale + contradictory operational knowledge
K5 — multiple plausible missing relationships / complex unknown unknown
```

H2 should test the ability to remain uncertain when the gap cannot be uniquely identified.

---

# 8. Required Terminal-State Distinction

The engine must distinguish:

```text
EXPLAINED
PARTIALLY_EXPLAINED
MODEL_INSUFFICIENT
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
UNRESOLVED
```

H2 focuses heavily on correct use of:

```text
MODEL_INSUFFICIENT
```

But `MODEL_INSUFFICIENT` must not become a catch-all.

---

# 9. MODEL_INSUFFICIENT Definition

Use `MODEL_INSUFFICIENT` when:

> The currently available operational knowledge cannot represent a plausible causal path capable of explaining the observed evidence.

Do not use it merely because:

```text
not every symptom is explained
an evidence source is unavailable
telemetry is sparse
confidence is low
```

Those may instead imply:

```text
INSUFFICIENT_EVIDENCE
PARTIALLY_EXPLAINED
UNRESOLVED
```

---

# 10. Knowledge-Gap Hypothesis Object

Add a structured object for a detected knowledge gap.

Recommended contract:

```json
{
  "gap_id": "KG-001",
  "gap_type": "MISSING_DEPENDENCY",
  "status": "CANDIDATE",
  "affected_entities": [
    "User Plane Function-01",
    "Transport Router-07"
  ],
  "suspected_missing_relation": {
    "from": "Transport Router-07",
    "relation": "ROUTES_THROUGH",
    "to": null
  },
  "reason": "Observed degradation propagates beyond known dependency boundary.",
  "supporting_evidence": [],
  "contradicting_evidence": [],
  "unexplained_residual": [],
  "confidence": 0.64,
  "required_validation": true
}
```

Do not populate unknown entity identities from hidden truth.

---

# 11. Knowledge States

Use explicit knowledge-state semantics:

```text
CONFIRMED
SUPPORTED
INFERRED
CANDIDATE
STALE
CONTRADICTED
REJECTED
```

For topology learning:

```text
Candidate topology ≠ confirmed topology
```

Only SME/HITL validation may promote a candidate relationship to confirmed knowledge.

---

# 12. Gap Localization

The engine should identify the **boundary of model failure**.

Example:

```text
Known path:
UPF → Router-A

Observed downstream symptoms:
DC-GW, firewall, enterprise VPN

But no known dependency connects Router-A to those systems.
```

Expected H2 result:

```text
MODEL_INSUFFICIENT

Likely knowledge-gap boundary:
Router-A → downstream transport/service dependency

Not:
"Root cause is MPLS-PE7"
```

unless operational evidence independently reveals MPLS-PE7.

---

# 13. Unexplained Residual

Add or strengthen the concept of `unexplained_residual`.

Residual means:

> Observed behavior that remains causally unsupported after the best current hypothesis and known graph relationships are applied.

Represent:

```json
{
  "residual_id": "RES-001",
  "evidence_ids": ["EV-101", "EV-102"],
  "affected_services": ["mobile-data"],
  "known_path_exhausted_at": "ip-rtr-07",
  "severity": 0.81,
  "structural_suspicion": true
}
```

Residual alone does not prove missing topology.

It is evidence for further investigation.

---

# 14. Model-Observation Contradiction

Add explicit detection of:

```text
Expected behavior from known model
        vs
Observed behavior
```

Examples:

```text
Known model predicts only one service impacted
Observed evidence shows three unrelated services impacted
```

or:

```text
Known model predicts path A
Evidence consistently appears on path B
```

Generate a structured contradiction record.

---

# 15. Next-Best-Evidence Planner

When a knowledge gap is suspected, FikraCore should determine:

> What observation would reduce uncertainty the most?

Possible evidence requests:

```text
topology neighbor query
routing table
interface counters
traceroute
MPLS LSP path
BGP state
ARP/ND table
service mapping
Kubernetes service/endpoints
VM/host placement
load-balancer backend map
firewall session path
DNS resolution path
database dependency
change record
NMS inventory
CMDB relation
power/facility alarm
external carrier status
```

Do not request evidence randomly.

---

# 16. Evidence-Request Ranking

Rank next-best evidence by a utility score.

Conceptual dimensions:

```text
Expected information gain
Discrimination power
Acquisition cost
Latency
Operational risk
Data reliability
Availability
```

A simple implementation is acceptable.

Do not over-engineer it during H2.

---

# 17. Required Evidence Request Object

Example:

```json
{
  "request_id": "NBE-001",
  "question": "Which downstream transport node carries traffic from Transport Router-07 toward Data Center Gateway-01?",
  "evidence_type": "TOPOLOGY_NEIGHBOR",
  "target": "Transport Router-07",
  "expected_information_gain": 0.81,
  "cost": 0.20,
  "risk": 0.05,
  "priority": 1,
  "hypotheses_discriminated": [
    "KG-001",
    "KG-002"
  ]
}
```

---

# 18. Falsification Loop

H2 must use a falsification-oriented loop:

```text
Current explanation
        ↓
Expected observations
        ↓
Compare with actual observations
        ↓
Support / contradiction
        ↓
Retain / reject
        ↓
Identify unexplained residual
        ↓
Test model sufficiency
        ↓
Request next-best evidence
```

Preserve rejected hypotheses.

Do not silently discard failed explanations.

---

# 19. Assumption Ledger

Add or extend the investigation assumption ledger.

Each assumption should have:

```text
CONFIRMED
SUPPORTED
UNCERTAIN
UNTESTED
CONTRADICTED
REJECTED
```

Example:

```json
{
  "assumption": "UPF traffic to dc-gw-01 traverses known router path",
  "state": "CONTRADICTED",
  "evidence": ["EV-202", "EV-205"]
}
```

Unknown unknowns often surface as failed assumptions.

---

# 20. Prevent Hallucinated Topology

Add explicit safeguards.

The engine must not write:

```text
Router-A ROUTES_THROUGH MPLS-PE7
```

as a confirmed fact merely because it explains the evidence.

It may produce:

```text
Candidate missing transport dependency downstream of Router-A
```

or, if evidence identifies the entity:

```text
Candidate:
Router-A ROUTES_THROUGH MPLS-PE7

status = CANDIDATE
```

Still require validation before promotion.

---

# 21. No Automatic Live telecombrain Mutation

H2 must not automatically change live gbrain / `telecombrain`.

Allowed:

```text
candidate knowledge artifact
candidate link artifact
validation queue
dry-run mutation plan
```

Forbidden:

```text
automatic add_link into live telecombrain
automatic schema mutation
automatic deletion/rewrite
```

---

# 22. Candidate Knowledge Store

Keep candidate learning separate from confirmed operational knowledge.

Suggested path:

```text
artifacts/knowledge-gaps/candidates/
```

Example:

```text
artifacts/knowledge-gaps/candidates/KG-001.json
```

A candidate may include:

```text
proposed relation
support
contradiction
provenance
confidence
required SME role
validation status
```

---

# 23. SME / HITL Validation Simulation

H2 can simulate the validation workflow without treating simulator truth as human knowledge.

Workflow:

```text
Candidate gap
        ↓
SME review requested
        ↓
SME decision:
  ACCEPT
  REJECT
  MODIFY
  NEED_MORE_EVIDENCE
```

For benchmark purposes, evaluator may use hidden truth to score whether the candidate was appropriate.

But the runtime engine must not receive the hidden answer.

---

# 24. H2 Benchmark Metrics

Measure at least:

```text
Correct MODEL_INSUFFICIENT detection rate
False MODEL_INSUFFICIENT rate
Knowledge-gap localization accuracy
Gap-type classification accuracy
Missing-edge boundary accuracy
Next-best-evidence usefulness
Hallucinated-topology rate
Correct abstention rate
Evidence-vs-model insufficiency discrimination
Canonical-resolution correctness
```

---

# 25. Leadership-Friendly Metric Names

For pitch material, prefer clear business/engineering language and human-readable network labels.

Prefer:

```text
Knowledge Gap Detected
Gap Localized
Next Evidence Recommended
No Hallucinated Topology
Candidate Relationship Proposed Safely
```

Avoid overly technical ranking terminology in leadership visuals.

---

# 26. H2 Evaluation Levels

Evaluate separately:

```text
Level 1 — Did engine recognize current model is insufficient?
Level 2 — Did engine localize the correct gap boundary?
Level 3 — Did engine identify the right type of missing relation?
Level 4 — Did engine request useful next evidence?
Level 5 — Did engine avoid inventing unverified topology?
```

---

# 27. Unknown-Unknown Success Example

Hidden truth:

```text
Packet Gateway-01 → Transport Router-01 → MPLS Edge Router-07 → Data Center Gateway-01
```

Operational knowledge:

```text
Packet Gateway-01 → Transport Router-01
Data Center Gateway-01 exists independently
No path known between them
```

Observed evidence:

```text
Packet Gateway-01 throughput drop
Transport Router-01 packet loss
Data Center Gateway-01 packet loss
Multiple downstream services impacted
```

Good H2 result:

```text
MODEL_INSUFFICIENT

Known model stops at Transport Router-01.
Observed downstream impact cannot be explained by current dependencies.

Candidate knowledge gap:
Missing transport dependency between Transport Router-01 and the downstream Data Center path.

Next-best evidence:
Retrieve the transport-neighbor / MPLS path from Transport Router-01 toward Data Center Gateway-01.
```

Bad result:

```text
Root cause = MPLS Edge Router-07
```

if MPLS Edge Router-07 was never visible in operational evidence.

---

# 28. Missing Evidence Example

Known topology is complete:

```text
User Plane Function-01 → Transport Router-01 → MPLS Edge Router-07 → Data Center Gateway-01
```

But only one alarm is available.

Expected:

```text
INSUFFICIENT_EVIDENCE
```

Not:

```text
MODEL_INSUFFICIENT
```

---

# 29. Wrong Hypothesis Example

Known model and evidence are sufficient, but the first hypothesis is inconsistent with healthy signals.

Expected:

```text
reject hypothesis
continue reasoning
```

Not:

```text
MODEL_INSUFFICIENT
```

This distinguishes failed reasoning from missing knowledge.

---

# 30. Conflicting Evidence Example

Evidence sources disagree:

```text
NMS reports link down
device telemetry reports link up
traffic still passing intermittently
```

Expected:

```text
CONFLICTING_EVIDENCE
```

or continued investigation.

Do not convert every contradiction into a topology gap.

---

# 31. Scenario Generation Rules

For H2 scenarios:

1. Generate full Hidden Truth Graph.
2. Generate causally coherent incident.
3. Generate evidence from Hidden Truth.
4. Derive an intentionally incomplete operational topology view.
5. Remove or corrupt only the knowledge required by the scenario design.
6. Verify that the missing knowledge is not leaked through metadata.
7. Run the normal truth-blind hypothesis engine.
8. Evaluate afterward against hidden truth.

---

# 32. No Trivial Leakage

Check for hidden information in:

```text
filenames
IDs
scenario names
descriptions
alarm text
metadata
ground-truth paths
evaluator expectation fields
```

Example forbidden leakage:

```text
SCN-MISSING-MPLS-EDGE-ROUTER-07
```

Prefer opaque IDs:

```text
H2-SCN-017
```

---

# 33. H2 Integrity Validator

Add H2-specific validation.

Check:

```text
hidden topology contains intended relation
operational topology does not contain intended relation
evidence remains causally consistent
removed knowledge is not leaked
scenario remains solvable at intended H2 level
candidate gap is evaluable
next-best-evidence target exists
```

Reject invalid scenarios before benchmark execution.

---

# 34. H2 Scenario Count

Start with a focused set before scaling.

Recommended:

```text
20 knowledge-gap classes
×
3 variants each
=
60 H2 scenarios
```

Variants may represent:

```text
clean
noisy
cross-domain
```

If implementation effort is high, start with 30 and expand after validation.

Do not generate hundreds before confirming the benchmark design works.

---

# 35. Comparison Baselines

Use at least two baselines:

```text
Baseline A:
Never claim model insufficiency; always force best RCA.

Baseline B:
Simple residual threshold → MODEL_INSUFFICIENT.
```

Compare FikraCore against both.

This demonstrates whether structured gap reasoning adds value beyond simplistic abstention.

---

# 36. H2 Required Reports

Generate:

```text
artifacts/hypothesis/h2/
├── aggregate-report.json
├── aggregate-report.md
├── run-diagnostics.jsonl
├── model-insufficiency-analysis.json
├── gap-localization-analysis.json
├── next-best-evidence-analysis.json
├── hallucination-analysis.json
├── by-gap-type.json
├── by-difficulty.json
├── baseline-comparison.json
├── boundary-leakage-report.json
├── candidate-knowledge/
└── final-h2-report.md
```

---

# 37. Suggested CLI Commands

Add commands similar to:

```bash
fikracore-mvp generate-h2-scenarios
fikracore-mvp validate-h2-scenarios
fikracore-mvp run-h2-benchmark
fikracore-mvp diagnose-h2-run H2-SCN-017
fikracore-mvp h2-report
```

Adapt to the existing CLI structure.

---

# 38. Required Tests

Add tests for at least:

```text
test_hidden_gap_not_visible_to_engine
test_model_insufficient_when_required_edge_missing
test_insufficient_evidence_when_model_complete
test_conflicting_evidence_not_misclassified_as_model_gap
test_gap_boundary_localization
test_candidate_relation_not_confirmed
test_no_automatic_telecombrain_mutation
test_next_best_evidence_ranked
test_unknown_entity_not_invented
test_hidden_truth_not_used_in_runtime
test_h2_scenario_leakage_detection
test_h1_regression_suite_still_passes
```

---

# 39. Acceptance Criteria

H2 is complete when:

```text
[ ] H1 behavior remains unchanged
[ ] dedicated H2 scenarios exist
[ ] H2 integrity validator passes all accepted scenarios
[ ] hidden topology is never visible to runtime reasoning
[ ] MODEL_INSUFFICIENT is distinguished from evidence insufficiency
[ ] knowledge-gap boundary can be localized
[ ] candidate gap objects are generated
[ ] candidate knowledge is never auto-promoted
[ ] next-best-evidence requests are generated
[ ] false model-gap rate is measured
[ ] topology hallucination rate is measured
[ ] baseline comparisons are complete
[ ] all H2 tests pass
[ ] final H2 report is generated
```

---

---

# Simulator UI, Curated Demonstration & Zaki Integration Requirement

H2 must produce outputs that are directly consumable by the future **FikraCore Simulator UI**.

This is not a separate demo application.

The Simulator UI must support two seamlessly connected presentation modes using the same scenario, evidence, reasoning state, and result:

```text
Investigation Mode
Curated Demo Mode
```

Both modes must be driven by the same backend contracts.

## Shared Architecture

```text
H1-H4 Scenario
      ↓
Reasoning / Simulation Engine
      ↓
Structured Scenario & Investigation State
      ├── Investigation Mode
      ├── Curated Demo Mode
      └── Mark / Zaki Voice / Chat
```

No separate fake demo data, duplicated reasoning logic, or presentation-only answers are allowed.

The curated demonstration must use the same evidence and engine outputs that would be used during an actual investigation.

## Investigation Mode

Investigation Mode is intended for engineering analysis.

It should support:

```text
Evidence timeline
Affected services
Topology view
Current hypotheses
Ranked root-cause candidates
Knowledge gaps
Unexplained residual
Next-best evidence
Assumption ledger
Candidate relationships
SME validation state
Reasoning provenance
Confidence
Terminal state
```

Technical detail may be available on demand, but human-readable terminology remains the default.

## Curated Demo Mode

Curated Demo Mode is intended for leadership, stakeholder, and product demonstrations.

It must support:

```text
Scenario selection
Reset
Replay
Step-by-step reveal
Guided narration
Highlighted affected path
Highlighted evidence
Highlighted root cause or knowledge gap
Human-readable labels
Concise explanation
Hide/show technical detail
Final proof point
```

The user must be able to demonstrate multiple curated scenarios across H1-H4 without leaving the Simulator UI.

Example scenario library:

```text
H1 — Causal RCA Validation
• Cross-domain transport failure
• Shared dependency failure
• Misleading change event

H2 — Knowledge-Gap Discovery
• Missing transport dependency
• Hidden shared infrastructure
• Stale topology relationship

H3 — Validated Learning
• Incident before learning
• SME-validated knowledge
• Different future incident after learning

H4 — Proactive Resilience
• What-if transport failure
• Shared failure-domain exposure
• Critical dependency analysis
```

## Standard UI Presentation Model

H2 must define a reusable presentation contract that can later be reused by H1, H3, and H4.

Recommended fields:

```json
{
  "scenario": {
    "id": "H2-SCN-017",
    "title": "Missing Transport Dependency",
    "stage": "H2",
    "objective": "Detect an operational knowledge gap without inventing the missing topology."
  },
  "impact": {
    "summary": "Mobile data degradation across multiple downstream services.",
    "affected_services": []
  },
  "timeline": [],
  "topology": {
    "visible_entities": [],
    "visible_relationships": [],
    "highlighted_path": [],
    "gap_boundary": null
  },
  "reasoning": {
    "hypotheses": [],
    "terminal_state": "MODEL_INSUFFICIENT",
    "explanation": "",
    "confidence": 0.0,
    "unexplained_residual": []
  },
  "next_best_evidence": [],
  "candidate_knowledge": [],
  "validation": {
    "state": "PENDING"
  },
  "presentation": {
    "current_step": 1,
    "available_steps": [],
    "headline": "",
    "key_message": "",
    "technical_details_available": true
  }
}
```

The exact schema may adapt to the existing implementation, but the same structured state must support both UI modes.

---

# Mark / Mark / Zaki Voice / Chat Integration

The existing Mark / Zaki assistant must connect to both Simulator UI modes.

Mark / Zaki is a **single conversation, orchestration, and presentation layer**.

Zaki is not the authoritative RCA or topology-learning engine.

It must consume the same structured scenario/investigation state shown by the UI.

## Zaki in Investigation Mode

Mark / Zaki should support questions such as:

```text
Why is this root cause ranked #1?
What evidence supports this hypothesis?
What evidence contradicts it?
Why is the model marked insufficient?
Where does the known topology stop?
What should I check next?
Show the affected service path.
What assumption failed?
What evidence would reduce uncertainty the most?
```

Responses must be grounded in the current investigation state.

Zaki must not invent relationships or evidence that are absent from the structured state.

## Zaki in Curated Demo Mode

Mark / Zaki becomes a guided presenter while remaining grounded in the same engine output.

Examples:

```text
Start the H2 missing-dependency scenario.
Explain what FikraCore currently knows.
Show why the current topology is insufficient.
Reveal the knowledge-gap boundary.
Why didn't FikraCore force a root-cause answer?
Show the next recommended evidence.
Continue to SME validation.
Replay this scenario from the beginning.
```

Demo narration should be concise, human-readable, and presentation-friendly.

## Mode Awareness

Mark / Zaki must know which presentation mode is active:

```text
INVESTIGATION
DEMO
```

Suggested behavioral difference:

```text
Investigation Mode
→ detailed
→ evidence-oriented
→ interactive
→ operational

Curated Demo Mode
→ concise
→ guided
→ presentation-friendly
→ step-aware
```

The reasoning source remains identical in both modes.

## Zaki Context Contract

Mark / Zaki should receive a structured context payload containing at least:

```text
active scenario
active H-stage
active presentation mode
current presentation step
visible evidence
visible topology
current hypotheses
current terminal state
knowledge-gap state
next-best evidence
candidate knowledge
validation status
human-readable display names
```

Mark / Zaki should not need to reconstruct the incident state independently from raw chat history.

## Mark / Zaki Must Not Create a Parallel Truth

Forbidden:

```text
UI says MODEL_INSUFFICIENT
while Mark / Zaki declares a definitive root cause

UI shows Candidate relationship
while Mark / Zaki calls it Confirmed

UI has no evidence for an entity
while Mark / Zaki introduces it as fact
```

The UI and Mark / Zaki must remain synchronized through the same structured state.

---

# Curated Scenario Metadata

Every H2 scenario intended for demonstration should include optional presentation metadata.

Recommended:

```json
{
  "demo": {
    "enabled": true,
    "title": "The Missing Transport Dependency",
    "audience": "leadership",
    "duration_minutes": 4,
    "learning_objective": "Show how FikraCore recognizes that its own network knowledge is incomplete.",
    "steps": [
      "Observe impact",
      "Review known topology",
      "Test current hypotheses",
      "Detect model gap",
      "Recommend next evidence",
      "Propose candidate knowledge",
      "Request SME validation"
    ],
    "final_message": "FikraCore knows when it does not know."
  }
}
```

This metadata controls presentation only.

It must not affect reasoning or evaluation.

---

# Curated Demonstration Integrity

Add explicit safeguards:

```text
Demo mode must not reveal hidden truth early.
Demo metadata must not influence hypothesis ranking.
Demo step ordering must not change engine outputs.
Mark / Zaki demo narration must not access evaluator-only data.
Reset/replay must reproduce the same deterministic scenario.
```

The curated experience may control what is visually revealed to the audience, but it must not change what the reasoning engine was allowed to know.

---

# UI-Ready Human-Readable Output

The global human-readable naming policy applies to all Simulator UI and Mark / Mark / Zaki outputs.

The UI should display:

```text
Transport Router-01
```

as the primary label.

Technical details may expose:

```text
Canonical ID:
topology/transport/routers/ip-rtr-01
```

The same display-name resolver must be used by:

```text
Simulator UI
Curated Demo Mode
Mark / Zaki Voice
Mark / Zaki Chat
Markdown reports
leadership visuals
```

This prevents inconsistent terminology between the UI and voice assistant.

---

# H2 UI / Demo / Zaki Test Requirements

Add tests for at least:

```text
test_same_state_drives_investigation_and_demo_modes
test_demo_metadata_does_not_change_reasoning
test_zaki_consumes_structured_investigation_state
test_zaki_cannot_access_hidden_truth
test_zaki_does_not_promote_candidate_to_confirmed
test_zaki_mode_awareness
test_demo_reset_replay_is_deterministic
test_ui_uses_human_readable_display_names
test_ui_preserves_canonical_ids_for_traceability
test_demo_scenario_step_order_is_presentation_only
```

---

# H2 Definition-of-Done Additions

H2 is not complete until:

```text
[ ] structured UI presentation model exists
[ ] Investigation Mode can consume H2 output
[ ] Curated Demo Mode can consume the same H2 output
[ ] curated demo metadata is separated from reasoning data
[ ] reset/replay is supported deterministically
[ ] Mark / Zaki consumes the same structured state as the UI
[ ] Mark / Zaki supports both Investigation and Demo modes
[ ] Mark / Zaki cannot access Hidden Truth
[ ] Mark / Zaki cannot contradict knowledge-state semantics
[ ] human-readable naming is consistent across UI and Mark / Zaki
[ ] no duplicate demo reasoning path exists
```

These are interface/output-contract requirements.

They do not alter H2's causal reasoning objective or H1's validated reasoning behavior.


# 40. H2 Investment Gate

At the end answer:

> Can FikraCore recognize when its operational knowledge is incomplete and safely drive discovery of missing knowledge without hallucinating the answer?

Classify:

```text
H2_SUPPORTED
H2_PARTIALLY_SUPPORTED
H2_NOT_SUPPORTED
```

Document evidence.

---

# 41. What H2 Does NOT Yet Prove

H2 does not prove that learned knowledge improves future incidents.

That is H3.

H2 proves:

```text
detect gap
localize gap
request evidence
propose candidate safely
```

H3 will test:

```text
validate candidate
promote to operational knowledge
encounter different future incident
measure whether reasoning improves
```

---

# 42. Transition to H3

Only if H2 is sufficiently supported should the project move to:

# Step 4.3 / H3 — Validated Knowledge Learning & Future-Incident Improvement

The H3 question will be:

> Does SME-validated knowledge discovered from one investigation improve FikraCore's reasoning on a different future incident?

---

# Final Principle

> A trustworthy telecom brain must know when it does not know.

H2 is not about making FikraCore guess better.

It is about making FikraCore detect the limits of its current operational model, reduce uncertainty deliberately, and learn only through validated evidence.
