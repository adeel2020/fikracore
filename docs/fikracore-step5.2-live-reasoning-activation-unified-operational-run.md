# FikraCore Step 5.2 — Live Reasoning Activation & Unified Operational Run

## Purpose

Step 5 and Step 5.1 are already implemented and verified.

This document defines the **next additive step only**:

> **Activate the same FikraCore reasoning architecture for live operational incidents while preserving the existing offline simulation path.**

Step 5.2 must unify runtime execution so both:

```text
Offline Simulation
and
Live Operations
```

flow through the same authoritative reasoning architecture, contracts, visualization model, and Zaki Copilot.

The objective is **not** to create a separate live reasoning engine.

The objective is to create one unified operational run model that supports different sources:

```text
SIMULATION
LIVE_INTENT
```

while preserving source-specific ingestion and epistemic boundaries.

---

# 1. Existing Baseline — Already Complete

The following capabilities are already implemented and must be treated as stable:

```text
Step 5 backend-authoritative UI synchronization
scenario/run scoping
stale revision rejection
backend-driven light-up state
human-readable operational labels
atomic UI revision handling
reasoning pathways
connection reasons
H1–H4 hypothesis evolution
knowledge gaps
next-best evidence
domain attribution
validation
learning
Zaki active-run binding

Step 5.1 simulation orchestration
explicit run lifecycle
single managed worker per run
stage exit conditions
blocked-state handling
same-stage NBE retest
Play / Pause / Stop / Replay semantics
stage watchdog
terminal-state finalization
stage-aware Zaki
Zaki governed actions
replay awareness
hidden-truth isolation
```

Do not rebuild these.

---

# 2. Core Step 5.2 Goal

Unify the runtime architecture:

```text
OFFLINE
Selected Scenario
→ Simulation Evidence Provider
→ Unified Operational Run
→ Existing Reasoning Pipeline
→ Existing Neural Reasoning Map
→ Existing Zaki Copilot

LIVE
Intent Violation
→ Live Operational Evidence
→ Unified Operational Run
→ Existing Reasoning Pipeline
→ Existing Neural Reasoning Map
→ Existing Zaki Copilot
```

The two source modes should differ primarily in:

```text
how the run starts
where evidence comes from
whether hidden ground truth exists
how replay/evaluation works
```

They should **not** use separate reasoning engines.

---

# 3. Non-Negotiable Architectural Rule

There must be:

```text
ONE reasoning pipeline
ONE authoritative run contract
ONE stage model
ONE hypothesis model
ONE pathway model
ONE connection model
ONE Zaki context model
ONE UI projection model
```

Source-specific adapters are allowed.

Source-specific reasoning engines are not.

---

# 4. Unified Operational Run

Extend the existing `SimulationRun` only if needed.

Preferred direction:

```text
SimulationRun
→ generalized Unified Operational Run contract
```

Do not destructively rename working code unless the repository architecture makes it safe.

A compatibility alias is preferred if renaming is desired.

Recommended conceptual contract:

```ts
type OperationalRun = {
  run_id: string
  source_mode: "SIMULATION" | "LIVE_INTENT"
  scenario_id?: string
  intent_id?: string
  source_display_name: string
  run_status: "CREATED" | "INITIALIZING" | "RUNNING" | "BLOCKED" | "PAUSED" | "COMPLETED" | "FAILED" | "STOPPED"
  terminal_state?: "EXPLAINED" | "PARTIALLY_EXPLAINED" | "UNRESOLVED" | "INSUFFICIENT_EVIDENCE" | "CONFLICTING_EVIDENCE" | "MODEL_INSUFFICIENT"
  current_stage: string
  stage_status: string
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
  stage_block_reason?: string
  waiting_for?: string
  exit_conditions?: StageExitCondition[]
}
```

If the existing `SimulationRun` already contains most of this, extend it additively rather than duplicating it.

---

# 5. Source Mode Contract

Introduce or normalize:

```text
source_mode = SIMULATION
source_mode = LIVE_INTENT
```

Examples:

```text
SIMULATION
scenario_id = H4-WI-040

LIVE_INTENT
intent_id = INTENT-ENTERPRISE-APN-001
```

Only one of `scenario_id` or `intent_id` should be authoritative for a given source mode.

---

# 6. Offline Simulation Path — Preserve Existing Behavior

The current simulation behavior must remain unchanged.

```text
User selects scenario
→ backend creates/resolves run
→ simulator releases deterministic synthetic evidence progressively
→ reasoning pipeline consumes admitted evidence
→ stages execute
→ gaps / NBE / validation / action proceed
→ evaluator compares against hidden truth after reasoning
```

Critical rule:

```text
SIMULATOR HIDDEN TRUTH ≠ OPERATIONAL REASONING STATE
```

Hidden truth must never enter reasoning, Zaki, UI, learning, or telecombrain except through an explicitly governed post-run evaluator surface.

---

# 7. Live Operations Entry Point

Live reasoning begins from an **Intent Violation**.

Example:

```text
Intent:
Enterprise APN Success Rate ≥ 99.5%

Observed:
97.9%

Violation:
Enterprise APN success below target
```

The intent violation is trigger/context, not automatically root cause, causal evidence, hypothesis, or domain attribution.

---

# 8. Live Intent Contract

Recommended:

```ts
type LiveIntentViolation = {
  intent_id: string
  display_name: string
  service?: string
  scope?: string
  target: {
    metric: string
    operator: ">=" | "<=" | ">" | "<" | "==" | "!="
    threshold: number | string
  }
  observed: {
    value: number | string
    observed_at: string
  }
  severity?: string
  source_system?: string
  domain_hint?: string
  correlation_window?: {
    start: string
    end?: string
  }
  metadata?: Record<string, unknown>
}
```

Visible example:

```text
Enterprise APN Success Rate Below 99.5% Target
```

Do not lead with an opaque intent ID.

---

# 9. Live Run Activation

When a live intent violation is admitted:

```text
Intent Violation
→ Deduplicate / correlate with open run
→ Create or attach to OperationalRun
→ Initialize authoritative run
→ Admit initial evidence
→ Start existing reasoning orchestrator
```

The backend decides whether to create a new run or attach to an existing active run.

Do not create a new run for every individual alarm.

---

# 10. Live Run Correlation / Deduplication

Possible correlation dimensions:

```text
service
affected entity
subscriber segment
site / region
time window
shared dependency
intent type
existing incident key
existing ticket
change window
```

Recommended result:

```ts
type RunCorrelationDecision = {
  decision: "CREATE_NEW_RUN" | "ATTACH_TO_EXISTING_RUN"
  matched_run_id?: string
  confidence?: number
  reasons: string[]
}
```

Do not let the frontend decide this.

---

# 11. Live Evidence Adapter

Create a source adapter layer for live operational evidence.

```text
Live Source Systems
→ Live Evidence Adapters
→ Canonical Evidence Contract
→ OperationalRun
```

Possible evidence sources:

```text
Grafana / Prometheus metrics
Loki logs
Tempo traces
alarms
change records
tickets
topology / inventory
telecombrain knowledge
OSS/BSS
Kubernetes / NFVI
network telemetry
healthy signals
```

Do not bind reasoning directly to vendor-specific raw payloads.

---

# 12. Evidence Types

Reuse the existing vocabulary:

```text
ALARM
LOG
METRIC
KPI
TRACE
CHANGE
TICKET
HEALTHY_SIGNAL
RECOVERY
```

Do not create parallel live-only evidence contracts.

---

# 13. Live Evidence Admission

Not every incoming event should become reasoning evidence.

Use explicit admission states:

```text
RECEIVED
FILTERED
ADMITTED
REJECTED
SUPERSEDED
```

Recommended contract:

```ts
type EvidenceAdmission = {
  evidence_id: string
  run_id: string
  source_mode: "LIVE_INTENT"
  admission_state: "RECEIVED" | "FILTERED" | "ADMITTED" | "REJECTED" | "SUPERSEDED"
  reason: string
  revision: number
  sequence: number
}
```

The Neural Reasoning Map should use admitted evidence only.

---

# 14. Live Evidence Provenance

Every live evidence item must retain provenance:

```text
source system
source entity
event time
ingestion time
original reference
canonical entity
domain
service
confidence/quality if applicable
```

---

# 15. Evidence Time Semantics

Live reasoning must distinguish:

```text
event_time
ingestion_time
reasoning_time
```

Do not assume ingestion order equals event order.

Use event time for temporal causal analysis where appropriate and sequence/revision for transport consistency.

---

# 16. Live Run Stage Model

Reuse the existing 8 authoritative stages:

```text
TRIGGER
SIGNAL_FLOOD
CORRELATION
HYPOTHESIS_GENERATION
HYPOTHESIS_TESTING
KNOWLEDGE_GAP_CHECK
LEARNING_VALIDATION
ACTION
```

Do not create a live-specific stage model.

---

# 17. Stage Semantics for Live Operations

## TRIGGER

Exit when a valid live violation is admitted and operational scope is established.

## SIGNAL_FLOOD

Collect/admit the initial evidence window.

## CORRELATION

Correlate alarms, KPIs, logs, traces, changes, tickets, healthy signals, and shared service dependencies.

## HYPOTHESIS_GENERATION

Generate defensible candidates from admitted evidence, telecombrain knowledge, service dependencies, and validated historical knowledge.

## HYPOTHESIS_TESTING

Actively test candidate explanations.

## KNOWLEDGE_GAP_CHECK

Detect missing topology, dependency, telemetry, change context, failover state, or model insufficiency.

## LEARNING_VALIDATION

Governed human/domain validation.

## ACTION

Recommend permitted operational action and learning capture.

---

# 18. Live Runs Are Potentially Long-Lived

Unlike simulations, live incidents may remain open for extended periods.

Support new evidence arriving after initial stage entry:

```text
new contradiction
recovery signals
late logs
late ticket updates
change updates
human validation
```

Do not assume a live run is a short deterministic playback.

---

# 19. Re-Opening Reasoning Within a Live Run

New evidence may require retesting without creating a second run.

```text
new evidence admitted
→ determine affected pathways/hypotheses
→ persist revision
→ retest affected reasoning
→ update synthesis
```

Do not silently reset the run.

---

# 20. Live Run Blocking

Existing BLOCKED semantics remain valid.

For live mode, evidence may arrive automatically from a provider or via operator request.

The same-stage retest rule remains unchanged.

---

# 21. Next-Best Evidence in Live Mode

Reuse the existing NBE contract.

Live NBE can target:

```text
telemetry query
log query
trace query
topology lookup
inventory lookup
change lookup
ticket lookup
human validation
network tool invocation
```

Do not create a separate live NBE model.

---

# 22. Operational Evidence Providers

Introduce a provider registry if one does not already exist.

```ts
interface EvidenceProvider {
  provider_id: string
  display_name: string
  supports(request: EvidenceRequestState): boolean
  execute(request: EvidenceRequestState, context: OperationalRunContext): Promise<EvidenceProviderResult>
}
```

Examples:

```text
LGTMProvider
TelecombrainProvider
ChangeCalendarProvider
TicketProvider
TopologyProvider
NetworkToolProvider
```

Do not hardwire providers directly into hypothesis logic.

---

# 23. Provider Result Contract

```ts
type EvidenceProviderResult = {
  request_id: string
  status: "RETURNED" | "UNAVAILABLE" | "FAILED" | "TIMED_OUT"
  evidence?: EvidenceState[]
  reason?: string
  provider_id: string
  completed_at: string
}
```

Persist provider outcome before same-stage retest.

---

# 24. telecombrain Role

The existing operational `telecombrain` remains the production knowledge source.

Do not create another production graph.

Use it for topology, dependencies, service context, validated knowledge, canonical naming, and operational pages while preserving knowledge states such as CONFIRMED, INFERRED, CANDIDATE, REJECTED, STALE.

---

# 25. Grafana LGTM Role

Grafana LGTM is an operational evidence plane, not causal truth.

```text
Prometheus → metrics / KPIs
Loki → logs
Tempo → traces
Grafana → query / visual access
FikraCore → reasoning over admitted evidence
```

LGTM evidence can support or contradict hypotheses but does not independently determine root cause.

---

# 26. Live Intent to Evidence Routing

Add an intent/context router if not already present.

```text
Intent Violation
→ determine service/scope/entities
→ select relevant evidence providers
→ request initial evidence window
→ canonicalize
→ admit evidence
→ start reasoning
```

Backend-owned only.

---

# 27. Reasoning Pathway Activation — Live Mode

Reuse current pathways:

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

Activation remains evidence-driven.

Never activate a pathway because the intent name contains a keyword.

---

# 28. Unified Neural Reasoning Map

The existing map should work for both source modes.

Source indicator:

```text
LIVE OPERATIONS
or
OFFLINE SIMULATION
```

For live mode:

```text
Intent Violation
→ Evidence
→ Reasoning Pathways
→ Reasoning Core / Intelligence Synthesis
→ Hypotheses
→ Gaps / Validation / Learning
→ Domain Attribution
```

Do not introduce a second live-only visualization.

---

# 29. Unified Zaki Copilot

Zaki consumes the same unified run contract.

Additional live context:

```text
source_mode = LIVE_INTENT
intent_id
intent display name
live severity
service scope
latest live evidence time
```

Zaki should explicitly understand whether it is explaining offline simulation or live operations.

---

# 30. Zaki Live Questions

Zaki should answer:

```text
What intent was violated?
What changed first?
What evidence has arrived?
Which pathways are active?
What is the leading hypothesis?
What contradicts it?
What is still unknown?
What evidence should we collect next?
Why is this run blocked?
Which domain is currently primary?
What changed in the last revision?
Has the service started recovering?
What would change the conclusion?
```

All answers must come from authoritative run state.

---

# 31. Zaki Live Safety

Zaki must not invent evidence, alarms, changes, tickets, domain ownership, resolution, or root cause.

If evidence is unavailable, say it is unavailable.

---

# 32. Recovery Signals

Live operations require explicit recovery handling.

Reuse or add:

```text
RECOVERY
HEALTHY_SIGNAL
```

Recovery evidence should influence reasoning but must not automatically prove root cause.

---

# 33. Incident Closure

A live run should not close simply because a KPI recovers.

Closure should consider:

```text
service recovery
root-cause confidence
remaining contradiction
validation state
open knowledge gaps
action completion
operator policy
```

---

# 34. Live Run Terminal Semantics

Use existing terminal states:

```text
EXPLAINED
PARTIALLY_EXPLAINED
UNRESOLVED
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
MODEL_INSUFFICIENT
```

Do not force every live incident into EXPLAINED.

---

# 35. Human Validation

Validation remains governance, not hidden truth.

Persist validated operational facts with provenance.

---

# 36. Learning Boundary

Continue:

```text
Operational Evidence
→ Reasoning
→ Human Validation
→ Candidate Learning
→ Governance
→ Validated Knowledge
```

Do not learn directly from raw model output, unvalidated hypotheses, or simulator hidden truth.

---

# 37. Unified API Surface

Prefer extending existing endpoints.

Possible conceptual API:

```text
POST /api/v1/fikracore/runs
GET /api/v1/fikracore/runs/{run_id}/snapshot
GET /api/v1/fikracore/runs/{run_id}/events
POST /api/v1/fikracore/runs/{run_id}/actions
POST /api/v1/fikracore/live/intents/{intent_id}/activate
```

Do not replace working endpoints unnecessarily.

---

# 38. Run Creation Request

```ts
type CreateOperationalRunRequest =
  | { source_mode: "SIMULATION"; scenario_id: string }
  | { source_mode: "LIVE_INTENT"; intent_id: string }
```

---

# 39. Run Creation Response

```ts
type CreateOperationalRunResponse = {
  run_id: string
  source_mode: "SIMULATION" | "LIVE_INTENT"
  scenario_id?: string
  intent_id?: string
  run_status: string
  revision: number
}
```

---

# 40. Live Event Streaming

Reuse the existing event transport.

Recommended live events:

```text
intent_violation_admitted
evidence_received
evidence_admitted
evidence_rejected
pathway_activated
hypothesis_created
hypothesis_updated
gap_detected
evidence_requested
evidence_returned
synthesis_updated
domain_attribution_updated
recovery_signal_admitted
validation_requested
validation_completed
run_completed
```

Preserve run/source IDs, revision, sequence, timestamp.

---

# 41. Source Isolation

For simulation, scenario_id must match run.

For live, intent_id must match run context.

Reject stale or unrelated events.

---

# 42. Live Evidence Deduplication

Deduplicate using source event ID, canonical fingerprint, entity, event time, event type, or payload signature.

Do not let repeated ingestion artificially strengthen a hypothesis.

---

# 43. Evidence Quality

Optionally expose evidence quality where already feasible, such as source reliability, freshness, completeness, sampling quality, and corroboration.

Do not invent arbitrary numeric confidence.

---

# 44. Historical Pattern Pathway

Only use governed historical knowledge.

Recommended states:

```text
VALIDATED
CANDIDATE
STALE
REJECTED
```

Do not treat unresolved historical runs as certified patterns.

---

# 45. Live Impact Model

Service impact starts:

```text
UNKNOWN
```

and may progress:

```text
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Do not preload final blast radius at run creation.

---

# 46. Domain Attribution

Domain attribution remains downstream.

Do not mark a primary domain at intent creation.

Attribution should emerge from evidence, dependencies, hypothesis testing, synthesis, and validation.

---

# 47. Operational Run UI Changes

Make only minimal additive UI changes.

Add a source selector or badge:

```text
Live Operations
Offline Simulation
```

For live mode show active intent, service, severity, run status, current stage, and latest evidence timestamp.

Reuse all existing Step 5 panels.

---

# 48. Intent Picker

Live mode should support a backend-driven intent selector.

Examples:

```text
Enterprise APN Success Below Target
VoLTE Call Setup Success Below Target
5G Registration Success Below Target
Roaming Attach Success Below Target
Latency Above SLA
Packet Loss Above SLA
```

Do not hardcode intent behavior in frontend logic.

---

# 49. Source Switching

When switching between Simulation and Live, active run context must switch atomically.

Clear transient selected-object state and do not leak old evidence, hypotheses, gaps, attribution, or Zaki context.

---

# 50. Zaki Context Switching

Invalidate old Zaki context, hydrate the new run, and bind to the new revision.

Zaki must know whether context is SIMULATION or LIVE OPERATIONS.

---

# 51. Replay Semantics

Simulation replay remains unchanged.

Live replay replays persisted operational events only.

Do not re-query live providers or rerun reasoning during replay.

---

# 52. Evaluation Boundary

Simulation runs may use evaluator comparison against hidden truth.

Live runs do not.

For live runs, human validation, operational outcome, service recovery, and post-incident review may later provide evaluation signals.

---

# 53. Audit Trail

Persist:

```text
intent trigger
admitted evidence
filtered/rejected evidence
reasoning pathway activation
hypothesis creation/updates
confidence changes
knowledge gaps
NBE requests/results
validation
domain attribution
recovery
terminal state
learning decision
Zaki governed actions
```

---

# 54. Incident Storyteller Integration

The existing Incident Storyteller should consume the persisted unified run trace.

Recommended story:

```text
Intent Violation
→ First Evidence
→ Correlation
→ Candidate Causes
→ Tests
→ Knowledge Gaps
→ New Evidence
→ Convergence
→ Validation
→ Action
→ Recovery
```

Do not create a separate incident-story data model if the run trace already contains what is needed.

---

# 55. Customer Ticket Journey Integration

If a ticket is associated with a live run, link it to run, service impact, relevant evidence, investigation status, and validated explanation if available.

Do not force unrelated tickets into the run.

---

# 56. Failure Handling

Live provider failures must be explicit.

Examples:

```text
Prometheus unavailable
Loki query timed out
topology provider unavailable
ticket system unavailable
change calendar unavailable
```

Represent these as provider failure, knowledge/evidence gap, or NBE failure, not silent absence.

---

# 57. Graceful Degradation

Continue reasoning when one provider fails if sufficient other evidence exists.

Zaki should explain the missing source.

---

# 58. Security / Governance

Live actions must obey existing permissions.

At minimum distinguish:

```text
read evidence
request evidence
request validation
execute operational action
approve learning
```

Do not let Zaki or frontend bypass authorization.

---

# 59. Observability of FikraCore Itself

Instrument the platform:

```text
runs created
runs attached
active live runs
stage duration
blocked duration
provider latency
provider failures
evidence admitted/rejected
hypothesis update count
NBE request count
Zaki request latency
run completion state
```

Keep platform observability separate from incident evidence.

---

# 60. Primary Acceptance Scenario — Live Enterprise APN

```text
Intent:
Enterprise APN Success Rate ≥ 99.5%

Observed:
97.9%
```

Expected:

```text
1. Intent violation admitted
2. Live operational run created
3. Initial evidence providers queried
4. evidence normalized and admitted progressively
5. Operational Evidence pathway activates
6. Service Dependency activates if backend evidence supports it
7. hypotheses are generated
8. H1–H4 evolve from admitted evidence
9. a knowledge gap may block the run
10. NBE requests missing telemetry/topology
11. returned evidence retests the same stage
12. synthesis converges or remains insufficient
13. domain attribution emerges only when supported
14. Zaki explains each transition
15. recovery evidence may arrive
16. validation/action follows
17. terminal state persisted
```

No hidden truth is available.

---

# 61. Secondary Acceptance Scenario — Live VoLTE

Example:

```text
Intent:
VoLTE Call Setup Success ≥ target

Violation:
Call setup success degraded
```

Expected different evidence, pathways, hypotheses, provider queries, gaps, and attribution.

No intent-name hardcoding in the frontend.

---

# 62. Simulation Regression Scenario

Run an existing offline H4 scenario.

Expected:

```text
existing simulation behavior remains unchanged
hidden truth remains evaluator-only
existing replay remains unchanged
existing H1–H4 tests remain green
```

---

# 63. Backend Tests

```text
test_create_live_run_from_intent_violation
test_live_run_uses_existing_operational_run_model
test_live_run_preserves_existing_stage_model
test_intent_violation_is_trigger_not_root_cause
test_live_evidence_normalized_to_existing_contract
test_live_evidence_admission_backend_owned
test_duplicate_live_evidence_does_not_double_count
test_live_run_attach_to_existing_incident
test_live_run_create_new_when_not_correlated
test_live_provider_failure_is_explicit
test_live_nbe_retests_same_stage
test_live_run_blocking_preserves_current_stage
test_live_domain_attribution_delayed_until_supported
test_live_impact_starts_unknown
test_live_recovery_does_not_auto_confirm_root_cause
test_live_run_terminal_state_validated
test_live_run_has_no_hidden_truth
test_simulation_hidden_truth_still_isolated
test_live_and_simulation_use_same_reasoning_pipeline
test_live_zaki_context_scoped_to_run
test_live_zaki_does_not_invent_evidence
test_source_switch_rejects_stale_events
test_live_replay_does_not_requery_providers
```

---

# 64. Frontend Tests

```text
test_source_mode_switch
test_live_intent_selector_uses_backend_data
test_live_run_hydrates_existing_step5_panels
test_live_evidence_progressive_render
test_live_pathway_activation_backend_driven
test_live_hypotheses_progressive
test_live_gap_blocked_state
test_live_domain_attribution_delayed
test_live_zaki_context_header
test_live_to_simulation_switch_clears_context
test_simulation_to_live_switch_clears_context
test_live_replay_mode_indicator
```

---

# 65. Regression Gate

Before implementation:

```text
run full Step 5 baseline
run full Step 5.1 suite
record baseline
```

After implementation all previous tests must remain green.

Do not accept Step 5.2 if it breaks offline simulation, scenario/run scoping, stage orchestration, blocked-state behavior, same-stage retest, replay, H1–H4, KnowledgeProvider, telecombrain, canonicalization, Neural Reasoning Map, domain attribution, validation, learning, or Zaki Simulation Copilot.

---

# 66. Definition of Done

```text
[ ] live intent violations can create/attach to an operational run
[ ] simulation and live use the same reasoning pipeline
[ ] simulation and live use the same run contract
[ ] existing 8-stage model remains authoritative
[ ] live evidence is normalized into existing evidence contracts
[ ] evidence admission is backend-owned
[ ] duplicate evidence cannot falsely strengthen hypotheses
[ ] live provider failures are explicit
[ ] live NBE uses existing same-stage retest loop
[ ] live run can block without stage skipping
[ ] live impact starts UNKNOWN and evolves from evidence
[ ] live domain attribution is delayed until supported
[ ] recovery signals do not automatically prove RCA
[ ] live runs have no hidden ground truth
[ ] offline simulator hidden truth remains evaluator-only
[ ] existing Neural Reasoning Map works for both source modes
[ ] existing Step 5 UI is reused
[ ] Zaki knows whether context is Live or Simulation
[ ] Zaki explains live stage/evidence/hypothesis/gap state
[ ] replay remains read-only
[ ] incident trace is persisted
[ ] all Step 5 and Step 5.1 regression tests remain green
```

---

# Final Principle

> **FikraCore should have one reasoning brain, not a simulator brain and a live-operations brain.**

> **Simulation and Live Operations differ in how evidence enters the system — not in how FikraCore reasons about it.**

> **Intent violation starts the live investigation. Admitted operational evidence drives reasoning. The unified run records state. The existing UI visualizes it. Zaki explains it. Human validation governs what becomes trusted knowledge.**
