# FikraCore Step 5 UI v2 — Hyper Canvas Upgrade Prompt

## Purpose

Upgrade the existing FikraCore Step 5 simulator UI without replacing the full interface.

The goal is to preserve the current product shell, navigation, scenario/run controls, Zaki, event stream, impact, knowledge gaps, next-best evidence, learning, and benchmark workspaces while replacing the old central causal graph with a new:

> **Hyper Canvas — Real-Time Parallel Hypothesis Testing for RCA**

The new Hyper Canvas becomes the primary intelligence surface of the simulator.

It must show FikraCore progressively reasoning from:

```text
raw signals
→ correlation
→ multiple competing hypotheses
→ evidence-driven confidence changes
→ unknown boundaries
→ next-best evidence
→ root-cause localization
→ validated action
```

The product must feel like:

> **watching FikraCore investigate the network in real time**

not:

> a static topology dashboard with results already known.

---

# 1. Preserve Existing UI Shell

Do not replace the full Step 5 UI.

Keep:

```text
Top Header
Scenario Selector
Run ID / Run Controls
Simulation Status
telecombrain MCP Status
Primary Navigation
Live Simulation Journey
Unified Live Event Stream
What FikraCore Is Doing
Service Impact
Knowledge Gaps
Next-Best Evidence
Learning
Zaki
Simulator Lab
Knowledge Core
Benchmarks
```

Upgrade only the intelligence presentation and synchronization around the center workspace.

---

# 2. Replace the Old Causal Graph

Replace:

```text
Telecom Network Causal Graph
```

with:

```text
Hyper Canvas — Real-Time Parallel Hypothesis Testing for RCA
```

The Hyper Canvas must not be a static graph.

It must combine:

```text
topology
event evidence
event clusters
candidate causal paths
parallel hypotheses
confidence evolution
unknown frontier
next-best-evidence requests
root-cause localization
impact propagation
```

---

# 3. Overall Layout

Keep the existing screen structure.

Recommended:

```text
┌─────────────────────────────────────────────────────────────┐
│ Header / Scenario / Run / MCP / Controls                   │
├─────────────────────────────────────────────────────────────┤
│ Primary Navigation                                          │
├─────────────────────────────────────────────────────────────┤
│ Live Simulation Journey                                     │
├───────────────┬───────────────────────────────┬─────────────┤
│ Raw Event     │ Hyper Canvas                  │ Parallel    │
│ Stream        │                               │ Hypotheses  │
│               │                               │ Board       │
├───────────────┴───────────────────────────────┴─────────────┤
│ What FikraCore Is Doing / Impact / Gaps / Next Evidence    │
├─────────────────────────────────────────────────────────────┤
│ Learning / Zaki                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 4. Five Synchronized Reasoning Layers

The upgraded simulator must synchronize five layers:

```text
1. Evidence Layer
2. Correlation Layer
3. Hypothesis Layer
4. Uncertainty Layer
5. Impact Layer
```

All layers must share:

```text
scenario_id
run_id
simulation_stage
evidence set
reasoning state
```

---

# 5. Evidence Layer

Purpose:

```text
What actually happened?
```

Use the existing Unified Live Event Stream.

Show only source observations:

```text
alarms
KPIs
metrics
logs
traces
changes
tickets
healthy signals
```

Do not mix reasoning outputs into the raw stream.

Good:

```text
DRA-01 NTP offset threshold exceeded
Diameter timeout rate increased
Session failures increased
Change CR-8821 applied
```

Bad:

```text
Common cause detected
Correlated failure identified
Hypothesis created
Root cause selected
```

Those belong to the reasoning layer.

---

# 6. Correlation Layer

Purpose:

```text
Which observations are related?
```

Show:

```text
event clustering
temporal alignment
shared dependency discovery
cross-domain grouping
noise suppression
healthy-peer comparison
```

The Hyper Canvas should visibly move from isolated signals to correlated groups.

Example:

```text
24 events
→ 12 correlated
→ 8 relevant entities
```

---

# 7. Parallel Hypothesis Layer

Purpose:

```text
What could explain the evidence?
```

Several hypotheses must progress in parallel.

Example:

```text
H1 Database Lock Contention
H2 Transport Path Degradation
H3 IMS Failure
H4 Application Overload
```

Each hypothesis must include:

```text
status
confidence
confidence delta
supporting evidence
contradicting evidence
missing evidence
candidate causal path
```

---

# 8. Hypothesis States

Use:

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

Do not immediately show final confidence.

Progression example:

```text
H1 42% → 61% → 78%
H2 31% → 24% → 11%
H3 18% → 9% → REJECTED
H4 9% → 6%
```

---

# 9. Parallel Hypothesis Board

Upgrade the existing right-side hypothesis panel.

Display:

```text
H1 Database Lock        78%  ↑ +12   LEADING
H2 Transport Path       24%  ↓ -10   WEAKENING
H3 IMS Fault             9%  ↓ -11   REJECTED
H4 App Overload          6%  ↓  -4   LOW SUPPORT
```

Each row/card should show:

```text
supports
contradictions
missing evidence
status
confidence history
```

Clicking a hypothesis:

```text
focuses its path on the Hyper Canvas
dims unrelated hypotheses
highlights supporting evidence
highlights contradictory evidence
shows missing evidence
```

---

# 10. Hyper Canvas Real-Time Behavior

The canvas should evolve in this order:

```text
1. Quiet topology / minimal context
2. First signal appears
3. Additional observations arrive
4. Relevant observations cluster
5. Shared dependencies light up
6. Multiple candidate paths emerge
7. Several hypotheses appear in parallel
8. Evidence strengthens / weakens paths
9. Rejected paths fade
10. Unknown frontier appears
11. Next-best-evidence request fires
12. New evidence returns
13. Hypotheses are retested
14. Search space narrows
15. Root candidate emerges
16. Impact propagation becomes clearer
17. Recommendation appears
```

---

# 11. Search-Space Reduction

Show intelligence as shrinking uncertainty.

Example:

```text
24 events
→ 12 correlated signals
→ 8 entities
→ 4 hypotheses
→ 2 plausible causes
→ 1 root candidate
```

Add a small live widget inside the Hyper Canvas:

```text
Search Space
24 → 12 → 8 → 4 → 2 → 1
```

---

# 12. Root-Cause Localization

Do not mark a root cause at run start.

Root cause must emerge gradually.

Example:

```text
18 possible entities
→ 7 correlated
→ 4 candidate causes
→ 2 plausible upstream causes
→ 1 root candidate
```

When a root candidate emerges, show:

```text
entity
confidence
why it became dominant
supporting evidence count
contradiction count
missing evidence
```

---

# 13. Evidence Flow on the Canvas

Evidence should visibly affect hypotheses.

Example:

```text
Alarm EVT-12
      ↓ supports
H1 +9%

Healthy peer check
      ↓ contradicts
H2 -14%

Change CR-8821
      ↓ supports
H1 +17%
```

Use animated evidence pulses to show why confidence changed.

---

# 14. Confidence Evolution

Do not use only a static confidence bar.

Show progression:

```text
41%
↓ temporal evidence
58%
↓ shared dependency
71%
↓ healthy peer contradiction
64%
↓ requested evidence
82%
```

Every significant confidence change must include:

```text
previous confidence
new confidence
delta
reason
evidence IDs
```

---

# 15. Uncertainty Layer

Purpose:

```text
What does FikraCore still not know?
```

Show:

```text
unknown boundaries
missing topology
missing evidence
contradictions
candidate relationships
model insufficiency
next-best evidence
```

Do not use only a generic question-mark node.

---

# 16. Unknown Frontier

Show an explicit investigation boundary.

Example:

```text
Known Investigation Region
        ↓
Current Frontier
        ↓
Unknown Dependency / Missing Evidence
```

The frontier should move as evidence arrives.

---

# 17. Next-Best Evidence

Keep the existing Next Best Evidence panel, but synchronize it with the Hyper Canvas.

Each evidence request must show:

```text
what is requested
which hypothesis it tests
why it matters
expected information gain
status
```

Example:

```text
Request:
DB lock-owner transaction trace

Tests:
H1 Database Lock Contention

Why:
Confirms whether the schema migration created the blocking transaction

Information Gain:
High
```

---

# 18. Visible Retest Loop

If evidence is missing:

```text
H1 TESTING
   ↓
NEEDS_MORE_EVIDENCE
   ↓
REQUEST EVIDENCE
   ↓
NEW EVIDENCE ARRIVES
   ↓
H1 RETEST
   ↓
CONFIDENCE CHANGES
```

Do not advance to learning while this loop remains unresolved.

---

# 19. Impact Layer

Keep the existing Service Impact panel but add epistemic certainty.

Use:

```text
UNKNOWN
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Example:

```text
OBSERVED
Session failures detected
```

then:

```text
ESTIMATED
~6,000 users potentially affected
```

then:

```text
CONFIRMED
6,120 affected sessions
```

Do not preload final impact from Hidden Truth.

---

# 20. Distinguish RCA from Impact Propagation

The Hyper Canvas must visually distinguish:

```text
upstream reasoning
= what caused the incident?
```

from:

```text
downstream impact
= what did the incident affect?
```

Do not use the same path styling for both.

---

# 21. Semantic Animation Language

Use animation only when meaningful.

Recommended semantics:

```text
cyan flow
= normal network/service flow

red pulse
= observed degradation propagation

amber dashed edge
= candidate / uncertain dependency

white pulse
= evidence request / active test

purple pulse
= FikraCore knowledge lookup / reasoning

green lock
= validated conclusion

grey fade
= falsified path
```

Avoid decorative motion.

---

# 22. Reasoning Focus

Show where FikraCore is currently investigating.

Example:

```text
Database-05
INVESTIGATING

Checking:
Lock ownership

Evidence:
3 / 4 available
```

The focus should move as the reasoning engine evaluates hypotheses.

---

# 23. Hyper Canvas Lenses

Add tabs/toggles:

```text
Network
Evidence
Hypotheses
Impact
Knowledge Gaps
```

Same graph, different overlay.

## Network

```text
topology
health
service flow
```

## Evidence

```text
event sources
event clusters
evidence movement
```

## Hypotheses

```text
parallel paths
confidence
rejections
supports / contradictions
```

## Impact

```text
service degradation
customer impact
blast radius
```

## Knowledge Gaps

```text
unknown frontier
missing evidence
candidate relationships
```

---

# 24. Semantic Zoom

Do not render the full telecombrain.

Use:

```text
Level 1 — Domains
Level 2 — Services
Level 3 — Service Chains
Level 4 — Network Functions
Level 5 — Nodes / Routers / Clusters
Level 6 — Interfaces / Pods / Protocols
```

Auto-focus on the active investigation neighborhood.

---

# 25. Keep "What FikraCore Is Doing"

Preserve the current panel but make it exact.

Good:

```text
Grouping 7 events inside a 2-minute window
Comparing SGW-01 with unaffected SGW-02
Testing whether DB lock precedes subscriber failures
Checking shared dependencies
Requesting lock-owner transaction trace
```

Avoid:

```text
Analyzing...
Processing...
Busy...
```

---

# 26. Add a Compact Explanation Block

Add:

```text
WHAT CHANGED?
WHY DOES IT MATTER?
WHAT IS STILL UNKNOWN?
WHAT HAPPENS NEXT?
```

Example:

```text
What changed?
A database lock increase occurred before subscriber failures.

Why does it matter?
It explains timing better than the transport hypothesis.

Still unknown?
The lock-owner transaction has not been identified.

Next?
Request database lock-owner trace and retest H1.
```

---

# 27. Reasoning Trace

Keep raw event stream separate from reasoning.

Add a trace drawer accessible from:

```text
View Trace
```

or by clicking a journey stage.

Trace modes:

```text
Summary
Verbose
Technical
```

---

# 28. Trace Event Examples

```text
CORRELATION
Grouped 5 events across Transport and Mobile Core

HYPOTHESIS
Created H1: Database lock contention

TEST
Temporal precedence supports H1

FALSIFICATION
H2 weakened by healthy transport peer

KNOWLEDGE GAP
Database lock owner unavailable

NEXT BEST EVIDENCE
Fetch lock-owner transaction trace
```

---

# 29. Existing Zaki — Keep and Upgrade

Do not replace Zaki.

Zaki must use the same:

```text
scenario
run
workspace
stage
selected hypothesis
selected entity
knowledge gap
evidence state
```

Zaki should explain:

```text
what changed
why it changed
what remains unknown
what is being tested next
```

---

# 30. Existing Learning — Keep but Stage-Gate

Do not remove Learning.

Before validation:

```text
No validated learning yet
```

After candidate extraction:

```text
Candidate learning
Awaiting SME validation
```

After acceptance:

```text
Validated knowledge
Eligible for promotion
```

---

# 31. Existing Simulator Journey — Keep

Preserve the journey stepper.

It must stay synchronized with real backend state.

Do not advance because time elapsed.

Stages must advance because exit conditions are satisfied.

---

# 32. Simulation Modes

Keep/support:

```text
Live
Replay
What-If
```

## Live

Show evidence and reasoning as they happen.

## Replay

Scrub through:

```text
event arrival
correlation
hypothesis creation
confidence changes
rejections
evidence requests
root localization
```

## What-If

Switch to forward reasoning:

```text
selected failure/change
→ propagation
→ failover
→ capacity
→ blast radius
→ mitigation comparison
```

---

# 33. Executive vs Engineer View

Do not build a separate product.

Use the same backend state with two display densities.

## Executive

Show:

```text
service impact
customer impact
top 2 hypotheses
confidence trend
search-space reduction
leading cause
recommended action
```

## Engineer

Show:

```text
full Hyper Canvas
all hypotheses
all evidence
reasoning trace
unknown frontier
next-best evidence
technical provenance
```

---

# 34. Backend State Contract

Recommended:

```json
{
  "scenario_id": "H4-WI-035",
  "run_id": "RUN-...",
  "stage": "HYPOTHESIS_TESTING",

  "evidence": [],
  "correlations": [],
  "hypotheses": [],
  "unknowns": [],
  "impact": {},
  "next_best_evidence": [],

  "reasoning_focus": {},

  "root_localization": {},

  "search_space": {
    "events": 24,
    "correlated_events": 12,
    "entities": 8,
    "active_hypotheses": 4,
    "plausible_causes": 2,
    "root_candidates": 1
  }
}
```

---

# 35. Live Message Types

Support:

```text
observation_added
correlation_created
correlation_rejected
hypothesis_created
hypothesis_ranked
hypothesis_test_started
hypothesis_supported
hypothesis_weakened
hypothesis_rejected
confidence_changed
knowledge_gap_detected
next_best_evidence_requested
evidence_received
hypothesis_retest_started
reasoning_focus_changed
root_candidate_changed
impact_observed
impact_estimated
impact_confirmed
validation_started
learning_candidate_created
recommendation_created
```

---

# 36. Scenario / Run Scoping

Every item must belong to:

```text
scenario_id
run_id
```

On scenario/run switch:

```text
clear old visualization
load authoritative snapshot
subscribe to active run
reject stale deltas
```

---

# 37. Hidden Truth Isolation

Never expose Hidden Truth to:

```text
Hyper Canvas
hypothesis ranking
Zaki
trace
impact
learning
recommendations
```

Hidden Truth remains evaluator-only.

---

# 38. Performance / Decluttering

Avoid visual overload.

Use:

```text
relevant subgraph only
semantic zoom
dim low-value hypothesis paths
fade rejected paths
virtualize event list
animate only state transitions
collapse details until selected
```

Keep all existing functions.

Declutter through hierarchy, not feature removal.

---

# 39. Required Tests

Add:

```text
test_existing_step5_shell_preserved
test_old_causal_graph_replaced_by_hyper_canvas
test_raw_event_stream_remains_operational_only
test_multiple_hypotheses_progress_in_parallel
test_candidate_paths_build_in_realtime
test_confidence_changes_have_evidence_reason
test_rejected_paths_remain_inspectable
test_unknown_frontier_visible
test_next_best_evidence_updates_canvas
test_returned_evidence_triggers_retest
test_search_space_reduces_progressively
test_root_candidate_emerges_only_after_testing
test_impact_evolves_separately
test_reasoning_trace_available
test_zaki_uses_same_reasoning_state
test_learning_remains_stage_gated
test_hidden_truth_never_leaks
test_state_is_scenario_run_scoped
```

---

# 40. Acceptance Walkthrough

Use a scenario with at least four plausible causes.

Expected flow:

```text
1. Existing Step 5 shell loads normally.
2. Hyper Canvas replaces the old causal graph.
3. First raw signal appears.
4. More evidence arrives in the existing event stream.
5. Correlation appears on Hyper Canvas.
6. Four hypotheses appear in parallel.
7. Four candidate paths grow.
8. H1 gains evidence and confidence rises.
9. H2 weakens after contradiction.
10. H3 is rejected but remains inspectable.
11. Unknown frontier appears.
12. Next-best evidence is requested.
13. Returned evidence enters the canvas.
14. H1 is retested.
15. Search space shrinks.
16. One root candidate becomes dominant.
17. Service impact becomes clearer.
18. Validation begins.
19. Learning candidate appears.
20. Recommendation appears.
21. Zaki explains the live reasoning state throughout.
```

---

# 41. Definition of Done

The upgrade is complete when:

```text
[ ] existing Step 5 navigation and shell remain intact
[ ] Hyper Canvas replaces only the old causal graph
[ ] multiple hypotheses progress in parallel
[ ] event correlation is visible in real time
[ ] candidate paths are built progressively
[ ] confidence changes are evidence-driven
[ ] rejected paths fade but remain inspectable
[ ] search-space reduction is visible
[ ] unknown frontier is visible
[ ] next-best evidence is integrated
[ ] retesting is visible
[ ] root cause emerges progressively
[ ] impact remains separate from RCA reasoning
[ ] reasoning trace is accessible
[ ] Zaki remains contextual
[ ] Learning remains stage-gated
[ ] Executive/Engineer density options are supported
[ ] no existing core function is removed
[ ] Hidden Truth remains isolated
[ ] all state remains scenario/run scoped
```

---

# Final Product Principle

> **Do not replace the existing FikraCore UI. Upgrade its central intelligence surface.**

> **Hyper Canvas should make the competition between explanations, evidence flow, uncertainty reduction, and root-cause localization visible in real time.**

> **The user should feel they are watching FikraCore investigate, not reading a completed incident report.**
