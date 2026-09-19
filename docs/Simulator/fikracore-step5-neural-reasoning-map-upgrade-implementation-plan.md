# FikraCore Step 5 Upgrade — Neural Reasoning Map Implementation Plan

## Purpose

Upgrade the **existing Step 5 UI** into the new **FikraCore Neural Reasoning Map** experience without replacing the validated Step 5 shell, navigation, scenario/run handling, hypothesis workflow, knowledge-gap workflow, Next-Best Evidence, Learning, or Zaki.

The current UI already contains:

```text
header
navigation
scenario selector
run controls
live simulation journey
unified live event stream
Hyper Canvas
parallel hypothesis board
reasoning focus
service impact
knowledge gaps
next-best evidence
learning
Zaki
```

These remain.

The primary change is:

> **Replace the current central graph/status visualization with a backend-synchronized Neural Reasoning Map that visually explains how evidence, reasoning pathways, hypotheses, gaps, validation, learning, and final domain attribution connect during the live investigation.**

This is an **upgrade inside Step 5**, not a new phase and not a rewrite of H1–H4 reasoning.

---

# 1. Upgrade Strategy

Use this implementation strategy:

```text
Existing Step 5 shell
        ↓
Preserve routes / state machine / scenario handling
        ↓
Extend backend state contracts additively
        ↓
Add dynamic reasoning pathway state
        ↓
Add intelligence synthesis state
        ↓
Add explicit domain attribution state
        ↓
Replace only the central visualization
        ↓
Synchronize all surrounding panels to the same revision
```

Do not rewrite:

```text
H1 reasoning
H2 gap discovery
H3 learning
H4 what-if
scenario compiler
live MCP integration
Zaki orchestration
existing Step 5 navigation
```

unless an additive contract change is required.

---

# 2. Existing UI Elements to Keep

Preserve the current layout and product shell.

## Keep

```text
Top Header
Scenario Selector
Run Status
telecombrain MCP Status
Primary Navigation
Live Simulation Journey
Unified Live Event Stream
Parallel Hypothesis Board
What FikraCore Is Doing
Service Impact
Knowledge Gaps
Next Best Evidence
Learning
Zaki
```

## Replace

Replace the existing central:

```text
Hyper Canvas / static network causal graph
```

with:

> **FikraCore Neural Reasoning Map**

---

# 3. Source Modes

The reasoning map must support two entry modes.

## Live Operations

Source:

```text
Intent Violation
```

Example:

```text
Enterprise APN success rate below target
```

The intent violation starts the investigation.

It does **not** determine the root cause.

It establishes:

```text
service context
SLO / intent breach
initial scope
investigation reason
```

Actual reasoning remains evidence-driven.

## Offline Network Simulation

Source:

```text
Selected Scenario
```

Example:

```text
H4-WI-001 — MPLS Edge Router Failure
```

The selected scenario releases deterministic synthetic operational evidence.

The scenario itself must not directly activate pathways or reveal truth.

---

# 4. Shared Investigation Flow

After entry, Live and Simulation must use the same workflow:

```text
Intent Violation / Scenario
        ↓
Build Incident Evidence
        ↓
Correlate
        ↓
Activate Reasoning Pathways
        ↓
Generate H1 / H2 / H3 / H4
        ↓
Test / Falsify
        ↓
Detect Knowledge Gaps
        ↓
Request Next Best Evidence
        ↓
Retest
        ↓
Intelligence Synthesis
        ↓
Domain Attribution
        ↓
Validation
        ↓
Learning / Action
```

Source differs.

Reasoning architecture does not.

---

# 5. Investigation Journey

Preserve the existing journey at the top.

Use human-readable stages:

```text
1. Detect Network Degradation
2. Build Incident Evidence
3. Correlate Across Domains
4. Identify Candidate Causes
5. Test & Eliminate Causes
6. Resolve Missing Network Context
7. Converge Multi-Domain Intelligence
8. Validate with Domain Engineer
9. Recommend Action / Capture Learning
```

Backend stages may remain canonical internally:

```text
TRIGGER
SIGNAL_FLOOD
CORRELATION
HYPOTHESIS_GENERATION
HYPOTHESIS_TESTING
KNOWLEDGE_GAP_CHECK
NEXT_BEST_EVIDENCE
VALIDATION
LEARNING
ACTION
```

UI stage labels are presentation only.

---

# 6. Neural Reasoning Map Objective

The center must answer:

> **What is happening, why is it happening, what intelligence is being used, what remains unknown, and how is FikraCore moving toward a conclusion?**

The map should visually connect:

```text
Evidence
→ Reasoning Pathways
→ Hypotheses
→ Gaps / Tests
→ Intelligence Synthesis
→ Validation / Learning
→ Domain Attribution
```

Do not render another dashboard inside the center.

The center should feel like a **live reasoning fabric**.

---

# 7. Visual Structure

Use a free-form neural layout inspired by the existing voice-assistant UI.

Recommended spatial hierarchy:

```text
LEFT
Source Mode
Live Intent / Offline Scenario

LEFT-CENTER
Evidence Streams

AROUND CENTER
Reasoning Pathways
Hypotheses
Knowledge Gaps

CENTER
Intelligence Synthesis

RIGHT-CENTER
Validation
Learning

FAR RIGHT / END
Domain Attribution
```

Important:

> **Domains must not appear as a source column. Domain attribution belongs at the end.**

The map may still reference source entity ownership internally, but the visual domain list is shown only after synthesis/validation as attribution.

---

# 8. Human-Readable Naming Contract

Never show opaque IDs as primary labels.

Use:

```text
display_name
canonical_id
```

Visible UI uses `display_name`.

Internal correlation uses `canonical_id`.

## Evidence

Visible:

```text
BGP Adjacency Flapping on IP/MPLS Edge Router-07
Packet Loss Increase on Enterprise APN Path
Customer Ticket: Enterprise APN Outage
Routing Change CR-7721
```

Not:

```text
EVT-102
EVT-991
```

## Reasoning Pathways

Visible exact names:

```text
Operational Evidence
Service Dependency
Subscriber Journey
Change & Configuration
Traffic & Capacity
Control & Signaling
Resilience & Failover
Historical Pattern
Knowledge Gap
```

## Hypotheses

Visible:

```text
H1 — IP/MPLS Edge Router-07 Failure
H2 — Downstream Service Overload
H3 — DNS Resolution Latency
H4 — Policy Misconfiguration
```

Use standard H1–H4 presentation.

## Knowledge Gaps

Visible:

```text
Redundant MPLS Path Health Unknown
Router-07 Interface Error Counters Missing
BGP Adjacency History Missing
```

Not:

```text
GAP-018
```

## Validation

Visible:

```text
Transport Engineer Confirmed Router-07 as Primary Cause
```

Not:

```text
VAL-003
```

## Domain Attribution

Visible:

```text
Primary Domain — IP Transport
Contributing Domain — Mobile Core
Affected Domain — RAN
```

Not:

```text
ATTR-001
```

Opaque IDs may exist only in metadata, trace, audit, and debugging.

---

# 9. Evidence Layer

The existing Unified Live Event Stream remains the authoritative raw observation surface.

Supported evidence types:

```text
Alarm
KPI
Metric
Log
Trace
Change
Ticket
Healthy Signal
```

The map should visualize admitted evidence as active nodes or streams.

Important rule:

> Raw evidence and reasoning must remain separate.

Do not show:

```text
common cause found
root cause selected
hypothesis confirmed
```

inside the raw event stream.

---

# 10. Reasoning Pathways

Reasoning pathways are analytical perspectives.

They are not domains.

Use:

```text
Operational Evidence
Service Dependency
Subscriber Journey
Change & Configuration
Traffic & Capacity
Control & Signaling
Resilience & Failover
Historical Pattern
Knowledge Gap
```

Optional additional pathways may be discovered when justified.

Conceptual rule:

> **Evidence = what FikraCore observes.**
>
> **Reasoning pathway = how FikraCore interprets or tests those observations.**

---

# 11. Dynamic Pathway Activation

Do not keep every pathway fully active.

Each pathway has a runtime state:

```text
DORMANT
DISCOVERED
ACTIVE
RESOLVED
REJECTED
```

Activation must be evidence-driven.

Examples:

```text
Recent routing change admitted
→ Change & Configuration ACTIVE

Packet-loss KPI admitted
→ Traffic & Capacity ACTIVE

Backup-path state required
→ Resilience & Failover ACTIVE

Similar prior incident found
→ Historical Pattern ACTIVE

Missing router counters identified
→ Knowledge Gap ACTIVE
```

Do not activate pathways merely because the scenario name contains "MPLS" or "VoLTE".

---

# 12. Persistent Capability, Dynamic Illumination

Underlying valid evidence→pathway relations may remain known to the backend.

Visual rule:

```text
Dormant valid relation
= very faint neural conduit

Active relation
= illuminated cyan conduit

Current evidence flow
= moving light pulse on same conduit

Supports hypothesis
= green pulse

Contradicts hypothesis
= red pulse

Unresolved / needs evidence
= amber pulse

Historical / learned context
= purple pulse

Rejected relation
= grey faded
```

Do not use separate arrow design plus circuitry.

Use one structured neural-connection language.

---

# 13. Visual Style of Connections

Avoid rigid PCB circuitry.

Avoid random decorative curves.

Use:

> **structured organic neural conduits**

Characteristics:

```text
smooth curved splines
clear start/end anchors
limited crossings
visible junctions
stable geometry
subtle cyan base
semantic colored activation
```

Connection geometry must be deterministic and stable across revisions.

The map should feel neural and alive, not robotic.

---

# 14. Concrete Cross-Connections

Every visible cross-connection must map to an authoritative backend relation.

Example:

```text
Packet Loss Increase on Enterprise APN Path
→ Traffic & Capacity
```

Reason:

```text
Packet-loss KPI exceeds the degradation threshold.
```

Example:

```text
Routing Change CR-7721
→ Change & Configuration
```

Reason:

```text
Change completed 6 minutes before the intent violation.
```

Example:

```text
Resilience & Failover
→ H1 — IP/MPLS Edge Router-07 Failure
```

Reason:

```text
Redundant path did not take traffic as expected.
```

No random decorative connections.

---

# 15. Click-to-Explain

Every node and connection must be explainable.

On click, show:

```text
What is this?
Why is it active?
What evidence supports it?
What hypothesis does it affect?
What is still unknown?
What changed most recently?
```

Example:

```text
Connection:
Routing Change CR-7721
→ Change & Configuration

Why:
The change completed 6 minutes before degradation.

Current Role:
Temporal relevance confirmed.
Causal relevance still under test.
```

---

# 16. Hypothesis Competition

Keep the existing Parallel Hypothesis Board.

Synchronize it with the Neural Reasoning Map.

Standard visible identifiers:

```text
H1
H2
H3
H4
```

Example:

```text
H1 — IP/MPLS Edge Router-07 Failure
H2 — Downstream Service Overload
H3 — DNS Resolution Latency
H4 — Policy Misconfiguration
```

Unknown confidence must show:

```text
Unranked
```

not:

```text
0%
```

---

# 17. Hypothesis States

Support:

```text
CANDIDATE
UNRANKED
RANKED
TESTING
SUPPORTED
WEAKENING
NEEDS_MORE_EVIDENCE
TESTING_NEW_EVIDENCE
REJECTED
ROOT_CANDIDATE
CONFIRMED
```

Hypotheses evolve only from backend reasoning.

Frontend must never compute confidence.

---

# 18. Evidence → Pathway → Hypothesis

The map must make many-to-many relationships visible.

Example:

```text
BGP Flap
   ├──→ Control & Signaling
   ├──→ Service Dependency
   └──→ Resilience & Failover
```

Then:

```text
Control & Signaling ───────► H1
Service Dependency ────────► H1
Resilience & Failover ─────► H1

Traffic & Capacity ────────► H2
Operational Evidence ──────► H2
```

This relationship is the key visual value of the Neural Reasoning Map.

---

# 19. Knowledge Gaps

Knowledge gaps remain visible beside/around synthesis.

Use exact names.

Examples:

```text
Router-07 Interface Error Counters Missing
Redundant MPLS Path State Unknown
BGP History Missing
```

Each gap must link to:

```text
affected hypothesis
affected pathway
next-best evidence request
```

---

# 20. Next-Best Evidence

Preserve the existing Next Best Evidence panel.

Synchronize it with the map.

Flow:

```text
Knowledge Gap
→ Request Evidence
→ Evidence Arrives
→ Pathway Reactivates
→ Hypothesis Retested
→ Synthesis Updated
```

The visual request may use a white/cyan pulse.

A request remains incomplete until authoritative evidence returns.

---

# 21. Intelligence Synthesis

Place **Intelligence Synthesis** at the center.

This is the convergence layer.

It is not the operational conclusion.

It answers:

> **What do the active evidence, reasoning pathways, hypothesis tests, contradictions, and unresolved gaps collectively support?**

Possible synthesis dimensions:

```text
Evidence Support
Service Dependency Fit
Temporal Fit
Change Relevance
Impact Alignment
Traffic / Capacity Fit
Control / Signaling Fit
Historical Similarity
Contradictions
Knowledge Gaps
Validation State
```

Possible synthesis states:

```text
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
PARTIALLY_EXPLAINED
STRONGLY_SUPPORTED
ROOT_CANDIDATE
MODEL_INSUFFICIENT
```

Do not force a single numeric score.

---

# 22. Remove Separate Operational Conclusion Node

Do not render a separate large "Operational Conclusion" node in the central map.

The synthesis state itself can drive:

```text
leading hypothesis
root candidate
remaining uncertainty
validation readiness
domain attribution readiness
```

The user should see the reasoning converge before downstream outcomes appear.

---

# 23. Validation

Preserve validation as a distinct stage.

Visible example:

```text
Transport Engineer Review Pending
```

States:

```text
PENDING
ACCEPTED
REJECTED
MODIFIED
NEED_MORE_EVIDENCE
```

Validation must be based on the backend evidence package.

No client-side confirmation.

---

# 24. Learning

Preserve Learning.

Before validation:

```text
No validated learning yet
```

After accepted validation:

```text
Validated Learning Candidate
```

Learning may capture:

```text
causal relationship
diagnostic pattern
validated dependency
procedure refinement
effective evidence test
known false positive
```

Hidden Truth is never used as learning input.

---

# 25. Domain Attribution at the End

Move all domain attribution to the far right/end of the reasoning journey.

This answers:

> **Which domain is primarily responsible, which domains contributed, and which domains were impacted?**

Example:

```text
Primary Domain
IP Transport

Contributing Domains
Mobile Core
OSS/BSS

Affected Domains
RAN
Mobile Core
IMS / VoLTE
```

Domain attribution must appear only when backend reasoning supports it.

Do not show a domain as "culprit" at run start.

---

# 26. Domain Attribution States

Use explicit roles:

```text
PRIMARY
CONTRIBUTING
AFFECTED
INVOLVED
MONITOR_ONLY
NOT_RELEVANT
```

Example:

```text
IP Transport        PRIMARY
Mobile Core         CONTRIBUTING
RAN                 AFFECTED
IMS / VoLTE         AFFECTED
Roaming             NOT_RELEVANT
Charging            MONITOR_ONLY
OSS / BSS           CONTRIBUTING
```

---

# 27. Authoritative InvestigationRun

Use one backend object as the source of truth.

Recommended:

```json
{
  "run_id": "RUN-20260913-001",
  "source_mode": "LIVE",
  "source": {},
  "stage": "HYPOTHESIS_TESTING",
  "revision": 184,
  "sequence": 392,

  "evidence": [],
  "reasoning_pathways": [],
  "connections": [],
  "hypotheses": [],
  "knowledge_gaps": [],
  "tests": [],
  "next_best_evidence": [],
  "synthesis": {},
  "validation": {},
  "learning": {},
  "domain_attribution": {},
  "reasoning_focus": {}
}
```

Every visible state derives from this object.

---

# 28. Evidence Object

Example:

```json
{
  "id": "EVT-102",
  "display_name": "BGP Adjacency Flapping on IP/MPLS Edge Router-07",
  "type": "ALARM",
  "source_entity": "IP/MPLS Edge Router-07",
  "timestamp": "2026-09-13T08:22:14+04:00",
  "status": "ACTIVE"
}
```

UI shows `display_name`.

ID remains internal.

---

# 29. Reasoning Pathway Object

Example:

```json
{
  "id": "PATH-SERVICE-DEPENDENCY",
  "display_name": "Service Dependency",
  "status": "ACTIVE",
  "activation_reason": "Enterprise APN traffic traverses IP/MPLS Edge Router-07",
  "evidence_ids": ["EVT-102", "EVT-109"],
  "hypothesis_ids": ["HYP-001"]
}
```

UI shows:

```text
Service Dependency
```

---

# 30. Hypothesis Object

Example:

```json
{
  "id": "HYP-001",
  "display_id": "H1",
  "display_name": "IP/MPLS Edge Router-07 Failure",
  "status": "TESTING",
  "confidence": 0.68,
  "supporting_evidence": ["EVT-102", "EVT-109"],
  "contradictions": [],
  "missing_evidence": ["GAP-018"]
}
```

UI shows:

```text
H1 — IP/MPLS Edge Router-07 Failure
```

---

# 31. Knowledge Gap Object

Example:

```json
{
  "id": "GAP-018",
  "display_name": "Redundant MPLS Path Health Unknown",
  "status": "OPEN",
  "affected_hypotheses": ["HYP-001"],
  "affected_pathways": ["PATH-RESILIENCE-FAILOVER"],
  "required_evidence": "Backup path telemetry"
}
```

UI shows exact gap text.

---

# 32. Validation Object

Example:

```json
{
  "id": "VAL-003",
  "display_name": "Transport Engineer Confirmed Router-07 as Primary Cause",
  "status": "ACCEPTED",
  "reviewer_role": "Transport Engineer"
}
```

UI shows the validated fact, not the ID.

---

# 33. Domain Attribution Object

Example:

```json
{
  "id": "ATTR-001",
  "primary_domain": {
    "display_name": "IP Transport",
    "role": "PRIMARY"
  },
  "other_domains": [
    {
      "display_name": "Mobile Core",
      "role": "CONTRIBUTING"
    },
    {
      "display_name": "RAN",
      "role": "AFFECTED"
    }
  ]
}
```

UI renders exact domain names.

---

# 34. Connection Object

Every visible neural cross-connection must have a backend relation.

Example:

```json
{
  "id": "CONN-188",
  "source_id": "EVT-102",
  "target_id": "PATH-SERVICE-DEPENDENCY",
  "relation_type": "CONTRIBUTES_TO",
  "state": "ACTIVE",
  "reason": "Affected Enterprise APN depends on the router path",
  "sequence": 188
}
```

No visual edge should exist without an authoritative relation.

---

# 35. Backend Workflow Ownership

Use one managed reasoning worker per run.

The worker owns:

```text
evidence admission
correlation
reasoning pathway activation
hypothesis generation
testing
falsification
knowledge-gap detection
next-best evidence
retesting
intelligence synthesis
validation state
domain attribution
learning eligibility
```

Frontend subscribers are read-only observers.

---

# 36. Snapshot + Live Events

Initial load:

```text
GET /api/v1/fikracore/runs/{run_id}/snapshot
```

Live updates:

```text
SSE /api/v1/fikracore/runs/{run_id}/events
```

or WebSocket if already used.

Recommended event types:

```text
evidence_added
connection_activated
pathway_discovered
pathway_activated
pathway_resolved
hypothesis_created
hypothesis_updated
confidence_changed
gap_detected
evidence_requested
evidence_received
hypothesis_retested
synthesis_updated
validation_requested
validation_completed
domain_attribution_updated
learning_candidate_created
reasoning_focus_changed
```

---

# 37. Revision / Sequence Safety

Every event must carry:

```text
run_id
scenario_id or intent_id
revision
sequence
timestamp
```

Frontend must:

```text
reject wrong run
reject stale revision
reject duplicate sequence
apply newer revision atomically
```

All Step 5 surfaces must show the same revision.

---

# 38. Atomic UI Synchronization

When one backend update is accepted, update atomically:

```text
Neural Reasoning Map
Parallel Hypothesis Board
Simulation Journey
What FikraCore Is Doing
Service Impact
Knowledge Gaps
Next Best Evidence
Learning
Zaki
Domain Attribution
```

No panel may lag behind the reasoning map.

---

# 39. Animation Contract

Animation happens only after authoritative state is accepted.

Correct:

```text
Backend reasons
→ persists state
→ emits event
→ frontend validates revision
→ store updates
→ visual pulse animates
```

Incorrect:

```text
UI animates
→ frontend infers conclusion
→ backend catches up
```

Backend always leads.

---

# 40. Current Reasoning Focus

Expose authoritative focus.

Example:

```json
{
  "entity": "IP/MPLS Edge Router-07",
  "pathway": "Resilience & Failover",
  "hypothesis": "H1 — IP/MPLS Edge Router-07 Failure",
  "test": "Check redundant path state",
  "reason": "Backup-path behavior could confirm or weaken H1"
}
```

The map can use a subtle moving halo around the active reasoning branch.

---

# 41. Zaki Integration

Zaki consumes the same authoritative run state.

Zaki must be able to answer:

```text
Why is this pathway active?
Why did H1 increase?
Which evidence contradicts H2?
What gap is blocking validation?
What evidence is needed next?
Why is IP Transport being attributed as primary?
What would change the conclusion?
```

Zaki explains backend state.

Zaki never invents state.

---

# 42. Acceptance Scenario

Use:

```text
H4-WI-001
MPLS Edge Router Failure
```

Expected visual progression:

```text
1. Offline Scenario selected.
2. First synthetic alarm admitted.
3. Evidence streams appear.
4. Operational Evidence pathway activates.
5. Service Dependency pathway activates.
6. Traffic & Capacity pathway activates.
7. H1–H4 candidate hypotheses appear.
8. H1 strengthens from admitted evidence.
9. H2 weakens.
10. H3 receives contradiction and fades.
11. Resilience & Failover pathway becomes relevant.
12. Redundant MPLS Path Health Unknown appears as a knowledge gap.
13. Next-best evidence becomes available.
14. Operator requests evidence.
15. Returned telemetry appears as new evidence.
16. H1 retests and strengthens.
17. Intelligence Synthesis becomes Strongly Supported / Root Candidate.
18. Transport Engineer validation starts.
19. Validation confirms or modifies the result.
20. Domain Attribution appears at the far right.
21. IP Transport becomes PRIMARY only after evidence supports attribution.
22. Learning candidate becomes eligible.
```

---

# 43. Cross-Scenario Validation

After the MPLS acceptance scenario, test a very different scenario:

```text
VoLTE call setup degradation
```

Expected active pathways may include:

```text
Operational Evidence
Subscriber Journey
Control & Signaling
Service Dependency
Change & Configuration
Historical Pattern
Knowledge Gap
```

Do not hardcode pathway activation by scenario.

If the same UI architecture works correctly, the Neural Reasoning Map is reusable.

---

# 44. Frontend Implementation Requirements

Use the existing Step 5 frontend stack.

The Neural Reasoning Map may use the existing graph library if already installed.

Requirements:

```text
stable node positions
deterministic layout
smooth curved neural conduits
limited edge crossings
progressive disclosure
click-to-explain
reduced-motion support
selection synchronization
responsive sizing
```

Do not rebuild the shell.

---

# 45. Performance Rules

Render only:

```text
active evidence
active pathways
active hypotheses
material gaps
current synthesis relationships
validation state
domain attribution
```

Do not render every possible capability relation at full opacity.

Use:

```text
faint dormant relations
bright active relations
dim rejected relations
```

Limit concurrent moving pulses.

---

# 46. Hidden Truth Isolation

Simulator Hidden Truth must never be exposed to:

```text
Evidence
Reasoning Pathways
Hypotheses
Knowledge Gaps
Intelligence Synthesis
Validation
Domain Attribution
Learning
Zaki
```

Hidden Truth remains evaluator-only.

---

# 47. Required Backend Tests

Add:

```text
test_live_intent_and_scenario_share_same_reasoning_pipeline
test_pathway_activation_is_evidence_driven
test_visible_connection_has_authoritative_relation
test_hypothesis_confidence_backend_owned
test_gap_uses_human_readable_display_name
test_validation_exposes_validated_fact
test_domain_attribution_occurs_after_synthesis
test_domain_attribution_uses_exact_domain_name
test_operator_requested_evidence_triggers_retest
test_multiple_subscribers_do_not_advance_run
test_revision_ordering
test_hidden_truth_isolation
```

---

# 48. Required Frontend Tests

Add:

```text
test_existing_step5_shell_preserved
test_neural_reasoning_map_replaces_old_center_only
test_human_readable_evidence_names
test_human_readable_pathway_names
test_h1_h4_visible_identifiers
test_exact_gap_names
test_exact_validation_fact
test_exact_domain_names
test_active_connections_light_from_backend_state
test_dormant_connections_remain_faint
test_connection_click_explains_reason
test_atomic_panel_synchronization
test_stale_update_rejected
test_reduced_motion
test_no_hydration_errors
```

---

# 49. Definition of Done

The Step 5 upgrade is complete when:

```text
[ ] existing Step 5 shell is preserved
[ ] current central graph/status view is replaced with Neural Reasoning Map
[ ] Live uses Intent Violation as entry source
[ ] Offline Simulation uses Selected Scenario as entry source
[ ] both modes share the same reasoning pipeline
[ ] evidence nodes use exact operational names
[ ] reasoning pathways use exact human-readable names
[ ] hypotheses use H1–H4 plus exact titles
[ ] knowledge gaps show exact missing-context descriptions
[ ] validation shows exact validated fact
[ ] domain attribution appears only at the end
[ ] domain attribution uses exact domain names
[ ] cross-connections are backend-authoritative
[ ] active relations illuminate dynamically
[ ] neural conduit geometry is clear and stable
[ ] no random decorative links exist
[ ] intelligence synthesis is central
[ ] no separate oversized Operational Conclusion node is required
[ ] validation remains separate from synthesis
[ ] learning remains stage-gated
[ ] Zaki uses the same revision
[ ] Hidden Truth remains isolated
[ ] no H1–H4 reasoning logic is rewritten unnecessarily
```

---

# Final Product Principle

> **Step 5 remains the product shell and validated reasoning experience. The Neural Reasoning Map becomes its central live explanation surface.**

> **Every visible glow, node, pathway, hypothesis change, knowledge gap, validation state, and domain attribution must correspond to real backend reasoning state.**

> **The goal is not to create another AI dashboard. The goal is to make FikraCore's running investigation understandable while it is happening.**
