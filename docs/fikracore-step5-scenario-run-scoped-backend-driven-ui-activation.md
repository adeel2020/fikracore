# FikraCore Step 5 — Scenario/Run-Scoped Backend-Driven UI Activation

## Objective

Upgrade the existing Step 5 UI so every visible light-up state, connection, hypothesis state, knowledge gap, validation state, learning state, and domain attribution is driven by authoritative backend state for the currently selected `scenario_id` and `run_id`.

Preserve the existing Step 5 shell, routes, scenario selector, run controls, event stream, Neural Reasoning Map, Hypothesis Board, Knowledge Gaps, Next Best Evidence, Service Impact, Validation, Learning, Zaki, and existing H1–H4 reasoning logic.

This is a backend synchronization and contract-extension task.

## Core Principle

The frontend is a projection of backend reasoning state.

It must never infer or fabricate:
- active evidence
- active reasoning pathways
- pathway relevance
- connection relevance
- hypothesis confidence
- knowledge gaps
- synthesis state
- validation state
- learning readiness
- domain attribution

The selected scenario starts or selects a backend run. The backend run determines what the UI lights up.

Do not hardcode scenario-specific frontend rules.

## Scope by Scenario and Run

Every runtime object and every live event must be scoped by:

```text
scenario_id
run_id
revision
sequence
timestamp
```

For Live Operations, allow:

```text
intent_id
run_id
revision
sequence
timestamp
```

The frontend must accept updates only when they match the currently active investigation.

## Scenario Selection Behavior

When the user selects a scenario:

1. Resolve or create the authoritative `run_id`.
2. Mark the UI as loading/synchronizing.
3. Unsubscribe from the previous run stream.
4. Clear all transient visual state from the previous run:
   - active evidence
   - active pathways
   - highlighted connections
   - hypothesis selection
   - confidence history
   - knowledge gaps
   - pending evidence requests
   - synthesis state
   - validation state
   - learning state
   - domain attribution
   - reasoning focus
5. Fetch the authoritative snapshot for the selected run.
6. Hydrate the whole Step 5 UI atomically.
7. Subscribe only to events matching the active `scenario_id` and `run_id`.
8. Reject stale or duplicate events.

Never carry reasoning state from one scenario into another.

## Authoritative InvestigationRun Contract

Extend the existing contract additively.

```ts
type InvestigationRun = {
  scenario_id: string
  run_id: string
  stage: string

  revision: number
  sequence: number
  updated_at: string

  evidence: EvidenceState[]
  reasoning_pathways: ReasoningPathwayState[]
  connections: ReasoningConnectionState[]

  synthesis: IntelligenceSynthesisState
  hypotheses: HypothesisState[]
  knowledge_gaps: KnowledgeGapState[]
  next_best_evidence: EvidenceRequestState[]

  impact: ServiceImpactState
  validation: ValidationState
  learning: LearningState
  domain_attribution: DomainAttributionState
  reasoning_focus?: ReasoningFocusState
}
```

Do not remove existing fields.

## Runtime State Semantics

Use explicit states instead of inferring from missing data:

```text
DORMANT
DISCOVERED
ACTIVE
TESTING
SUPPORTING
CONTRADICTING
BLOCKED
NEEDS_EVIDENCE
WEAKENING
REJECTED
RESOLVED
CONFIRMED
```

Use only meaningful subsets per object.

## Evidence Contract

```ts
type EvidenceState = {
  evidence_id: string
  scenario_id: string
  run_id: string
  display_name: string

  evidence_type:
    | "ALARM"
    | "LOG"
    | "METRIC"
    | "KPI"
    | "TRACE"
    | "CHANGE"
    | "TICKET"
    | "HEALTHY_SIGNAL"
    | "RECOVERY"

  source_entity?: string
  domain?: string
  service?: string

  state: "DORMANT" | "DISCOVERED" | "ACTIVE" | "RESOLVED"

  event_time: string
  provenance?: object

  revision: number
  sequence: number
}
```

Use human-readable labels such as:

```text
BGP Adjacency Flapping on IP/MPLS Edge Router-07
```

not opaque IDs such as `EVT-102`.

## Reasoning Pathway Contract

```ts
type ReasoningPathwayState = {
  pathway_id: string
  scenario_id: string
  run_id: string

  display_name:
    | "Operational Evidence"
    | "Service Dependency"
    | "Subscriber Journey"
    | "Change & Configuration"
    | "Traffic & Capacity"
    | "Control & Signaling"
    | "Resilience & Failover"
    | "Historical Pattern"
    | "Knowledge Gap"

  state:
    | "DORMANT"
    | "DISCOVERED"
    | "ACTIVE"
    | "RESOLVED"
    | "REJECTED"

  activation_reason?: string
  evidence_ids: string[]
  hypothesis_ids: string[]

  revision: number
  sequence: number
}
```

The UI must never decide pathway activation from the scenario name. Activation must come from backend reasoning.

## Connection Contract

Every visible Evidence → Pathway or Pathway → Hypothesis connection must correspond to a backend relation.

```ts
type ReasoningConnectionState = {
  connection_id: string
  scenario_id: string
  run_id: string

  source_id: string
  target_id: string

  relation_type:
    | "CONTRIBUTES_TO"
    | "SUPPORTS"
    | "CONTRADICTS"
    | "REQUIRES"
    | "RESOLVES"
    | "ATTRIBUTES_TO"

  state:
    | "DORMANT"
    | "ACTIVE"
    | "SUPPORTING"
    | "CONTRADICTING"
    | "BLOCKED"
    | "REJECTED"
    | "CONFIRMED"

  reason: string
  evidence_ids?: string[]
  confidence_delta?: number

  revision: number
  sequence: number
}
```

No visible edge may exist without an authoritative connection object.

## Light-Up Rules

Keep the visual structure stable and change only runtime state:

```text
DORMANT → low-opacity conduit/node
DISCOVERED → short soft pulse
ACTIVE → cyan illumination
TESTING → animated cyan/amber pulse
SUPPORTING → green traveling pulse
CONTRADICTING → red traveling pulse
BLOCKED / NEEDS_EVIDENCE → amber
WEAKENING → decreasing brightness
REJECTED → grey / faded
CONFIRMED → stable green glow
```

Dormant nodes should stay faint rather than disappear if they are part of the stable mental map.

## Hypothesis Contract

Use visible identifiers `H1`, `H2`, `H3`, `H4`.

```ts
type HypothesisState = {
  hypothesis_id: string
  display_id: "H1" | "H2" | "H3" | "H4"
  display_name: string

  scenario_id: string
  run_id: string

  state:
    | "CANDIDATE"
    | "UNRANKED"
    | "RANKED"
    | "TESTING"
    | "SUPPORTED"
    | "WEAKENING"
    | "NEEDS_MORE_EVIDENCE"
    | "TESTING_NEW_EVIDENCE"
    | "REJECTED"
    | "ROOT_CANDIDATE"
    | "CONFIRMED"

  confidence?: number

  supporting_evidence: string[]
  contradicting_evidence: string[]
  missing_evidence: string[]

  revision: number
  sequence: number
}
```

Unknown confidence must render as `Unranked`, not `0%`.

## Intelligence Synthesis Contract

The Reasoning Core / Intelligence Synthesis state must come from the backend.

```ts
type IntelligenceSynthesisState = {
  scenario_id: string
  run_id: string

  state:
    | "INSUFFICIENT_EVIDENCE"
    | "PARTIAL"
    | "CONFLICTING_EVIDENCE"
    | "CONVERGING"
    | "STRONGLY_SUPPORTED"
    | "ROOT_CANDIDATE"
    | "MODEL_INSUFFICIENT"

  leading_hypothesis_id?: string
  active_pathway_ids: string[]

  dimensions?: {
    evidence_support?: string
    service_dependency_fit?: string
    temporal_fit?: string
    change_relevance?: string
    impact_alignment?: string
    traffic_capacity_fit?: string
    signaling_fit?: string
    historical_similarity?: string
    contradictions?: string
    knowledge_gaps?: number
    validation_state?: string
  }

  revision: number
  sequence: number
}
```

The frontend must not compute synthesis locally.

## Knowledge Gap Contract

```ts
type KnowledgeGapState = {
  gap_id: string
  scenario_id: string
  run_id: string
  display_name: string

  state:
    | "OPEN"
    | "NEEDS_EVIDENCE"
    | "IN_PROGRESS"
    | "RESOLVED"

  affected_hypothesis_ids: string[]
  affected_pathway_ids: string[]

  required_evidence?: string

  revision: number
  sequence: number
}
```

Use exact labels such as:

```text
Redundant MPLS Path Health Unknown
```

## Validation Contract

```ts
type ValidationState = {
  scenario_id: string
  run_id: string

  state:
    | "NOT_STARTED"
    | "PENDING"
    | "ACCEPTED"
    | "REJECTED"
    | "MODIFIED"
    | "NEED_MORE_EVIDENCE"

  display_name?: string
  reviewer_role?: string

  revision: number
  sequence: number
}
```

Expose the actual validated fact, e.g.:

```text
Transport Engineer Confirmed Router-07 as Primary Cause
```

## Domain Attribution Contract

```ts
type DomainAttributionState = {
  scenario_id: string
  run_id: string

  domains: {
    display_name: string
    role:
      | "PRIMARY"
      | "CONTRIBUTING"
      | "AFFECTED"
      | "INVOLVED"
      | "MONITOR_ONLY"
      | "NOT_RELEVANT"

    confidence?: number
    reason?: string
  }[]

  revision: number
  sequence: number
}
```

Do not mark a domain `PRIMARY` at run start. Domain attribution should become visible only when backend reasoning supports it.

## Snapshot API

Use one authoritative snapshot endpoint:

```text
GET /api/v1/fikracore/runs/{run_id}/snapshot
```

On initial load or reconnect:

1. fetch snapshot
2. validate `run_id`
3. replace current run state atomically
4. then subscribe to live updates

## Live Event Stream

Use the existing SSE/WebSocket mechanism.

Recommended event types:

```text
evidence_added
evidence_updated
connection_activated
connection_updated
pathway_discovered
pathway_activated
pathway_resolved
synthesis_updated
hypothesis_created
hypothesis_updated
confidence_changed
hypothesis_retested
gap_detected
gap_updated
evidence_requested
evidence_received
validation_requested
validation_updated
learning_candidate_created
learning_updated
domain_attribution_updated
reasoning_focus_changed
stage_changed
```

Each event must contain:

```ts
{
  scenario_id: string
  run_id: string
  revision: number
  sequence: number
  timestamp: string
  event_type: string
  payload: unknown
}
```

## Stale Update Protection

Frontend rules:

```text
if event.run_id !== activeRunId → ignore
if event.scenario_id !== activeScenarioId → ignore
if event.revision < currentRevision → ignore
if event.sequence <= lastAppliedSequence → ignore
```

Do not merge stale state.

## Atomic Synchronization

One accepted backend revision must update all surfaces together:

```text
Neural Reasoning Map
Hypothesis Board
Knowledge Gaps
Next Best Evidence
Service Impact
Validation
Learning
Domain Attribution
Investigation Timeline
Zaki
Stage Journey
```

No panel should show a different reasoning revision.

## Simulation Execution Behavior

Do not preload final state.

Correct model:

```text
stage executes on backend
→ backend persists result
→ backend emits stage/result events
→ frontend accepts revision
→ relevant nodes/connections light up
```

Do not show final hypothesis, final attribution, final impact, or final learning before the backend reaches those states.

## Replay Behavior

Replay must consume recorded backend events. Do not regenerate visual logic independently.

Replay should reproduce:

```text
same evidence admission
same pathway activation
same hypothesis evolution
same gaps
same synthesis progression
same attribution
```

for the recorded run.

## Zaki Synchronization

Zaki must consume the same active:

```text
scenario_id
run_id
revision
stage
evidence
pathways
hypotheses
gaps
synthesis
validation
domain attribution
```

Zaki should be able to answer:

```text
Why is this pathway active?
Why did H1 increase?
Which evidence contradicts H2?
What is blocking the current stage?
What evidence is needed next?
Why is IP Transport marked PRIMARY?
What would change the current conclusion?
```

Zaki must never infer from stale or different-run state.

## Human-Readable Naming Rule

Visible UI must always prefer:

```text
exact evidence name
exact pathway name
H1/H2/H3/H4 + exact title
exact knowledge gap name
exact validated fact
exact domain name
```

Opaque IDs remain for:

```text
API references
trace
audit
deduplication
debugging
```

## Preserve Existing Architecture

Do not replace or rewrite:

```text
H1 reasoning
H2 knowledge-gap logic
H3 learning logic
H4 what-if logic
telecombrain
KnowledgeProvider
CanonicalResolver
scenario catalog
scenario generator
existing Step 5 routing
existing Zaki bridge
```

Extend existing contracts only where required.

## Acceptance Test

Use at least two different scenarios.

### Scenario A — MPLS Edge Router Failure

Expected:

```text
relevant evidence lights
Service Dependency activates
Traffic & Capacity activates if evidence supports it
Resilience & Failover activates only when required
H1–H4 evolve from backend state
knowledge gap appears if backup path state is missing
domain attribution appears later
IP Transport becomes PRIMARY only after reasoning supports it
```

### Scenario B — VoLTE Call Setup Degradation

Expected:

```text
different evidence
different pathway activation
different hypothesis candidates
different gaps
different attribution
```

The frontend code must not contain scenario-specific activation rules.

## Required Tests

Backend:

```text
test_snapshot_scoped_to_run
test_events_scoped_to_scenario_and_run
test_pathway_activation_backend_owned
test_connection_reason_present
test_hypothesis_confidence_backend_owned
test_gap_exact_display_name
test_validation_exact_display_name
test_domain_attribution_delayed_until_supported
test_duplicate_event_rejected
test_stale_revision_rejected
test_two_subscribers_do_not_advance_run
```

Frontend:

```text
test_scenario_switch_clears_previous_run
test_snapshot_atomically_hydrates_ui
test_wrong_run_event_ignored
test_stale_revision_ignored
test_dormant_pathway_dimmed
test_active_pathway_lit
test_support_connection_green
test_contradiction_connection_red
test_gap_amber
test_rejected_hypothesis_faded
test_h1_h4_visible
test_all_panels_share_revision
test_zaki_uses_active_run
```

## Definition of Done

```text
[ ] every light-up state is backend-driven
[ ] every visual is scoped by active scenario_id/run_id
[ ] stale state cannot leak between scenarios
[ ] no scenario-specific frontend activation logic exists
[ ] every visible connection has a backend reason
[ ] all panels use the same revision
[ ] simulation state appears progressively
[ ] final conclusions do not appear early
[ ] Zaki uses the same authoritative run state
[ ] human-readable labels are used everywhere
[ ] existing H1–H4 behavior remains intact
```

## Final Rule

> The selected scenario determines the run context.  
> The backend reasoning determines what becomes active.  
> The frontend only visualizes that state.
