# FikraCore Step 5 — Simulation Traceability & UI Consistency Fix for Codex

## Objective

Fix two related problems in the FikraCore live simulator:

1. **Simulation tracing is insufficient** — operators and developers cannot inspect the exact backend reasoning pipeline in verbose detail.
2. **UI state is logically inconsistent** — raw network evidence, reasoning outputs, hypothesis state, service impact, stage progression, and learning are being shown at incompatible times or mixed together.

The fix must make the simulator both:

```text
TRACEABLE
and
EPISTEMICALLY CONSISTENT
```

The final simulator should let a user understand:

```text
what raw evidence arrived
what FikraCore did with it
what belief changed
why that belief changed
what remains unknown
what evidence is needed next
when impact is observed vs estimated vs confirmed
when a hypothesis is testing vs waiting for evidence
when validation/learning is actually allowed
```

---

# 1. Core Design Rule

Separate these four state channels:

```text
A. OBSERVABILITY
   alarms / KPIs / metrics / logs / traces / changes / tickets

B. REASONING
   correlation / hypothesis / testing / falsification / confidence changes

C. IMPACT
   observed / estimated / confirmed service and customer impact

D. VALIDATION / LEARNING / ACTION
   validation / knowledge candidate / promotion / recommendation
```

Do not mix them into one generic event stream.

---

# 2. Correct Simulation Lifecycle

Use this logical pipeline:

```text
TRIGGER
   ↓
SIGNAL_FLOOD
   ↓
CORRELATION
   ↓
HYPOTHESIS_GENERATION
   ↓
HYPOTHESIS_TESTING
   ├── SUPPORTED + evidence sufficient
   │       ↓
   │   KNOWLEDGE_GAP_CHECK
   │
   ├── SUPPORTED + evidence missing
   │       ↓
   │   NEXT_BEST_EVIDENCE
   │       ↓
   │   NEW OBSERVATION
   │       ↓
   │   HYPOTHESIS_TESTING
   │
   └── REJECTED
           ↓
       test next hypothesis

after reasoning reaches terminal condition:
   ↓
VALIDATION
   ↓
LEARNING
   ↓
ACTION / RECOMMENDATION
```

The important loop is:

```text
HYPOTHESIS
→ TEST
→ NEEDS_MORE_EVIDENCE
→ NEXT_BEST_EVIDENCE
→ NEW EVIDENCE
→ TEST AGAIN
```

A stage must advance because its exit condition is satisfied, not because time has passed.

---

# 3. Hypothesis State Machine

Implement explicit hypothesis states:

```text
CANDIDATE
UNRANKED
RANKED
TESTING
SUPPORTED
NEEDS_MORE_EVIDENCE
TESTING_NEW_EVIDENCE
CONTRADICTED
REJECTED
ROOT_CANDIDATE
CONFIRMED
```

Do not leave a hypothesis in:

```text
Testing...
```

after the available tests are finished.

If additional evidence is required, transition to:

```text
SUPPORTED
+
NEEDS_MORE_EVIDENCE
```

and make the Next-Best-Evidence process active.

---

# 4. Stage Advancement Rules

## Trigger exits when

```text
at least one valid observation exists
```

## Signal Flood exits when

```text
initial observation window closes
or
minimum evidence set is available
```

## Correlation exits when

```text
event groups are built
shared dependencies are evaluated
candidate relationships are emitted
```

## Hypothesis Generation exits when

```text
one or more candidate explanations exist
```

## Hypothesis Testing exits when

```text
all active candidates are:
SUPPORTED
REJECTED
or NEEDS_MORE_EVIDENCE
```

If `NEEDS_MORE_EVIDENCE` exists:

```text
do not advance directly to Learning
```

Route through:

```text
Knowledge Gap / Next Best Evidence
```

and then back to testing when new evidence arrives.

## Learning / Validation may begin only when

```text
reasoning has reached an eligible terminal state
AND
validation workflow has started
```

---

# 5. Raw Event Stream Must Contain Only Operational Evidence

The **Unified Live Event Stream** should contain only source observations such as:

```text
ALARM
METRIC
KPI
LOG
TRACE
CHANGE
TICKET
HEALTHY_SIGNAL
```

Good examples:

```text
DRA-01 NTP offset threshold exceeded
Diameter timeout rate increased on DRA-01
OCS transaction latency increased
Peer timeout detected
Enterprise session setup failures reported
NTP configuration changed on Clock Source-01
```

Do not show these as raw alarms/events:

```text
Correlated alarms across multiple domains
Common cause failure pattern detected
Shared dependency degradation
Hypothesis H1 created
Root cause candidate selected
```

Those are reasoning outputs.

---

# 6. Separate Reasoning Trace

Create a dedicated:

```text
FikraCore Reasoning Trace
```

This stream should contain internal reasoning events such as:

```text
CORRELATION
Grouped 6 observations inside a 120-second window

INFERENCE
DRA-01 and DRA-02 share NTP-01

HYPOTHESIS
Created candidate: Shared NTP Clock Skew

TEST
Temporal precedence supports HYP-001

FALSIFICATION
DRA software defect weakened by healthy-peer comparison

KNOWLEDGE_GAP
NTP-01 health unavailable

NEXT_BEST_EVIDENCE
Fetch NTP offset history

VALIDATION
SME review started

LEARNING
Candidate knowledge created

ACTION
Recommended NTP source validation
```

---

# 7. Trace Levels

Provide three trace levels.

## Summary

Human-readable reasoning summary:

```text
what changed
why it matters
what remains unknown
what happens next
```

## Verbose

Every reasoning event:

```text
event ingestion
correlation
candidate creation
ranking
evidence tests
confidence changes
knowledge gaps
evidence requests
validation
learning
recommendations
```

## Technical

Include:

```text
canonical IDs
timestamps
component names
raw inputs
raw outputs
provider provenance
scores
sequence numbers
snapshot version
request IDs
latency
```

---

# 8. Trace API

Add or expose:

```text
GET /api/v1/fikracore/simulations/{run_id}/trace
```

Support filters:

```text
?level=summary
?level=verbose
?level=technical

?stage=correlation
?component=hypothesis_engine
?entity=DRA-01
?hypothesis=HYP-001
?type=confidence_update
```

For live trace:

```text
WS /api/v1/fikracore/simulations/{run_id}/trace/live
```

or equivalent SSE if already used by the project.

---

# 9. Trace Record Contract

Use a common envelope:

```json
{
  "timestamp": "2026-09-11T19:42:04.318Z",
  "scenario_id": "H4-WI-016",
  "run_id": "RUN-...",
  "sequence": 145,
  "stage": "HYPOTHESIS_TESTING",
  "component": "hypothesis_engine",
  "event_type": "confidence_update",
  "entity_ids": ["DRA-01"],
  "hypothesis_id": "HYP-001",
  "message": "Clock skew precedes Diameter failures",
  "details": {
    "previous_confidence": 0.58,
    "new_confidence": 0.71
  },
  "provenance": "fikracore_reasoning_engine"
}
```

---

# 10. Every Visible Transition Must Be Traceable

Every material UI change must have a corresponding trace record.

Examples:

```text
graph node becomes root candidate
→ root_candidate_changed trace

confidence 58% → 71%
→ confidence_update trace

knowledge gap appears
→ knowledge_gap_detected trace

stage changes
→ stage_transition trace

next-best evidence starts
→ evidence_request_started trace

learning candidate appears
→ learning_candidate_created trace
```

---

# 11. Simulation Trace UI

Add a compact:

```text
View Trace
```

control near the Live Simulation Journey.

Clicking it should open a trace drawer or full-page console.

Support:

```text
Summary
Verbose
Technical
```

and filters:

```text
Stage
Component
Entity
Hypothesis
Event Type
Time Range
```

---

# 12. Clickable Stage Trace

Each journey stage should be clickable.

Example:

```text
3 Correlation
```

opens trace filtered to:

```text
stage=CORRELATION
```

Show:

```text
inputs received
events grouped
dependencies checked
candidate links created
rejected correlations
duration
output produced
```

---

# 13. Service Impact Must Have Certainty State

Impact can appear before RCA completes, but it must show epistemic status.

Use:

```text
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Example early:

```text
Observed Impact
Customer session failures detected
Scope still being estimated
```

Later:

```text
Estimated Impact
~20,000 sessions potentially affected
```

Later still:

```text
Confirmed Impact
3 regions
~20,000 affected users
```

Do not show precise values without indicating whether they are observed, estimated, or confirmed.

---

# 14. Impact Contract

Example:

```json
{
  "service": "Network Services",
  "impact_state": "ESTIMATED",
  "degradation_pct": 65,
  "affected_users": 20000,
  "confidence": 0.72,
  "evidence_ids": ["EVT-12", "EVT-15"]
}
```

---

# 15. Graph State Must Separate Health from Reasoning

Do not use a single red state to mean both:

```text
unhealthy
and
root cause
```

Use:

```json
{
  "entity_id": "DRA-01",
  "health_state": "DEGRADED",
  "reasoning_role": "OBSERVED",
  "knowledge_state": "KNOWN"
}
```

Later:

```json
{
  "entity_id": "DRA-01",
  "health_state": "DEGRADED",
  "reasoning_role": "ROOT_CANDIDATE",
  "knowledge_state": "INFERRED",
  "confidence": 0.885
}
```

---

# 16. Causal Path State

Use staged path labels:

```text
Candidate Dependency Path
Leading Causal Path
Confirmed Causal Path
```

Do not display:

```text
Confirmed Causal Path
```

before validation supports it.

---

# 17. What FikraCore Is Doing Now

Replace vague tasks such as:

```text
Busy analyzing common cause
Processing
Analyzing
```

with exact actions:

```text
Grouping alarms by timestamp and dependency
Comparing DRA-01 and DRA-02 clock offsets
Checking unaffected DRA peers
Testing whether Diameter failures follow NTP skew
Requesting missing NTP source health evidence
```

---

# 18. Required Explanation Block

Add a persistent small panel:

```text
WHAT CHANGED?
WHY DOES IT MATTER?
WHAT IS STILL UNKNOWN?
WHAT HAPPENS NEXT?
```

Example:

```text
What changed?
Two redundant DRA nodes now show clock skew before Diameter failures.

Why does it matter?
A shared dependency may explain both failures better than two independent faults.

Still unknown?
Health of the common NTP source.

Next?
Fetch NTP offset and reachability evidence.
```

This block should update whenever reasoning state materially changes.

---

# 19. Zaki Must Use the Same Reasoning State

Zaki should narrate the current stage and state.

Zaki should answer:

```text
what was observed
what belief changed
why it changed
what is unknown
what evidence is needed next
```

Do not let Zaki jump ahead of the backend state.

If the hypothesis is:

```text
SUPPORTED + NEEDS_MORE_EVIDENCE
```

Zaki should say:

```text
The leading hypothesis is supported by current evidence, but it is not yet confirmed.
FikraCore is waiting for NTP source health evidence before retesting.
```

---

# 20. Stage-Gated UI Disclosure

At each stage, only show what has been earned.

## Trigger

Show:

```text
first observation
affected entity
severity
timestamp
```

Hide:

```text
ranked hypotheses
root candidate
confirmed path
validated impact
learning
recommendation
```

## Signal Flood

Show:

```text
raw observations
counts
source distribution
```

## Correlation

Show:

```text
event groups
shared dependencies
candidate relationships
```

Do not show final root cause.

## Hypothesis Generation

Show:

```text
candidate explanations
initial basis
```

Rank only if ranking has actually occurred.

## Hypothesis Testing

Show:

```text
rank
confidence
supports
contradictions
missing evidence
confidence changes
```

## Knowledge Gap / Evidence Acquisition

Show:

```text
unknown boundary
missing evidence
next-best evidence
```

## Learning / Validation

Show:

```text
candidate learning
validation status
SME decision
```

## Action

Show:

```text
strongest supported explanation
recommendation
validated impact
```

---

# 21. Backend Stage Event Types

Emit explicit events such as:

```text
observation_added
correlation_created
candidate_hypothesis_created
hypothesis_ranked
hypothesis_test_started
evidence_support_added
evidence_contradiction_added
hypothesis_rejected
hypothesis_needs_more_evidence
next_best_evidence_requested
new_evidence_received
hypothesis_retest_started
root_candidate_changed
knowledge_gap_detected
validation_started
validation_completed
learning_candidate_created
recommendation_created
stage_transition
```

---

# 22. Stage Transition Trace

Every stage transition should emit:

```json
{
  "type": "stage_transition",
  "from": "HYPOTHESIS_TESTING",
  "to": "KNOWLEDGE_GAP_CHECK",
  "reason": "Leading hypothesis is supported but missing source health evidence",
  "scenario_id": "H4-WI-016",
  "run_id": "RUN-..."
}
```

---

# 23. Next-Best-Evidence Loop

When evidence is missing:

```text
HYPOTHESIS_TESTING
      ↓
NEEDS_MORE_EVIDENCE
      ↓
NEXT_BEST_EVIDENCE
      ↓
NEW EVIDENCE ARRIVES
      ↓
HYPOTHESIS_RETEST
```

The UI must visibly show this loop.

Do not advance to Learning while this loop remains unresolved.

---

# 24. Learning Gate

Learning may begin only when:

```text
reasoning terminal state reached
AND
candidate knowledge extracted
AND
validation workflow initiated
```

Do not show:

```text
Learning Enabled
```

as if learning is already complete.

Prefer:

```text
Learning Available
No validated learning yet
```

or:

```text
Candidate Learning Awaiting Validation
```

---

# 25. Unified Event Stream vs Reasoning Trace

Enforce:

```text
Unified Live Event Stream
= operational evidence only
```

and:

```text
FikraCore Reasoning Trace
= internal reasoning only
```

Do not mix them.

---

# 26. Suggested UI Layout Change

Keep the existing main layout, but add:

```text
Live Event Stream
→ raw network/OSS evidence

Reasoning Trace
→ optional drawer / panel / console

What FikraCore Is Doing
→ current active reasoning tasks

Explanation Block
→ what changed / why / unknown / next
```

This adds clarity without cluttering the main dashboard.

---

# 27. Trace Persistence

Persist trace records per:

```text
scenario_id
run_id
```

Allow replay:

```text
GET /simulations/{run_id}/trace
```

so historical runs can be inspected deterministically.

---

# 28. Trace Ordering

Trace ordering must use:

```text
sequence number
then timestamp
```

Do not rely on frontend arrival order only.

---

# 29. Trace Reconnect Safety

On reconnect:

```text
send last sequence received
request missing trace range
resume stream
```

If sequence gap exists:

```text
backfill trace
or
request full trace snapshot
```

---

# 30. Technical Trace Provenance

For technical mode include:

```text
component
provider
input IDs
output IDs
canonical entity IDs
knowledge source
reasoning engine version
latency
confidence components
```

Do not expose Hidden Truth.

---

# 31. Hidden Truth Isolation

Never include simulator Hidden Truth in:

```text
operator trace
Zaki trace
frontend trace
reasoning explanations
hypothesis confidence
impact
recommendations
```

Hidden Truth remains evaluator-only.

---

# 32. Acceptance Scenario

Use a scenario that requires:

```text
multiple observations
correlation
multiple hypotheses
one rejected hypothesis
one evidence gap
next-best evidence
retest
final supported explanation
```

Expected sequence:

```text
1. Raw alarm appears.
2. Additional raw evidence arrives.
3. Correlation groups observations.
4. Candidate hypotheses are created.
5. Hypotheses are ranked.
6. Leading hypothesis is tested.
7. It becomes SUPPORTED + NEEDS_MORE_EVIDENCE.
8. Next-best evidence request starts.
9. New evidence arrives in the raw event stream.
10. Hypothesis retest starts.
11. Confidence changes with explanation.
12. Knowledge gap resolves or remains explicit.
13. Validation begins only after reasoning terminal state.
14. Candidate learning appears.
15. Action/recommendation appears.
```

---

# 33. Required Tests — UI Consistency

Add:

```text
test_raw_event_stream_contains_only_operational_evidence
test_reasoning_outputs_not_classified_as_alarm
test_testing_stops_when_waiting_for_evidence
test_needs_more_evidence_state_visible
test_next_best_evidence_loop_returns_to_testing
test_learning_not_started_while_evidence_waiting
test_impact_has_epistemic_state
test_graph_health_separate_from_reasoning_role
test_confirmed_path_not_visible_too_early
test_stage_advances_only_on_exit_condition
test_zaki_respects_current_reasoning_state
```

---

# 34. Required Tests — Simulation Trace

Add:

```text
test_every_stage_transition_emits_trace
test_every_confidence_change_emits_trace
test_every_hypothesis_creation_emits_trace
test_every_hypothesis_rejection_emits_trace
test_every_knowledge_gap_emits_trace
test_every_next_best_evidence_request_emits_trace
test_trace_records_have_scenario_and_run_id
test_trace_records_have_sequence
test_trace_replay_is_deterministic
test_trace_live_stream_resumes_after_reconnect
test_trace_does_not_include_hidden_truth
```

---

# 35. Required Tests — Trace/UI Link

Add:

```text
test_graph_state_change_has_matching_trace_record
test_hypothesis_confidence_change_has_matching_trace_record
test_impact_state_change_has_matching_trace_record
test_stage_stepper_change_has_matching_trace_record
test_learning_state_change_has_matching_trace_record
```

---

# 36. Definition of Done

The fix is complete when:

```text
[ ] raw observability and reasoning are separated
[ ] event names are factual source observations
[ ] hypothesis states are explicit and correct
[ ] Testing does not remain active while waiting for evidence
[ ] Next-Best-Evidence loops back to testing
[ ] stage progression is condition-driven
[ ] service impact is labeled observed / estimated / confirmed
[ ] graph health and reasoning role are separate
[ ] Learning / Validation cannot start prematurely
[ ] Zaki explains current reasoning without jumping ahead
[ ] View Trace is available
[ ] Summary / Verbose / Technical trace modes work
[ ] stages are clickable for filtered trace
[ ] every meaningful UI transition has a trace record
[ ] trace is run-scoped and replayable
[ ] trace reconnect is sequence-safe
[ ] Hidden Truth remains isolated
```

---

# Final Principles

> **Operational evidence, reasoning output, impact, and learning are different data classes and must remain separate.**

> **A stage advances only when its exit condition is satisfied.**

> **If a hypothesis needs more evidence, the simulator must visibly loop through evidence acquisition and retesting before validation or learning.**

> **Every visible simulation transition must be explainable through a corresponding backend trace record.**
