# Hyper Canvas: Live Hypothesis Competition — Revised Implementation Plan

## Summary

Upgrade the existing FikraCore Step 5 investigation experience by replacing the central multi-column status view with one stable, interactive **Hyper Canvas** where competing explanations emerge, gain or lose support, and remain inspectable throughout the investigation.

Preserve the existing:

```text
header
navigation
live simulation journey
event stream
right-side hypothesis board
cockpit panels
Learning
Zaki
Simulator controls
```

Update their shared data bindings only where needed so all visible surfaces remain synchronized to the same authoritative scenario/run reasoning state.

Confirmed choices:

```text
shared topology
canvas plus backend state changes
operator-triggered evidence requests
restart replay without timeline scrubbing
backend-authoritative reasoning state
```

Core product principle:

> **Hyper Canvas must visualize the competition between explanations, the reduction of uncertainty, and the emergence of a root cause over time.**

---

# 1. Canvas Experience

## 1.1 Dedicated Hyper Canvas Component

Extract Hyper Canvas into a dedicated component.

Use the installed:

```text
react-force-graph-2d
d3-force
```

Load client-side with a stable hydration placeholder.

The graph must not be a generic network-wide topology view.

It must render only the **investigation-relevant subgraph** derived from:

```text
current evidence
correlated event neighborhood
active hypothesis paths
current reasoning focus
unknown frontier
impact dependencies
```

Do not render the entire telecombrain.

---

## 1.2 Stable Entity Identity and Layout

Every rendered entity must use a stable canonical entity ID.

Keep:

```text
entity_id
display_name
canonical_id
domain
entity_type
health_state
reasoning_role
knowledge_state
```

Graph layout rules:

```text
settle once
pin existing nodes after stabilization
retain existing positions across state revisions
place new nodes near related neighbors
never globally re-layout the graph because new evidence arrived
```

Persist positions either:

```text
in authoritative run state
OR
in a stable per-run layout cache
```

The user must never lose visual orientation while reasoning progresses.

---

## 1.3 Shared Topology, Multiple Hypotheses

All active hypotheses must use the same shared topology.

Do not render separate graphs per hypothesis.

Each hypothesis overlays its own candidate path on the same graph.

Overlapping routes should remain distinguishable using:

```text
offset edges
path labels
path emphasis
opacity hierarchy
selection focus
```

All active candidate paths are visible together by default.

---

## 1.4 Path Semantics

Do not use one visual style for every path.

Use explicit path roles.

Recommended:

```text
Candidate Causal Path
= amber dashed

Leading Causal Path
= emphasized amber solid

Confirmed Causal Path
= green solid

Observed Impact Propagation
= red

Rejected Path
= grey / faded

Unknown Frontier
= amber dotted boundary

Evidence Request
= white pulse

Knowledge / Reasoning Lookup
= purple pulse
```

Causal reasoning and downstream impact propagation must remain visually distinct.

---

## 1.5 Hypothesis Selection

Selecting a hypothesis from either:

```text
Hyper Canvas
Parallel Hypothesis Board
```

must:

```text
highlight the selected candidate path
highlight supporting observations
highlight contradictory observations
show unresolved frontier
show missing evidence
dim unrelated hypotheses
retain rejected hypotheses as selectable
```

Clicking the canvas background clears focus.

Selection state must remain synchronized with the board, Zaki context, and inspector.

---

## 1.6 Real Transition Animation

Animate only meaningful state transitions.

Examples:

```text
evidence arrives at source
support pulse reaches hypothesis path
contradiction pulse reaches hypothesis path
confidence changes
candidate path strengthens
candidate path weakens
path becomes rejected
unknown frontier changes
root candidate is promoted
```

Pause mode and reduced-motion preferences must suppress animation without hiding state.

Avoid decorative continuous motion.

---

## 1.7 Lenses

Keep the existing lens controls.

Recommended lenses:

```text
Network
Evidence
Correlation
Hypotheses
Impact
Knowledge Gaps
```

These lenses must change overlays on the same graph without repositioning the topology.

### Network

```text
topology
health
service flow
```

### Evidence

```text
source observations
evidence associations
event clusters
```

### Correlation

```text
correlated groups
shared dependencies
noise suppression
```

### Hypotheses

```text
candidate paths
confidence state
support
contradiction
rejection
```

### Impact

```text
service impact
customer impact
blast radius
```

### Knowledge Gaps

```text
unknown frontier
missing evidence
missing topology
candidate relationships
model insufficiency
```

---

## 1.8 Density Modes

Keep:

```text
Executive
Engineer
```

### Executive

Emphasize:

```text
top 2 hypotheses
service/customer impact
search-space reduction
leading explanation
recommended next step
```

### Engineer

Expose:

```text
all candidate paths
all evidence associations
reasoning provenance
frontier details
confidence history
```

Both modes must consume the same backend state.

---

## 1.9 Replace Internal Columns

Replace the old internal multi-column status blocks with:

```text
compact search-space strip
current reasoning focus
selection inspector
confidence history
evidence reasons
frontier details
```

Provide:

```text
zoom
fit
focus
reset focus
```

using Lucide icons and tooltips.

Preserve surrounding panel placement.

Allow central vertical growth and page scrolling where needed.

On narrow screens, move the inspector below the graph as a full-width panel.

---

# 2. Search-Space Reduction

Make uncertainty reduction visible.

Example:

```text
24 events
→ 12 correlated signals
→ 8 relevant entities
→ 4 hypotheses
→ 2 plausible causes
→ 1 root candidate
```

Expose backend-derived counts only.

Never fabricate counts in the browser.

The user should always be able to answer:

> **How much uncertainty has FikraCore removed so far?**

---

# 3. Explicit Unknown Frontier Types

Do not represent every unknown as a generic question mark.

Use explicit frontier categories:

```text
MISSING_EVIDENCE
MISSING_TOPOLOGY
CANDIDATE_RELATIONSHIP
MODEL_INSUFFICIENT
UNRESOLVED_DEPENDENCY
```

Each frontier object should identify:

```text
frontier_id
type
entity_ids
hypothesis_ids
description
severity
resolvable
required_evidence
```

This prevents missing telemetry from being confused with missing topology or model insufficiency.

---

# 4. Authoritative Simulation State

Extend existing snapshot and SSE contracts additively with:

```text
operational topology edges
evidence clusters
per-hypothesis candidate paths
evidence associations
confidence history
reasoning focus
frontier references
search-space state
```

Preserve existing routes and existing fields.

Missing new fields must render unavailable state.

Never fabricate fallback paths, confidence trails, evidence counts, or root causes in the browser.

---

# 5. Explicit Hypothesis Contract

Recommended hypothesis object:

```json
{
  "hypothesis_id": "H1",
  "label": "MPLS Edge Router Failure",
  "status": "TESTING",
  "confidence": 0.61,
  "confidence_state": "RANKED",
  "support_count": 4,
  "contradiction_count": 1,
  "missing_evidence_count": 2,
  "path_entity_ids": [],
  "path_edge_ids": [],
  "frontier_ids": [],
  "last_delta": 0.14,
  "last_delta_reason": "Interface loss precedes service degradation"
}
```

Supported status examples:

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

Unknown confidence must render:

```text
Unranked
```

not:

```text
0%
```

---

# 6. Confidence Semantics

Confidence must not be treated as a probability distribution.

Hypotheses do not need to sum to 100%.

Define confidence as:

> **The current degree of evidential support for a hypothesis based on temporal precedence, topology consistency, blast-radius fit, telemetry evidence, change relevance, historical precedent, contradictions, negative evidence, and unresolved gaps.**

Every confidence transition must record:

```text
previous value
new value
delta
reason
evidence IDs
sequence
timestamp
```

Example:

```json
{
  "hypothesis_id": "H1",
  "previous": 0.47,
  "new": 0.61,
  "delta": 0.14,
  "reason": "Interface loss precedes downstream service degradation",
  "evidence_ids": ["EVT-32", "EVT-37"],
  "sequence": 104
}
```

Replace:

```text
browser-generated confidence history
estimated correlation counts
fixed competing zeros
stage-only conclusions
```

with backend-derived values.

---

# 7. Reasoning Focus

Current investigation focus must be authoritative, not frontend-derived.

Recommended object:

```json
{
  "entity_id": "RTR-07",
  "hypothesis_id": "H1",
  "test_id": "TEST-44",
  "stage": "HYPOTHESIS_TESTING",
  "reason": "Checking interface-loss precedence and redundant path state"
}
```

The Hyper Canvas may use this to highlight the current focal entity or path.

Zaki must receive the same focus state.

---

# 8. Deterministic Operational Reasoning

Use deterministic simulator evidence and test rules stored separately from evaluator Hidden Truth.

Rules may consume only observations already admitted to the run.

They must never read simulator truth directly.

Acceptance scenario should include four plausible candidate explanations.

Other scenarios must expose only candidates supported by their available evidence and topology.

---

# 9. Automatic Processing and Operator Evidence Gates

Process available observations automatically through:

```text
correlation
candidate generation
testing
falsification
confidence updates
```

When required evidence is unavailable:

```text
block progression
surface knowledge gap
generate next-best-evidence request
```

The operator triggers evidence collection through existing controls.

Returned evidence must then:

```text
enter the event stream as a new source observation
update the authoritative snapshot
trigger retesting
revise confidence
resolve or retain gaps
```

---

# 10. Stage Eligibility

Advance stages only when actual exit conditions hold.

Do not advance because:

```text
time elapsed
button clicked
animation completed
subscriber connected
```

Learning and recommendations stay gated until required retesting and validation finish.

Confirmation requires a completed supporting test and validation decision.

---

# 11. Managed Worker Per Run

Move progression logic out of SSE subscriptions.

Use exactly one managed worker/state machine per run.

SSE subscribers must only observe.

Multiple tabs or multiple subscribers must never:

```text
accelerate evidence delivery
advance a stage twice
duplicate a confidence transition
execute an action twice
```

Playback speed may control event delivery cadence only.

It must not change stage eligibility or reasoning outcome.

---

# 12. Action Execution

Action execution must be:

```text
idempotent
availability-checked
scenario/run scoped
revision aware
```

Reject unavailable actions.

Failed requests must retain an actionable error state.

A failed request must never mark:

```text
evidence completed
test completed
action executed
```

---

# 13. Atomic Synchronization

Apply each authoritative update atomically so these surfaces always represent the same revision:

```text
Hyper Canvas
Parallel Hypothesis Board
Journey Stepper
Impact Panel
Knowledge Gaps
Next Best Evidence
What FikraCore Is Doing
Learning
Zaki
```

Honor explicit `null` values to clear obsolete state.

Do not retain stale blocking messages because a field became null.

---

# 14. Scenario / Run Protection

Reject:

```text
stale scenario responses
stale run responses
duplicate transitions
out-of-order revisions
duplicate evidence events
```

Every live message must include:

```text
scenario_id
run_id
revision
sequence
```

The frontend must reject updates that do not belong to the active run.

---

# 15. Reconnect Behavior

On reconnect:

```text
load authoritative snapshot
restore current graph state
restore current hypothesis state
restore current frontier
restore current impact state
restore current focus
```

Do not replay historical animations automatically.

Historical animation belongs to Replay mode, not reconnect.

---

# 16. Restart Replay

Restart Replay must clear:

```text
observations
correlations
tests
actions
confidence histories
pending work
knowledge gaps
frontiers
selections
learning state
recommendations
```

Preserve monotonic revision semantics.

Replay must reproduce:

```text
same scenario definition
same deterministic evidence schedule
same correlation outcomes
same hypothesis candidates
same test outcomes
same confidence trajectory
same operator evidence gate
```

Only values such as:

```text
run_id
wall-clock timestamps
```

may differ.

Timeline seeking remains deferred.

---

# 17. Frontend Must Never Become the Reasoning Engine

Add an explicit architectural rule:

> **The frontend must never infer causality, create missing graph edges, compute hypothesis confidence, promote a root candidate, infer impact certainty, or generate knowledge gaps independently.**

The frontend only renders authoritative backend reasoning state.

Client-side logic may handle:

```text
layout
selection
focus
animation
filtering
density
lens overlays
```

but not reasoning.

---

# 18. Validation Before Learning and Recommendation

Use the following sequence:

```text
quiet network
→ observations
→ correlation
→ candidate hypotheses
→ hypothesis testing
→ weakening/rejection
→ unknown frontier
→ operator evidence request
→ returned evidence
→ retest
→ root candidate
→ validation
→ confirmed cause
→ learning eligibility
→ recommendation
```

Do not jump from:

```text
root candidate
```

directly to:

```text
learning
recommendation
```

without validation.

---

# 19. Root-Cause Localization

Root cause must emerge progressively.

Example:

```text
18 possible entities
→ 7 correlated
→ 4 candidate causes
→ 2 plausible upstream causes
→ 1 root candidate
```

When the root candidate changes, emit an authoritative event.

Recommended:

```text
root_candidate_changed
```

The final confirmed cause should only appear after validation.

---

# 20. Impact State

Keep impact separate from RCA.

Impact certainty states:

```text
UNKNOWN
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Do not preload final impact from Hidden Truth.

The graph must visually distinguish:

```text
upstream causal reasoning
```

from:

```text
downstream service/customer propagation
```

---

# 21. Learning State

Learning remains stage-gated.

Before validation:

```text
No validated learning yet
```

After validation candidate creation:

```text
Candidate learning
Awaiting governance / SME decision
```

After acceptance:

```text
Validated knowledge
Eligible for promotion
```

Learning must never consume Hidden Truth directly.

---

# 22. Zaki Synchronization

Zaki must consume the same authoritative revision as the rest of the investigation.

Zaki context should include:

```text
scenario_id
run_id
stage
revision
selected_hypothesis
selected_entity
reasoning_focus
evidence state
impact state
knowledge gaps
next-best evidence
```

Zaki may:

```text
explain
summarize
compare
orchestrate approved actions
```

Zaki must never:

```text
invent confidence
invent topology
invent root cause
invent blast radius
invent validated learning
```

---

# 23. Compatibility

Preserve existing:

```text
routes
navigation
scenario controls
run controls
event stream
hypothesis board
impact panel
knowledge gap panel
NBE controls
Learning
Zaki
```

Add typed fields to the existing simulation store/context.

Missing new fields render:

```text
Unavailable
Not yet generated
Unknown
Unranked
```

rather than fabricated fallback state.

---

# 24. Hydration and Initial Rendering

Keep server and first client render deterministic.

Do not use:

```text
current timestamps
client-only store state
random graph seeds
browser-specific measurements
```

to alter the initial shell structure.

Use a stable canvas placeholder until client-side graph initialization completes.

No hydration warnings are acceptable.

---

# 25. Performance and Visual Stability

Use:

```text
investigation-relevant subgraph only
stable pinned positions
incremental node insertion
virtualized event list
bounded active animations
opacity reduction for weak hypotheses
semantic zoom
```

Avoid:

```text
global force re-layout on every event
rendering the entire telecombrain
continuous decorative animation
large numbers of permanently animated particles
```

---

# 26. Verification — Backend

Backend tests must cover:

```text
competing confidence trajectories
confidence reasons resolve to real evidence IDs
candidate-path growth
contradiction
hypothesis weakening
hypothesis rejection
blocked evidence collection
returned-evidence retesting
delayed root confirmation
validation before confirmed cause
learning after validation only
recommendation after validation only
failed action handling
duplicate action idempotency
pause/resume
clean replay
two simultaneous SSE subscribers
stale revision rejection
Hidden Truth isolation
```

---

# 27. Verification — Frontend

Frontend tests must cover:

```text
atomic revision application
stale-response rejection
out-of-order sequence rejection
explicit null clearing
selection synchronization
board/canvas focus synchronization
rejected-path inspection
unranked confidence rendering
unknown-frontier rendering
removal of fabricated history
stable graph positions across revisions
reduced-motion behavior
reconnect without historical animation replay
```

---

# 28. Browser Acceptance Flow

Use the existing acceptance scenario.

Expected visual sequence:

```text
quiet network
→ first observations
→ evidence clusters
→ relevant investigation subgraph
→ four candidate paths
→ hypotheses initially unranked
→ testing begins
→ one hypothesis strengthens
→ another weakens
→ one is rejected but remains inspectable
→ unknown frontier appears
→ next-best-evidence request becomes available
→ operator requests evidence
→ returned observation arrives
→ hypothesis retest
→ confidence revision
→ search space narrows
→ root candidate emerges
→ validation
→ confirmed cause
→ learning becomes eligible
→ recommendation appears
```

---

# 29. Screenshot / Visual Verification

Capture:

```text
desktop
tablet if supported
mobile/narrow viewport
```

Verify:

```text
graph is nonblank
labels are readable
layout remains stable
hypothesis routes are distinguishable
unknown frontier is visible
rejected paths remain inspectable
controls work
reduced motion works
no hydration errors
no panel overlap
inspector moves below graph on narrow screens
```

---

# 30. Tooling / Repository Validation

Run:

```text
focused backend tests
frontend tests
TypeScript checks
lint checks if configured
```

Then update the repository graph:

```text
graphify update .
```

---

# 31. Deferred Scope

Do not add in this iteration:

```text
timeline scrubbing / arbitrary seek
new What-If behavior
full workspace redesign
new global topology browser
new learning engine
new confidence algorithm outside existing reasoning rules
```

Keep this iteration focused on:

```text
live hypothesis competition
authoritative backend state
progressive uncertainty reduction
stable shared canvas
```

---

# 32. Definition of Done

The Hyper Canvas upgrade is complete when:

```text
[ ] the old central multi-column status view is replaced by one stable shared graph
[ ] only investigation-relevant topology is rendered
[ ] existing node positions remain stable as evidence arrives
[ ] multiple hypotheses coexist on the same graph
[ ] candidate, leading, confirmed, impact, rejected, and frontier paths are visually distinct
[ ] unknown confidence renders as unranked
[ ] confidence history is backend-authoritative
[ ] every confidence transition has a reason and evidence IDs
[ ] unknown frontiers have explicit types
[ ] current reasoning focus is backend-authoritative
[ ] evidence requests are operator-triggered
[ ] returned evidence triggers retesting
[ ] stage advancement is evidence-driven
[ ] one managed worker owns each run
[ ] multiple SSE subscribers cannot accelerate progression
[ ] all surfaces apply the same authoritative revision atomically
[ ] reconnect restores current state without replaying old animation
[ ] replay reproduces the same deterministic investigation
[ ] validation occurs before confirmed cause
[ ] validation occurs before learning and recommendation
[ ] frontend never performs causal reasoning
[ ] Hidden Truth remains isolated
[ ] existing shell/navigation/Zaki/Learning are preserved
```

---

# Final Product Principle

> **Hyper Canvas is not a topology viewer. It is the live visual surface of FikraCore's reasoning process.**

> **Multiple explanations compete over the same evidence, uncertainty shrinks, weak explanations are falsified, missing evidence becomes explicit, and the root cause emerges only when the evidence justifies it.**

> **The operator should be able to understand not only what FikraCore currently believes, but why that belief changed.**
