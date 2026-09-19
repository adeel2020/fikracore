# FikraCore Step 5.1 — Simulation Orchestration & Zaki Copilot

## Purpose

Step 5 is already implemented, tested, and verified.

This document defines the **next additive step only**.

Do **not** reimplement or redesign capabilities that are already complete.

Step 5.1 is limited to:

1. **Simulation Execution Orchestration**
2. **Zaki Simulation Copilot**

The objective is to add a robust backend-controlled run lifecycle and make Zaki deeply stage-aware, while preserving all existing Step 5 behavior.

---

# 1. Existing Step 5 Baseline — Already Complete

The following are already implemented and verified and must be treated as stable:

```text
scenario/run scoping
backend-driven light-up state
stale event rejection
scenario-switch cleanup
atomic snapshot hydration
backend-owned pathway activation
backend-owned connection reasons
backend-owned hypothesis confidence
knowledge-gap naming
validation naming
domain attribution gating
progressive simulation state
shared UI revision
human-readable labels
H1–H4 fidelity
Zaki active-run binding
TypeScript checks
ESLint checks
backend acceptance tests
frontend acceptance tests
```

Do not rebuild these.

---

# 2. Non-Negotiable Preservation Rule

Before changing code:

1. Inspect the existing Step 5 implementation.
2. Identify current:
   - run model
   - stage state machine
   - APIs
   - SSE/WebSocket flow
   - simulation store
   - Zaki bridge
   - existing action handlers
3. Reuse all existing contracts where possible.
4. Extend only additively.
5. Do not create:
   - a second run model
   - a second simulation engine
   - a duplicate event bus
   - a duplicate Zaki context model
6. Run the full existing regression suite before changes.
7. Run it again after changes.
8. Reject the implementation if prior Step 5 behavior regresses.

---

# 3. Step 5.1 Scope

Build only:

```text
A. Simulation Orchestrator

B. Zaki Simulation Copilot
```

Do not expand scope into:

```text
new UI redesign
new H1–H4 reasoning
new confidence algorithm
new KnowledgeProvider
new canonicalization layer
new scenario catalog
new hidden-truth logic
new learning engine
new domain-attribution engine
new transport mechanism if one already exists
```

---

# PART A — SIMULATION ORCHESTRATOR

# 4. Goal

Introduce one authoritative backend execution lifecycle for each simulation run.

The frontend must remain a passive projection of backend state.

The orchestrator owns:

```text
run lifecycle
stage lifecycle
stage entry
stage execution
stage exit conditions
blocked-state handling
Next-Best Evidence wait/resume
same-stage retest
stage completion
run finalization
```

---

# 5. Canonical Run Lifecycle

Use the existing run object if already present.

Add lifecycle state only if missing.

Recommended run states:

```text
CREATED
INITIALIZING
RUNNING
BLOCKED
PAUSED
COMPLETED
FAILED
STOPPED
```

Semantics:

```text
CREATED
= run exists but execution has not started

INITIALIZING
= scenario/runtime context is being prepared

RUNNING
= backend worker is actively executing the current stage

BLOCKED
= current stage cannot advance until a required condition is satisfied

PAUSED
= run is intentionally suspended

COMPLETED
= terminal pipeline completed successfully

FAILED
= unrecoverable backend execution failure

STOPPED
= operator intentionally terminated the run
```

Do not overload `COMPLETED` to mean stopped or blocked.

---

# 6. One Managed Worker Per Run

There must be exactly one execution authority per `run_id`.

Conceptually:

```text
run_id
  ↓
managed simulation worker
  ↓
authoritative stage execution
```

Multiple:

```text
browser tabs
SSE clients
WebSocket clients
Zaki sessions
UI remounts
```

must never independently advance the run.

Subscribers may:

```text
read snapshot
receive events
request governed operator actions
```

Subscribers must not:

```text
advance stages directly
change hypothesis confidence
activate pathways
mark evidence complete
confirm validation
promote learning
```

---

# 7. Stage Execution Lifecycle

Use this execution loop:

```text
ENTER STAGE
    ↓
EXECUTE STAGE
    ↓
PERSIST RESULT
    ↓
INCREMENT REVISION / SEQUENCE
    ↓
EMIT AUTHORITATIVE EVENT(S)
    ↓
CHECK EXIT CONDITIONS
    ├── satisfied
    │      ↓
    │   READY_TO_ADVANCE
    │      ↓
    │   COMPLETE STAGE
    │      ↓
    │   ENTER NEXT STAGE
    │
    └── not satisfied
           ↓
        BLOCKED
           ↓
     expose exact reason
           ↓
     expose missing context
           ↓
     expose Next-Best Evidence
           ↓
     wait for action/evidence
           ↓
     evidence result arrives
           ↓
     RETEST SAME STAGE
           ↓
     check exit conditions again
```

The stage must not advance merely because time elapsed.

---

# 8. Stage State

Use the current stage model if one already exists.

If explicit stage status is missing, extend additively:

```text
NOT_STARTED
ACTIVE
BLOCKED
READY_TO_ADVANCE
COMPLETE
```

Recommended data shape:

```ts
type StageExecutionState = {
  scenario_id: string
  run_id: string

  stage: string

  status:
    | "NOT_STARTED"
    | "ACTIVE"
    | "BLOCKED"
    | "READY_TO_ADVANCE"
    | "COMPLETE"

  entered_at?: string
  completed_at?: string

  exit_conditions?: StageExitCondition[]

  block_reason?: string
  waiting_for?: string

  revision: number
  sequence: number
}
```

Adapt this to the existing repository instead of creating a duplicate model.

---

# 9. Stage Exit Conditions

Every stage must have explicit backend exit conditions.

Never advance because:

```text
UI animation finished
timer expired
Play was clicked
React effect fired
subscriber connected
frontend inferred readiness
```

Recommended exit-condition structure:

```ts
type StageExitCondition = {
  condition_id: string
  display_name: string
  satisfied: boolean
  expected?: string
  actual?: string
  reason?: string
}
```

Examples:

```text
Trigger
→ at least one valid source observation admitted

Signal Flood / Evidence Build
→ configured evidence window/minimum evidence condition satisfied

Correlation
→ correlation state persisted

Hypothesis Generation
→ candidate generation completed
  OR explicitly no defensible candidate yet

Hypothesis Testing
→ required tests completed
  OR material unresolved context detected

Knowledge Gap Check
→ gaps classified and
  resolved / explicitly unresolved / NBE required

Validation
→ domain engineer/HITL decision recorded
  OR explicitly not applicable

Action / Learning
→ final recommendation / learning eligibility persisted
```

---

# 10. Blocked-State Handling

When a stage is blocked, remain on that same stage.

Persist:

```text
stage
status = BLOCKED
block_reason
waiting_for
exit_conditions
```

Example:

```text
Stage:
Knowledge Gap Check

Status:
BLOCKED

Blocking Reason:
Redundant MPLS Path Health Unknown

Waiting For:
Backup-path telemetry

Affected Hypothesis:
H1 — IP/MPLS Edge Router-07 Failure

Affected Pathway:
Resilience & Failover
```

The UI must display the exact reason.

Do not show only a generic `?`.

---

# 11. Next-Best Evidence Loop

The correct loop is:

```text
Blocked Stage
→ Knowledge Gap
→ Next-Best Evidence
→ Operator Request
→ Backend Validates Request
→ Request Persisted
→ Evidence Provider Executes
→ Evidence Returned / Unavailable / Failed / Timed Out
→ Result Persisted
→ Same Stage Retests
→ Exit Conditions Re-evaluated
```

Do not mark evidence as completed merely because the operator clicked a button.

Valid evidence-request outcomes may include:

```text
RETURNED
UNAVAILABLE
FAILED
TIMED_OUT
DECLINED
```

All outcomes remain inspectable.

---

# 12. Run Controls

Preserve the existing UI controls.

Clarify semantics only where needed.

## Play

If:

```text
CREATED
```

then:

```text
initialize + start run
```

If:

```text
PAUSED
```

then:

```text
resume existing run
```

If:

```text
BLOCKED
```

then:

```text
Play must not bypass the block
```

Only resume when the backend determines the missing condition is satisfied.

## Pause

```text
RUNNING → PAUSED
```

Persist pause state.

Resume from persisted state.

## Stop

```text
RUNNING / BLOCKED / PAUSED
→ STOPPED
```

Do not convert STOPPED to COMPLETED.

## Replay

Replay is read-only.

Replay consumes recorded backend events.

Replay must not:

```text
rerun reasoning
change original state
generate new confidence
produce new learning
```

---

# 13. Stage Watchdog

Add a diagnostic stage watchdog.

Track:

```text
current stage
stage entered_at
elapsed time
stage status
exit conditions
satisfied conditions
unsatisfied conditions
blocking reason
waiting_for
last event
last sequence
```

Important:

> The watchdog diagnoses a stuck stage. It must not force progression.

Example trace:

```text
Stage: KNOWLEDGE_GAP_CHECK
Status: BLOCKED
Elapsed: 00:01:42

Satisfied:
✓ Knowledge gap classified

Waiting:
✗ Required topology context resolved

Blocking reason:
Shared upstream dependency is unavailable in operational knowledge.

Next:
Request topology/inventory evidence or conclude MODEL_INSUFFICIENT.
```

---

# 14. Event Ordering

Recommended stage-event order:

```text
stage_entered
→ stage_progressed / reasoning events
→ optional stage_blocked
→ optional evidence_requested
→ optional evidence_received
→ optional hypothesis_retested
→ stage_ready_to_advance
→ stage_completed
→ next stage_entered
```

Persist state before broadcasting events.

Reuse the existing:

```text
scenario_id
run_id
revision
sequence
timestamp
```

ordering contract.

---

# 15. Run Finalization

Do not force every scenario to produce a confirmed root cause.

Supported terminal outcomes may include:

```text
EXPLAINED
PARTIALLY_EXPLAINED
UNRESOLVED
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
MODEL_INSUFFICIENT
```

Before setting:

```text
run_status = COMPLETED
```

persist:

```text
terminal state
supported hypotheses
remaining contradictions
remaining knowledge gaps
synthesis state
service-impact certainty
validation result if applicable
domain attribution if supported
recommendation if supported
learning eligibility/candidate if supported
full reasoning trace
```

---

# 16. UI Representation

The existing Step 5 Journey should bind to backend stage state.

Recommended presentation:

```text
COMPLETE
→ green check

ACTIVE
→ cyan active state

BLOCKED
→ amber / question state + exact reason

READY_TO_ADVANCE
→ cyan pulse

NOT_STARTED
→ dimmed
```

For blocked stages, show:

```text
Stage
Status
Waiting For
What Has Been Received
Next Required Action
```

Do not redesign the current UI unless required for these fields.

---

# PART B — ZAKI SIMULATION COPILOT

# 17. Goal

Upgrade the existing Zaki integration from:

```text
run-aware assistant
```

to:

```text
stage-aware Simulation Copilot
```

Do not create a new assistant implementation.

Extend the existing Zaki bridge and context model.

---

# 18. Zaki's Role

Zaki is:

```text
Simulation Copilot
Contextual Explainer
Reasoning Navigator
Operator Assistant
```

Zaki is not:

```text
reasoning authority
source of truth
confidence calculator
root-cause generator independent of backend
validation authority
domain-attribution authority
learning authority
```

Core rule:

> The backend reasons. The run state records. The UI visualizes. Zaki explains and orchestrates.

---

# 19. Authoritative Zaki Context

Zaki must consume the same active run state as the UI.

Minimum:

```text
scenario_id / intent_id
run_id
revision
sequence
run_status
current stage
stage status
```

Also include, when available:

```text
source context
evidence
active reasoning pathways
active connections
hypotheses
hypothesis confidence/history
knowledge gaps
next-best evidence
intelligence synthesis
service impact
validation
learning
domain attribution
reasoning focus
blocking reason
waiting_for
stage exit conditions
```

Do not trust stale frontend state.

---

# 20. Zaki Context Resolution

Preferred request flow:

```text
UI sends:
message
+ scenario_id / intent_id
+ run_id
+ current revision
+ selected object context

Zaki backend:
→ verifies run
→ loads authoritative InvestigationRun
→ checks revision
→ loads selected-object context
→ builds grounded prompt/context
→ invokes model
→ returns grounded response
```

The server should resolve authoritative state.

Do not use the entire browser store as trusted truth.

---

# 21. Stage-Aware Zaki Behavior

## Trigger / Detection

Explain:

```text
what started the run
what intent/scenario is active
what is currently known
what is not yet known
```

Do not discuss final root cause.

## Evidence Build

Explain:

```text
which evidence arrived
where it came from
what is still unavailable
```

## Correlation

Explain:

```text
which evidence is being grouped
which services/entities appear related
which shared dependencies are being examined
```

## Hypothesis Generation

Explain:

```text
H1–H4 candidate explanations
why each is plausible
which pathways contributed
```

## Hypothesis Testing

Explain:

```text
supporting evidence
contradicting evidence
missing evidence
why confidence changed
```

## Knowledge Gap

Explain:

```text
exact missing context
why it matters
which hypothesis/pathway it blocks
next-best evidence
```

## Validation

Explain:

```text
what fact is being reviewed
which engineer/domain is expected to validate
what remains uncertain
```

## Action / Learning

Explain:

```text
recommended action
why it is recommended
whether learning is eligible
what validated knowledge may be retained
```

---

# 22. Blocked-Stage Copilot

When:

```text
run_status = BLOCKED
```

Zaki should prioritize:

```text
Why are we blocked?
Which exit condition failed?
What evidence has already arrived?
What is still required?
Which hypothesis is affected?
Which pathway is affected?
What happens after evidence arrives?
Can the run terminate as MODEL_INSUFFICIENT?
```

Example response:

```text
The simulation is blocked at Knowledge Gap Check.

Missing context:
Redundant MPLS Path Health Unknown.

Affected hypothesis:
H1 — IP/MPLS Edge Router-07 Failure

Affected pathway:
Resilience & Failover

Next-best evidence:
Retrieve backup-path telemetry.

After the evidence returns, H1 will be retested on the same stage.
```

---

# 23. Explainability Actions

Recommended contextual actions:

```text
Explain this
Why is this active?
Show supporting evidence
Show contradicting evidence
Why did H1 increase?
Why did H2 weaken?
What remains unknown?
What evidence is needed next?
Why are we blocked?
What changed since last revision?
Why is this domain PRIMARY?
What would change the conclusion?
```

Use existing action handlers where possible.

---

# 24. Pathway Explanation

Zaki should explain:

```text
pathway name
why active
which evidence activated it
which hypotheses it affects
current contribution state
```

Example:

```text
Service Dependency is active because Enterprise APN,
Internet Services, and Corporate IP-VPN share the same
upstream IP/MPLS dependency.

It currently supports H1.
```

---

# 25. Connection Explanation

For a selected Neural Reasoning Map connection, provide Zaki:

```text
source display name
target display name
relation type
state
reason
supporting evidence
confidence delta if any
provenance
```

Example:

```text
Routing Change CR-7721
→ Change & Configuration

Why active:
The change completed six minutes before degradation.

Current interpretation:
Temporally relevant, but not yet proven causal.
```

---

# 26. Hypothesis Explanation

For H1–H4, Zaki should summarize:

```text
hypothesis title
state
confidence if available
supporting evidence
contradictions
missing evidence
active pathways
latest confidence delta
reason for latest change
```

If confidence is unknown:

```text
Unranked
```

not:

```text
0%
```

---

# 27. Intelligence Synthesis Explanation

Zaki should explain the Reasoning Core / Intelligence Synthesis state.

Possible dimensions:

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

Do not invent a single synthesis score unless the backend provides one.

---

# 28. Domain Attribution Explanation

Zaki should explain:

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
IP Transport is PRIMARY because the leading supported cause
belongs to the transport domain and explains the cross-domain impact.

Mobile Core is AFFECTED, not primary.
```

Do not identify a culprit domain before backend attribution exists.

---

# 29. Next-Best Evidence Through Zaki

Zaki may:

```text
explain why evidence is needed
compare evidence requests
explain which hypotheses the request discriminates
invoke an existing permitted request action
```

Zaki must not directly mark evidence complete.

Correct flow:

```text
Zaki invokes request
→ backend handler validates
→ request persisted
→ provider executes
→ result returned
→ run updated
→ same stage retests
→ Zaki sees new revision
```

---

# 30. Governed Zaki Actions

Allowed through existing backend handlers:

```text
request evidence
focus hypothesis
focus pathway
show evidence
show gap
request validation
resume run if backend permits
```

Forbidden direct mutations:

```text
set confidence
confirm root cause
set PRIMARY domain
accept validation
promote learning
complete stage
```

---

# 31. Play / Pause / Stop / Replay Awareness

Zaki must understand the run control state.

## Play

For `CREATED`:

```text
starts run
```

For `PAUSED`:

```text
resumes run
```

For `BLOCKED`:

```text
does not bypass the blocking condition
```

## Stop

Explain:

```text
run becomes STOPPED
```

not completed.

## Replay

Show clearly:

```text
REPLAY MODE
```

Zaki must explain recorded events, not imply new reasoning is occurring.

---

# 32. Replay-Aware Zaki

In replay, provide:

```text
mode = REPLAY
original_run_id
replay_position
replay_revision
```

Zaki should answer:

```text
What happened at this point?
Why did H2 weaken here?
Which evidence had arrived?
Why did the stage block?
```

Do not use future replay events unless the user asks for a completed-run summary.

---

# 33. Revision-Diff Awareness

To support "What changed?", provide Zaki an authoritative diff when possible.

Recommended:

```ts
type ZakiRevisionDiff = {
  previous_revision: number
  current_revision: number

  evidence_added?: string[]
  pathways_activated?: string[]
  hypotheses_changed?: string[]
  gaps_added?: string[]
  gaps_resolved?: string[]
  synthesis_changed?: boolean
  validation_changed?: boolean
  attribution_changed?: boolean
}
```

Do not derive the diff by visually inspecting the frontend.

---

# 34. Response Levels

Support:

```text
Executive
Operator
Engineer
Deep Technical
```

## Executive

Focus:

```text
service impact
leading explanation
uncertainty
primary domain
decision
```

## Operator

Focus:

```text
stage
evidence
pathways
hypotheses
gaps
NBE
next action
```

## Engineer

Focus:

```text
entities
dependencies
protocol/topology context
support/contradiction
test results
```

## Deep Technical

Focus:

```text
canonical IDs
provenance
revision
sequence
provider
trace
```

Human-readable names remain primary.

---

# 35. Zaki Context Header

Compact panel example:

```text
ZAKI — SIMULATION COPILOT

Scenario:
Incomplete Operational Knowledge Model Insufficiency

Run:
RUN-20260913-103431

Stage:
Knowledge Gap Check

State:
BLOCKED
```

Do not overload the panel.

---

# 36. Proactive Zaki Messages

Allow proactive messages only on real backend state changes.

Examples:

```text
New evidence changed H1 confidence.

A knowledge gap is blocking the current stage.

H3 was rejected after contradictory evidence arrived.

The run is waiting for redundant-path telemetry.

Domain attribution changed to IP Transport PRIMARY.

Validation is ready.
```

Do not repeat unchanged state.

---

# 37. Failure Handling

If context is unavailable or incomplete, Zaki must say so.

Examples:

```text
The active run does not contain enough information to answer that.

The current stage has not produced domain attribution yet.

The knowledge provider is unavailable for this request.

That evidence has not yet been admitted to this run.
```

Never silently guess.

---

# 38. Hidden Truth Isolation

During simulation reasoning:

```text
Hidden Truth → Zaki
```

is forbidden.

Allowed:

```text
Operational Run State → Zaki
```

Evaluator results may only be discussed after they are explicitly exposed through a governed post-run evaluation surface.

---

# 39. Zaki Endpoint

Reuse the existing endpoint.

If an additive endpoint is required:

```text
POST /api/v1/fikracore/zaki/chat
```

Recommended request:

```json
{
  "message": "Why are we blocked?",
  "scenario_id": "H4-WI-040",
  "run_id": "RUN-20260913-103431",
  "revision": 184,
  "response_level": "ENGINEER",
  "selected_context": {
    "stage": "KNOWLEDGE_GAP_CHECK"
  }
}
```

The backend must resolve authoritative state itself.

---

# 40. Response Contract

Recommended:

```ts
type ZakiResponse = {
  scenario_id?: string
  run_id: string
  revision: number

  response_level:
    | "EXECUTIVE"
    | "OPERATOR"
    | "ENGINEER"
    | "DEEP_TECHNICAL"

  answer: string

  grounded_in?: {
    evidence_ids?: string[]
    pathway_ids?: string[]
    hypothesis_ids?: string[]
    gap_ids?: string[]
    connection_ids?: string[]
    stage?: string
  }

  uncertainty?: string[]
  suggested_actions?: ZakiSuggestedAction[]
}
```

---

# 41. Suggested Action Contract

```ts
type ZakiSuggestedAction = {
  action_id: string
  display_name: string

  action_type:
    | "SHOW_EVIDENCE"
    | "FOCUS_HYPOTHESIS"
    | "FOCUS_PATHWAY"
    | "REQUEST_EVIDENCE"
    | "SHOW_GAP"
    | "SHOW_ATTRIBUTION"
    | "REQUEST_VALIDATION"

  enabled: boolean
  disabled_reason?: string
  target_id?: string
}
```

Do not expose actions the current run does not permit.

---

# 42. Acceptance Scenario

Primary acceptance:

```text
H4-WI-040 — Incomplete Operational Knowledge Model Insufficiency
```

Expected:

```text
1. run starts normally
2. stages execute backend-first
3. evidence appears progressively
4. hypotheses evolve
5. Knowledge Gap Check blocks
6. exact gap is exposed
7. Zaki explains why blocked
8. Zaki explains affected hypothesis/pathway
9. NBE becomes available
10. operator requests evidence
11. backend persists request
12. result returns
13. same stage retests
14. Zaki explains what changed
15. run advances or terminates as MODEL_INSUFFICIENT
16. no false RCA is forced
```

Secondary acceptance:

```text
MPLS Edge Router Failure
```

Expected:

```text
different evidence
different pathways
different hypotheses
different blocking behavior
different domain attribution
```

No scenario-specific frontend/Zaki hardcoding.

---

# 43. Backend Tests

Add focused tests:

```text
test_one_managed_worker_per_run
test_stage_does_not_advance_before_exit_condition
test_blocked_stage_retests_same_stage_after_evidence
test_play_does_not_bypass_blocked_condition
test_stop_marks_run_stopped_not_completed
test_replay_does_not_rerun_reasoning
test_stage_watchdog_reports_blocking_condition
test_run_finalizes_only_on_terminal_condition

test_zaki_context_scoped_to_run
test_zaki_context_scoped_to_scenario
test_zaki_rejects_stale_revision
test_zaki_uses_authoritative_snapshot
test_zaki_does_not_use_hidden_truth
test_zaki_explains_blocked_stage
test_zaki_explains_stage_exit_condition
test_zaki_explains_pathway_activation
test_zaki_explains_hypothesis_delta
test_zaki_explains_domain_attribution
test_zaki_does_not_mutate_confidence
test_zaki_does_not_complete_stage
test_zaki_action_routes_through_backend_handler
test_zaki_replay_does_not_look_ahead
test_zaki_context_switch_clears_old_run
```

---

# 44. Frontend Tests

Add only focused new tests:

```text
test_run_status_controls_play_pause_stop
test_blocked_stage_shows_exact_reason
test_stage_exit_condition_visible
test_replay_mode_does_not_mutate_run

test_zaki_panel_displays_active_run_context
test_zaki_updates_when_revision_changes
test_zaki_scenario_switch_clears_old_context
test_zaki_blocked_stage_prompt
test_zaki_suggested_action_disabled_when_not_permitted
test_zaki_response_level_switch
test_zaki_replay_mode_indicator
test_zaki_click_connection_passes_selected_context
test_zaki_click_hypothesis_passes_selected_context
```

---

# 45. Regression Gate

Before implementation:

```text
run all current Step 5 tests
record baseline
```

After implementation:

```text
all prior tests must remain green
```

Do not accept Step 5.1 if it breaks:

```text
H1
H2
H3
H4
MCP integration
KnowledgeProvider
CanonicalResolver
scenario/run synchronization
backend-driven UI activation
Neural Reasoning Map
Hypothesis Board
Knowledge Gaps
Next-Best Evidence
Validation
Learning
Domain Attribution
existing Zaki active-run binding
```

---

# 46. Definition of Done

```text
[ ] existing Step 5 behavior remains intact
[ ] no duplicate simulation engine exists
[ ] one managed worker owns each run
[ ] run lifecycle is explicit
[ ] every stage has explicit backend exit conditions
[ ] blocked stages remain on the same stage
[ ] NBE returns into same-stage retest
[ ] Play cannot bypass a block
[ ] Pause/Stop/Replay have authoritative semantics
[ ] watchdog explains stuck/blocked stages
[ ] finalization uses explicit terminal states

[ ] existing Zaki implementation is preserved
[ ] Zaki is stage-aware
[ ] Zaki explains blocked stages
[ ] Zaki explains stage exit conditions
[ ] Zaki explains pathway activation
[ ] Zaki explains H1–H4 evolution
[ ] Zaki explains knowledge gaps/NBE
[ ] Zaki explains synthesis
[ ] Zaki explains domain attribution
[ ] Zaki uses authoritative run revision
[ ] Zaki actions are governed
[ ] Zaki distinguishes execution from replay
[ ] Zaki never consumes Hidden Truth during reasoning
[ ] all prior Step 5 tests remain green
```

---

# Final Principle

> **Step 5 already synchronizes the UI correctly. Step 5.1 must not rebuild that work.**

> **Step 5.1 adds execution discipline to the simulation and deeper operational awareness to Zaki.**

> **The backend orchestrator runs the simulation. The existing UI visualizes it. Zaki explains it.**
