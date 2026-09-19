# FikraCore Step 5 — Simulation Progression, Clean Run Initialization & Impact Gating Fix

## Purpose

Fix the simulator defects where:

1. a simulation run can remain stuck at an early stage and does not progress;
2. customer/service impact is already visible before the investigation has earned it;
3. a scenario run may start partially pre-solved instead of epistemically empty;
4. stage transitions do not clearly explain why they advanced or why they are blocked.

The simulator must start from minimal observable evidence and progressively derive:

```text
correlation
hypotheses
impact
knowledge gaps
next-best evidence
validation
learning
recommendations
```

> **A simulation run must start epistemically empty and progressively earn impact, hypotheses, causal paths, knowledge gaps, and recommendations.**

---

# 1. Required Simulation Lifecycle

Use:

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
   ↓
KNOWLEDGE_GAP / NEXT_BEST_EVIDENCE
   ↘
     RETEST LOOP
   ↓
VALIDATION
   ↓
LEARNING
   ↓
ACTION / RECOMMENDATION
```

A stage must advance only when its exit condition is satisfied.

Do not advance stages based only on elapsed time.

---

# 2. Clean Run Initialization

When a simulation run starts, initialize operational state as unknown/empty.

Recommended:

```python
run_state = {
    "stage": "TRIGGER",
    "events": [],
    "correlations": [],
    "hypotheses": [],
    "impact": {
        "state": "UNKNOWN",
        "affected_users": None,
        "affected_services": [],
        "regions": [],
        "degradation_pct": None,
        "confidence": None
    },
    "knowledge_gaps": [],
    "next_best_evidence": [],
    "learning": None,
    "recommendations": [],
    "root_candidate": None,
    "causal_path": None
}
```

Do not populate final incident values at run creation.

---

# 3. Hidden Truth Must Stay Separate

Scenario definitions may contain:

```text
actual root condition
true blast radius
expected affected users
true service degradation
hidden dependency
expected final causal path
```

These must remain in simulator/evaluator truth only.

Correct:

```text
Hidden Truth
→ Evaluator
```

Operational run state gets only:

```text
observable initial evidence
```

Never initialize run state from the final scenario outcome.

---

# 4. Observable Initial State

Each scenario should define an operational starting point separate from Hidden Truth.

Example:

```text
Hidden Truth:
Database migration lock ultimately causes service degradation.

Initial Observable State:
one database alarm
one latency anomaly
everything else unknown
```

The simulator then progressively emits further evidence.

---

# 5. Explicit Stage Exit Conditions

## Trigger

Exit when:

```text
at least one valid source observation has been ingested
```

Example:

```python
if stage == "TRIGGER" and valid_observation_count >= 1:
    transition_to("SIGNAL_FLOOD")
```

## Signal Flood

Exit when:

```text
initial evidence window closes
or
minimum evidence count is reached
or
scenario-specific evidence condition is satisfied
```

## Correlation

Exit when:

```text
event groups are created
temporal relationships evaluated
shared dependencies evaluated
candidate relationships emitted
```

## Hypothesis Generation

Exit when:

```text
one or more candidate explanations exist
```

## Hypothesis Testing

Testing finishes when active candidates reach one of:

```text
SUPPORTED
REJECTED
CONTRADICTED
NEEDS_MORE_EVIDENCE
```

Do not leave `Testing...` after all currently available tests are complete.

---

# 6. Needs-More-Evidence Loop

If the leading hypothesis requires more evidence:

```text
HYPOTHESIS_TESTING
      ↓
NEEDS_MORE_EVIDENCE
      ↓
NEXT_BEST_EVIDENCE
      ↓
NEW OBSERVATION
      ↓
HYPOTHESIS_RETEST
```

Do not advance directly to Validation or Learning.

---

# 7. Validation and Learning Gates

Validation may begin only when:

```text
reasoning reaches an eligible terminal state
AND
required evidence state is sufficiently resolved
```

Learning may begin only after validation starts.

At Trigger do not show:

```text
Learning Enabled
```

Prefer:

```text
Learning available after validation
```

or:

```text
No validated learning yet
```

---

# 8. Customer / Service Impact State Machine

Impact may appear before RCA completes, but it must carry certainty.

Use:

```text
UNKNOWN
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

At run start:

```text
Impact:
UNKNOWN

No customer-impact evidence yet.
```

Do not show precise impact values unless evidence supports them.

---

# 9. Impact Progression

## Observed

```text
Subscriber session failures detected.
Scope still being estimated.
```

## Estimated

```text
~6,000 users potentially affected
Confidence: 64%
```

## Confirmed

```text
6,120 affected sessions
1 region
```

Use confirmed values only when backend validation supports them.

---

# 10. Impact Contract

Example:

```json
{
  "service": "Subscriber Services",
  "impact_state": "ESTIMATED",
  "degradation_pct": 20,
  "affected_users": 6000,
  "regions": 1,
  "confidence": 0.64,
  "evidence_ids": ["EVT-12", "EVT-15"]
}
```

Do not derive early impact directly from Hidden Truth.

---

# 11. Stage Transition Events

Every stage transition must emit a trace record.

Example:

```json
{
  "type": "stage_transition",
  "scenario_id": "H4-WI-035",
  "run_id": "RUN-...",
  "from": "TRIGGER",
  "to": "SIGNAL_FLOOD",
  "reason": "Initial valid observation received",
  "timestamp": "2026-09-12T01:43:38Z"
}
```

---

# 12. Stage Blocked Trace

If a stage does not advance, emit the reason.

Example:

```json
{
  "type": "stage_blocked",
  "scenario_id": "H4-WI-035",
  "run_id": "RUN-...",
  "stage": "TRIGGER",
  "required_condition": "valid_observation_count >= 1",
  "actual": {
    "valid_observation_count": 0
  },
  "reason": "No validated source observation has been ingested"
}
```

---

# 13. Stage Watchdog

Track:

```text
entered_at
elapsed_in_stage
exit_conditions
current_condition_values
blocking_reason
next_expected_transition
```

Technical Trace example:

```text
Current Stage: TRIGGER
Elapsed: 00:00:39

Exit Condition:
valid_observation_count >= 1

Current:
valid_observation_count = 1

Transition:
BLOCKED

Reason:
signal_flood_start event not emitted
```

If blocked too long, emit a diagnostic event instead of silently hanging.

---

# 14. Stage Progress UI

Near the journey stepper show:

```text
Current Stage
Waiting For
Received / Required
Next Transition
Status
```

Example:

```text
Stage:
Trigger

Waiting For:
Initial evidence ingestion

Received:
1 / 1 valid observation

Next:
Signal Flood

Status:
Transition pending
```

---

# 15. Backend-Driven Progress

The UI must consume:

```text
current_stage
stage_status
exit_condition_state
next_stage
blocking_reason
```

Stage status values:

```text
NOT_STARTED
ACTIVE
WAITING
BLOCKED
COMPLETED
FAILED
```

---

# 16. Stage Snapshot Contract

Recommended:

```json
{
  "current_stage": "TRIGGER",
  "stage_status": "BLOCKED",
  "entered_at": "2026-09-12T01:43:00Z",
  "elapsed_ms": 39000,
  "exit_conditions": [
    {
      "name": "valid_observation_count",
      "operator": ">=",
      "required": 1,
      "actual": 1,
      "satisfied": true
    }
  ],
  "next_stage": "SIGNAL_FLOOD",
  "blocking_reason": "signal_flood_start event not emitted"
}
```

---

# 17. Transition Engine Audit

Audit for:

```text
stage enum mismatch
incorrect stage name
transition event never emitted
wrong run_id
stage guard rejecting valid event
async task not awaited
failed callback
transition not persisted
frontend stale snapshot
```

---

# 18. Transition Persistence Order

Use:

```text
validate exit condition
↓
update run stage
↓
persist run state
↓
emit stage_transition
↓
broadcast snapshot/delta
```

Transitions must be idempotent.

---

# 19. Simulation Start Contract

Starting a scenario should:

```text
create fresh run
initialize clean operational state
set stage=TRIGGER
emit first observable evidence according to scenario schedule
start stage engine
start trace
```

Do not hydrate a new run from previous run data or final scenario outcome.

---

# 20. Replay Contract

Replay must begin from the same clean initial operational state and replay evidence in recorded order.

Do not start replay from a final snapshot.

---

# 21. Scenario Evidence Release Plan

Each scenario should define a visible evidence schedule separate from Hidden Truth.

Example:

```text
T+0   DB lock alarm
T+5   query latency KPI rises
T+12  session failures increase
T+18  customer ticket arrives
```

The exact schedule must come from the scenario.

---

# 22. Trigger-Stage UI Defaults

At Trigger:

## Hypothesis

```text
No hypotheses generated yet
```

## Impact

```text
Impact unknown
```

## Knowledge Gaps

```text
No explicit knowledge gap detected yet
```

## Next Best Evidence

```text
Not requested yet
```

## Learning

```text
No validated learning yet
```

## Causal Path

```text
Awaiting causal analysis
```

---

# 23. No Final-Looking Placeholders

Avoid values such as:

```text
-20%
6,000 users
68% path confidence
25% hypothesis confidence
```

before they are derived.

Use:

```text
—
Unknown
Not yet evaluated
Awaiting analysis
```

---

# 24. Causal Graph at Trigger

Show only:

```text
observed entities
healthy known context
unknown state
```

Do not show:

```text
Root Candidate
Leading Causal Path
Confirmed Causal Path
```

until those states exist.

---

# 25. Hypothesis Panel at Trigger

Show:

```text
No hypotheses generated yet.

FikraCore is collecting initial evidence.
```

No ranked cards.

---

# 26. Verbose Trace Integration

The trace should expose exact run progression.

Example:

```text
[01:43:00.100] RUN_CREATED
scenario=H4-WI-035

[01:43:00.120] RUN_STATE_INITIALIZED
impact=UNKNOWN
hypotheses=0
knowledge_gaps=0

[01:43:00.150] STAGE_ENTER
stage=TRIGGER

[01:43:01.004] OBSERVATION_ADDED
event=EVT-001
source=DB-CORE-05

[01:43:01.010] EXIT_CONDITION_CHECK
valid_observation_count=1
required=1
satisfied=true

[01:43:01.014] STAGE_TRANSITION
TRIGGER -> SIGNAL_FLOOD
```

Blocked:

```text
[01:43:39.000] STAGE_BLOCKED
stage=TRIGGER
reason=signal_flood_start event not emitted
```

---

# 27. Required Backend Tests

Add:

```text
test_new_run_starts_with_unknown_impact
test_new_run_has_no_ranked_hypotheses
test_new_run_has_no_root_candidate
test_new_run_has_no_confirmed_path
test_trigger_advances_when_first_observation_arrives
test_signal_flood_advances_when_exit_condition_met
test_stage_transition_is_persisted
test_stage_transition_emits_trace
test_blocked_stage_emits_reason
test_stage_transition_is_idempotent
test_hidden_truth_not_copied_into_operational_run
```

---

# 28. Impact Tests

Add:

```text
test_impact_starts_unknown
test_observed_impact_requires_source_evidence
test_estimated_impact_has_confidence
test_confirmed_impact_requires_validation
test_hidden_truth_impact_not_exposed_early
```

---

# 29. UI Tests

Add:

```text
test_trigger_shows_unknown_impact
test_trigger_shows_no_hypothesis
test_trigger_shows_no_learning
test_trigger_shows_no_confirmed_path
test_stage_block_reason_visible
test_stage_progress_updates_after_transition
test_no_real_looking_placeholder_values_before_derivation
```

---

# 30. Acceptance Walkthrough

```text
1. Start a fresh run.
2. Confirm Impact = UNKNOWN.
3. Confirm Hypotheses = none.
4. Confirm Causal Path = awaiting analysis.
5. Confirm Learning = none.
6. Observe first source event.
7. Confirm Trigger exit condition becomes satisfied.
8. Confirm transition to Signal Flood occurs.
9. Confirm additional evidence appears progressively.
10. Confirm impact changes only when evidence supports it.
11. Confirm hypotheses appear only after generation stage.
12. Confirm the run does not get stuck silently.
13. If blocked, confirm exact blocking reason appears in trace.
```

---

# 31. Definition of Done

```text
[ ] every new run starts clean and epistemically empty
[ ] Hidden Truth is not copied into operational state
[ ] impact starts UNKNOWN
[ ] no ranked hypothesis exists at Trigger
[ ] no confirmed path exists at Trigger
[ ] no learning state is implied at Trigger
[ ] stages advance only when exit conditions are satisfied
[ ] blocked stages expose an exact reason
[ ] stage transitions are persisted and traceable
[ ] transition engine is retry-safe
[ ] impact evolves UNKNOWN → OBSERVED → ESTIMATED → CONFIRMED
[ ] UI never shows final-looking values before derivation
[ ] replay starts from clean initial state
[ ] verbose trace explains every transition
```

---

# Final Principles

> **A scenario may know the final truth; the operational simulation run must not.**

> **The run begins with minimal observable evidence and progressively earns every conclusion.**

> **Every stage needs explicit entry conditions, exit conditions, transition events, and a trace explaining why it advanced—or why it is blocked.**
