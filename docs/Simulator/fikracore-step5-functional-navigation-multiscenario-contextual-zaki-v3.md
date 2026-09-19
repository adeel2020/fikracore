# FikraCore Step 5 UI — Functional Navigation, Multi-Scenario Support & Contextual Zaki

## Purpose

Fix the Step 5 Simulator UI so that:

- top-level tabs switch to real capability workspaces;
- all clickable links execute meaningful actions;
- the UI discovers and supports multiple scenarios from the backend;
- scenario/run context is preserved across workspaces;
- Zaki produces grounded, context-aware responses based on the active scenario, workspace, selected network context, and response depth.

The UI must be a functional interface over the validated FikraCore capability layer, not a static mockup.

> **A capability tab must change capability state, not just color.**

> **Every clickable UI element must navigate, inspect, filter, focus, or execute a real backend action.**

---

# 1. Primary Workspaces

Implement these top-level workspaces:

```text
Investigate
Discover
Learn
Predict
Knowledge Core
Simulator Lab
Benchmarks
```

Each workspace must have:

```text
its own route
its own component tree
its own backend capability binding
loading / ready / empty / error / stale states
shared scenario/run context
```

---

# 2. Workspace Responsibilities

## Investigate

Purpose:

```text
What happened and why?
```

Render:

```text
Live Event Stream
Causal Graph
Hypothesis Evolution
Reasoning Activity
Service Impact
Evidence
Current Root Candidate
Terminal State
```

Backend:

```text
H1 / investigate capability
current simulation-run reasoning state
```

---

## Discover

Purpose:

```text
What do we not know?
```

Render:

```text
Knowledge Gap Summary
MODEL_INSUFFICIENT state
Known vs Unknown topology
Unknown Boundaries
Missing Dependency Edges
Candidate Relationships
Next-Best Evidence
Gap Priority
```

Backend:

```text
H2 / discover capability
knowledge-gap state
```

---

## Learn

Purpose:

```text
What validated knowledge should we retain?
```

Render:

```text
Candidate Knowledge
Learning Units
SME / HITL Validation
Accepted / Rejected / Modified status
Promotion State
Rollback State
Before vs After comparison
Future Incident Improvement
```

Backend:

```text
H3 / learn capability
candidate / promotion state
```

---

## Predict

Purpose:

```text
What could fail and what should we protect?
```

Render:

```text
What-If Trigger
Forward Propagation
Affected Services
Blast Radius
Critical Failure Surface
Failover Risk
Capacity Risk
Change Risk
Mitigation Comparison
Re-Simulate
```

Backend:

```text
H4 / predict capability
what-if state
```

---

## Knowledge Core

Purpose:

```text
What does FikraCore know?
```

Render:

```text
Knowledge Summary
Domain Coverage
Service Coverage
Knowledge States
Cross-Domain Coverage
Top Gaps
Orphans
Stale Knowledge
Recently Learned Knowledge
```

Backend:

```text
Step 4.7 knowledge inventory
live telecombrain
```

---

## Simulator Lab

Purpose:

```text
Select, run, replay, and compare scenarios.
```

Render:

```text
Scenario Library
Scenario Details
Run Controls
Replay
Pause / Resume
Simulation Speed
Compare Runs
Scenario Timeline
Current Run Status
```

Backend:

```text
scenario registry
simulation lifecycle
```

---

## Benchmarks

Purpose:

```text
Measure FikraCore performance.
```

Render:

```text
H1 Results
H2 Results
H3 Results
H4 Results
Live MCP Parity
Knowledge Inventory Validation
Regression Suite
Confidence Calibration
Metric Trends
```

Backend:

```text
benchmark artifacts
parity reports
regression reports
```

---

# 3. Workspace Routing

Recommended routes:

```text
/simulator/investigate
/simulator/discover
/simulator/learn
/simulator/predict
/simulator/knowledge
/simulator/lab
/simulator/benchmarks
```

Use query parameters for active context:

```text
?scenario=SCN-017&run=RUN-102&entity=tr-01
```

Requirements:

```text
URL changes when workspace changes
active tab reflects URL
browser Back/Forward works
deep links work
```

---

# 4. Shared Application State

Use one shared application store.

```ts
interface FikraCoreAppState {
  activeWorkspace: Workspace;

  scenarioRegistry: ScenarioRegistryState;

  scenarioId: string | null;
  runId: string | null;

  selectedEntityId: string | null;
  selectedServiceId: string | null;
  selectedHypothesisId: string | null;
  selectedGapId: string | null;
  selectedEvidenceId: string | null;

  simulationStatus: SimulationStatus;
  providerStatus: ProviderStatus;

  investigate: InvestigateState;
  discover: DiscoverState;
  learn: LearnState;
  predict: PredictState;
  knowledge: KnowledgeState;
  simulator: SimulatorState;
  benchmarks: BenchmarkState;

  zaki: ZakiContextState;
}
```

Do not duplicate `scenarioId`, `runId`, or selected entity state inside individual components.

---

# 5. Multi-Scenario Backend Discovery

The UI must support **all scenarios returned by the backend registry**.

`SCN-001` is only the deterministic acceptance scenario.

The frontend must not hard-code:

```text
scenario IDs
scenario names
stage
domains
services
topology
metrics
expected results
```

Use or add a backend endpoint equivalent to:

```text
GET /api/v1/fikracore/scenarios
```

Recommended scenario contract:

```json
{
  "id": "SCN-017",
  "display_name": "Shared Transport Failure",
  "aliases": ["transport outage", "shared path failure"],
  "stage": "H1",
  "capabilities": ["investigate", "discover", "predict"],
  "domains": ["Mobile Core", "Transport"],
  "services": ["4G LTE Data"],
  "difficulty": "L3",
  "status": "READY",
  "source": "benchmark-registry"
}
```

Reuse the existing canonical scenario registry rather than creating a second one.

---

# 6. Scenario Selector

The selector must support:

```text
search
filter by stage
filter by domain
filter by service
filter by capability
sort
refresh
select
```

Example:

```text
Search: transport

SCN-017       Shared Transport Failure
H2-GAP-011    Missing Transport Dependency
H4-WI-001     MPLS Edge Router Failure
```

---

# 7. Scenario Capability Availability

Not every scenario must support every capability.

Scenario metadata should define availability.

Example:

```json
{
  "scenario_id": "SCN-017",
  "capabilities": {
    "investigate": true,
    "discover": true,
    "learn": false,
    "predict": true
  }
}
```

If unavailable:

```text
disable the action/tab
show the reason
do not render fabricated empty output
```

---

# 8. Scenario Switching

When a scenario changes:

```text
1. detach old scenario-specific subscriptions
2. clear stale run-specific state
3. fetch scenario metadata
4. fetch topology/context
5. fetch available capabilities
6. fetch current or last run
7. reconnect live stream if applicable
8. refresh all live statistics
9. update Zaki context
```

Never display old scenario data under a new scenario heading.

---

# 9. Scenario and Run Separation

Model:

```text
Scenario Definition
      ↓
Run 1
Run 2
Run 3
```

Support:

```text
open active run
start new run
view previous runs
replay completed run
compare runs
```

---

# 10. Scenario-Specific Live State

The selected scenario/run controls:

```text
event count
alarm count
metric count
hypotheses
confidence
service impact
affected users
blast radius
knowledge gaps
next-best actions
learning candidates
simulation stage
elapsed time
topology
```

No fallback to SCN-001 values.

---

# 11. Backend Capability Binding

Map each workspace to the existing validated capability layer.

```text
Investigate   → investigate
Discover      → discover
Learn         → learn
Predict       → predict
Knowledge     → inspect knowledge
Simulator Lab → simulate
Benchmarks    → benchmark / report
```

If HTTP routes do not yet exist, add only:

```text
controllers
serializers
API adapters
state endpoints
```

Do not rewrite validated H1–H4 reasoning.

---

# 12. No UI-Specific Reasoning

Forbidden:

```text
UI-specific RCA logic
UI-specific gap detection
UI-specific learning decisions
UI-specific blast-radius calculation
UI-side confidence calculation
```

The frontend renders capability output.

---

# 13. Contextual Links

Every visible link must have a real action.

## View All Events

```text
open event drawer/workspace
preserve scenario/run
show all events
allow filter + click-to-focus
```

## View Evidence

```text
show supporting evidence
show contradicting evidence
show missing evidence
show provenance
```

## View Affected Map

Show:

```text
affected services
regions if real geography exists
customer segments
blast-radius path
```

If geography is unavailable, show logical service-impact topology.

## Search Knowledge Core

```text
navigate to Knowledge Core
preserve scenario/run
pre-filter relevant entities/gaps
```

## View All Hypotheses

Show:

```text
active hypotheses
rejected hypotheses
rank history
confidence history
evidence mapping
```

---

# 14. Cross-Panel Synchronization

Selecting any operational object must update relevant panels.

Example:

```text
Select Transport Router-01
        ↓
Graph highlights entity
Event stream focuses related events
Hypothesis panel highlights linked hypotheses
Discover filters related gaps
Next-best evidence filters relevant actions
Zaki receives selected entity context
```

Use one shared selected entity ID.

---

# 15. Next-Best-Evidence Actions

`Run` must execute a real backend action.

State:

```text
READY
→ RUNNING
→ COMPLETED / FAILED
```

Returned evidence must update:

```text
event stream
hypothesis evolution
reasoning tasks
knowledge gap state
```

---

# 16. Contextual Zaki AI Copilot

Zaki must produce a response based on the user's **current operational context**, not from the whole brain indiscriminately.

Zaki context should include:

```text
selected scenario
selected run
active workspace
current simulation stage
selected domain
selected service
selected entity
selected hypothesis
selected knowledge gap
selected evidence
current impact
current unknowns
current next-best actions
knowledge source
user response level
```

---

# 17. Zaki Context Envelope

Recommended request envelope:

```json
{
  "scenario_id": "SCN-017",
  "scenario_name": "Shared Transport Failure",
  "run_id": "RUN-102",

  "workspace": "investigate",
  "simulation_stage": "hypothesis_testing",

  "response_level": "engineer",

  "selected_domain": "Transport",
  "selected_service": "4G LTE Data",
  "selected_entity_id": "tr-01",
  "selected_hypothesis_id": "HYP-001",
  "selected_gap_id": null,
  "selected_evidence_id": null,

  "knowledge_source": "live_telecombrain"
}
```

The backend should enrich this context with current structured capability state before passing it to the LLM.

---

# 18. Zaki Workspace Awareness

The same question must be interpreted differently depending on active workspace.

Example user question:

```text
"What is happening?"
```

Expected focus:

```text
Investigate
→ symptoms, leading hypothesis, evidence, confidence

Discover
→ unknown boundary, knowledge gap, next-best evidence

Learn
→ candidate knowledge, validation status, future improvement

Predict
→ propagation, blast radius, resilience risk

Knowledge Core
→ known coverage, stale knowledge, gaps

Simulator Lab
→ scenario/run status and simulation progress

Benchmarks
→ performance metrics and benchmark outcome
```

---

# 19. Zaki Response Levels

Support explicit response depth:

```text
Executive
Operator
Engineer
Deep Technical
```

Suggested parameter:

```text
response_level
```

### Executive

Focus on:

```text
service impact
business/customer effect
high-level cause/risk
recommended action
```

### Operator

Focus on:

```text
current state
leading hypothesis
operational evidence
next action
```

### Engineer

Focus on:

```text
causal path
supporting/contradicting evidence
confidence
knowledge gaps
dependency reasoning
```

### Deep Technical

Focus on:

```text
canonical entities
relationship path
evidence provenance
raw reasoning states
confidence components
technical limitations
```

---

# 20. Zaki Auto-Context

The operator should not need to repeat context.

Examples:

```text
user selects tr-01
→ Zaki selected_entity_id becomes tr-01

user opens Discover
→ Zaki workspace becomes discover

user selects KG-01
→ Zaki selected_gap_id becomes KG-01

user switches scenario
→ all prior scenario-specific Zaki context is cleared and replaced
```

---

# 21. Zaki Grounding Rules

Zaki may:

```text
explain
summarize
compare
clarify
navigate
orchestrate permitted actions
```

Zaki must not independently create:

```text
topology
root cause
confidence
blast radius
knowledge state
confirmed relationships
learning promotion
Hidden Truth
```

These remain FikraCore capability outputs.

---

# 22. Zaki Uncertainty Preservation

Zaki must preserve engine state.

If backend says:

```text
MODEL_INSUFFICIENT
```

Zaki must not phrase the answer as a confirmed root cause.

If hypothesis state is:

```text
SUPPORTED
```

Zaki must not say:

```text
CONFIRMED
```

---

# 23. Zaki Navigation

Zaki should use the same workspace router.

Examples:

```text
"Show the knowledge gap."
→ Discover

"Show blast radius."
→ Predict

"What did we learn?"
→ Learn

"Show what you know about Transport."
→ Knowledge Core

"Open this scenario."
→ Simulator Lab / selected scenario
```

---

# 24. Floating Zaki UI

Keep the floating copilot.

## Resting Mode

```text
small holographic orb
online beacon
meaningful status
quick-expand
```

Suggested status states:

```text
Idle
Observing
Reasoning
Needs Evidence
Recommendation Ready
Insufficient Evidence
```

## Expanded Mode

Show:

```text
Current Scenario
Current Workspace
Simulation Stage
Leading Hypothesis / Current Risk
Selected Entity / Gap
Current Unknowns
Recommended Next Action
Contextual Suggestion Chips
Conversation History
```

---

# 25. Contextual Suggestion Chips

Generate chips dynamically from current state.

Examples in Investigate:

```text
Why is Transport ranked first?
What contradicts this hypothesis?
What evidence is missing?
```

Discover:

```text
Where does known topology stop?
What evidence can resolve this gap?
Why is this relationship only a candidate?
```

Learn:

```text
What knowledge is awaiting validation?
What improved after learning?
Can this knowledge be promoted safely?
```

Predict:

```text
Show the blast radius.
Why does failover fail?
Which mitigation reduces the risk most?
```

---

# 26. Loading, Empty, Error & Stale States

Every workspace must support:

```text
LOADING
READY
EMPTY
ERROR
STALE
```

Examples:

```text
No unresolved knowledge gaps for this run.
No learning candidates available yet.
Knowledge provider unavailable — Retry.
```

Do not keep another workspace's data visible while loading.

---

# 27. Active Workspace Visibility

Each view must identify itself clearly.

Example:

```text
DISCOVER
Knowledge Gap & Unknown Boundary Analysis

Scenario: SCN-017
Run: RUN-102
```

---

# 28. Backend Source Visibility

Show:

```text
Knowledge Source
Simulation Run
Last Update
```

Example:

```text
telecombrain MCP: LIVE
Run: RUN-102
Updated: 10:43:16
```

---

# 29. Semantic Navigation Controls

Use proper:

```text
nav
button
router links
anchors
```

Do not use decorative `div` click targets for primary navigation.

If functionality is unavailable:

```text
disable control
show reason / Coming Soon
```

No fake links.

---

# 30. Suggested Scenario Library

Simulator Lab should display:

```text
Scenario
Stage
Domains
Services
Capabilities
Difficulty
Last Run
Status
```

Actions:

```text
Open
Run
Replay
Compare
Present
```

---

# 31. Functional Navigation Tests

Validate:

```text
Investigate → Discover
Discover → Learn
Learn → Predict
Predict → Knowledge
Knowledge → Simulator
Simulator → Benchmarks
Benchmarks → Investigate
```

For each verify:

```text
active tab
route
component
backend binding
context preservation
```

---

# 32. Multi-Scenario Tests

Add:

```text
test_scenario_registry_loaded_from_backend
test_multiple_scenarios_supported
test_no_hardcoded_scn001_dependency
test_scenario_search
test_scenario_filter_by_stage
test_scenario_filter_by_domain
test_scenario_filter_by_service
test_scenario_filter_by_capability
test_scenario_alias_resolution
test_scenario_switch_clears_stale_state
test_scenario_switch_updates_topology
test_scenario_switch_updates_live_stats
test_scenario_capability_availability
test_multiple_runs_per_scenario
```

---

# 33. Zaki Context Tests

Add:

```text
test_zaki_receives_active_scenario
test_zaki_receives_active_run
test_zaki_receives_active_workspace
test_zaki_receives_selected_entity
test_zaki_receives_selected_hypothesis
test_zaki_receives_selected_gap
test_zaki_context_resets_on_scenario_change
test_zaki_workspace_changes_response_focus
test_zaki_response_level_executive
test_zaki_response_level_operator
test_zaki_response_level_engineer
test_zaki_response_level_deep_technical
test_zaki_preserves_model_insufficient
test_zaki_does_not_invent_confidence
test_zaki_navigation_uses_shared_router
```

---

# 34. Contextual Action Tests

Test:

```text
View all events
View Evidence
View Affected Map
Search Knowledge Core
View all hypotheses
Run next-best evidence
Inspect Candidate
What-If
Zaki navigation
```

Every action must create an observable state change.

---

# 35. Regression Safety

Do not break:

```text
H1
H2
H3
H4
Step 4.5
Step 4.6
Step 4.7
simulation lifecycle
scenario resolver
Zaki grounding
Hidden Truth isolation
```

---

# 36. Definition of Done

Complete when:

```text
[ ] all seven top-level workspaces are functional
[ ] workspace switching changes real capability state
[ ] routes and active tabs remain synchronized

[ ] scenario registry is backend-discovered
[ ] multiple scenarios can be searched and filtered
[ ] scenario switching refreshes topology and live state
[ ] capability availability is scenario-aware
[ ] multiple runs are supported per scenario

[ ] shared scenario/run context is preserved across workspaces
[ ] stale scenario data is cleared correctly

[ ] all visible links/actions are functional
[ ] no fake clickable elements remain

[ ] Zaki receives scenario, run, workspace, stage, and selection context
[ ] Zaki supports Executive / Operator / Engineer / Deep Technical response levels
[ ] Zaki response focus changes by workspace
[ ] Zaki auto-context updates on user selection
[ ] Zaki preserves uncertainty and capability states
[ ] Zaki never invents operational truth

[ ] no UI-specific reasoning implementation exists
[ ] all prior reasoning and integration regressions remain green
```

---

# 37. Acceptance Walkthrough

## Multi-Scenario Validation

```text
1. Load the backend scenario registry.
2. Confirm multiple scenarios are visible.
3. Search by scenario name or alias.
4. Filter by H1 / H2 / H3 / H4.
5. Filter by domain and service.
6. Select a non-SCN-001 scenario.
7. Confirm topology, statistics, capabilities, and Zaki context update.
8. Select another scenario and confirm stale state disappears.
```

## Capability Navigation

Using any scenario with applicable capabilities:

```text
1. Open Investigate.
2. Confirm incident workspace.
3. Open Discover.
4. Confirm knowledge-gap workspace.
5. Open Learn.
6. Confirm learning workspace.
7. Open Predict.
8. Confirm forward What-If workspace.
9. Open Knowledge Core.
10. Confirm live knowledge inventory.
11. Open Simulator Lab.
12. Confirm scenario/run controls.
13. Open Benchmarks.
14. Confirm benchmark results.
15. Use browser Back/Forward and verify context restoration.
```

## Zaki Context Validation

```text
1. Select a Transport entity.
2. Ask "What is happening?"
3. Confirm response is scoped to the selected scenario/entity.
4. Switch to Discover.
5. Ask the same question.
6. Confirm response focuses on unknowns/gaps.
7. Change response level from Executive to Engineer.
8. Confirm depth changes without changing underlying facts.
9. Switch scenario.
10. Confirm Zaki does not reference the previous scenario.
```

---

# Final Principle

> **FikraCore provides the intelligence. The UI exposes capability state. Zaki explains that state in the user's current operational context.**

And:

> **Scenario + Run + Workspace + Selection + Response Level = Zaki Context.**
