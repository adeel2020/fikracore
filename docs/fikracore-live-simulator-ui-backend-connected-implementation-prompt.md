# FikraCore Live Simulator UI — Backend-Connected Implementation Prompt

## Objective

Build the **FikraCore Live Simulator UI** to match the attached reference design while ensuring that every visible metric, scenario state, network element, hypothesis, timeline event, knowledge gap, service-impact value, and Zaki response is driven by the real backend.

The UI must not use static mock values once connected to the backend.

The experience should feel like a **live telecom reasoning cockpit** where the operator can select a scenario, start or replay a simulation, and watch FikraCore continuously update:

```text
events
correlations
hypotheses
causal paths
service impact
knowledge gaps
next-best evidence
learning capture
simulation stage
```

The primary principle is:

> **The UI is a live view of FikraCore state, not a static visualization.**

---

# 1. Target Experience

The screen should closely follow the attached reference design.

Primary regions:

```text
Top Header / Scenario Context
Primary Navigation
Live Simulation Journey
Unified Live Event Stream
Telecom Network Causal Graph
Hypothesis Evolution
What FikraCore Is Doing Now
Service Impact / Blast Radius
Knowledge Gap / Unknown Boundary
Next-Best Evidence / Intelligence Actions
Learning Capture
Floating Zaki AI Copilot
```

The layout must stay dense but uncluttered.

---

# 2. Core Product Behavior

The UI must support both:

```text
SELECTED SCENARIO MODE
LIVE SIMULATION MODE
```

A user must be able to:

```text
select a scenario
load scenario metadata
start simulation
pause simulation
resume simulation
stop simulation
replay simulation
change simulation speed
inspect entities
inspect evidence
inspect hypotheses
trigger next-best-evidence actions
open Zaki
```

---

# 3. Backend-First Rule

Do not hard-code operational results into React components.

All live data must come from backend APIs or a live streaming channel.

Frontend components must consume structured state.

Recommended flow:

```text
FikraCore Backend
      ↓
Scenario / Simulation API
      ↓
WebSocket / SSE Live State Stream
      ↓
Frontend State Store
      ↓
UI Components
```

---

# 4. Recommended Backend Integration

Use:

```text
REST
```

for:

```text
scenario list
scenario metadata
initial topology snapshot
initial simulation state
historical/replay state
knowledge summary
entity details
```

Use:

```text
WebSocket
```

or:

```text
Server-Sent Events
```

for:

```text
live event stream
simulation-stage progression
entity-state updates
relationship-state updates
hypothesis confidence updates
knowledge-gap updates
service-impact changes
reasoning-task updates
learning updates
Zaki context changes
```

Prefer WebSocket if bidirectional live actions are required.

---

# 5. Suggested API Surface

Adapt to the existing FikraCore backend conventions.

Recommended endpoints:

```text
GET  /api/v1/fikracore/scenarios
GET  /api/v1/fikracore/scenarios/{scenario_id}
GET  /api/v1/fikracore/scenarios/{scenario_id}/topology
GET  /api/v1/fikracore/scenarios/{scenario_id}/state

POST /api/v1/fikracore/simulations
GET  /api/v1/fikracore/simulations/{run_id}
POST /api/v1/fikracore/simulations/{run_id}/pause
POST /api/v1/fikracore/simulations/{run_id}/resume
POST /api/v1/fikracore/simulations/{run_id}/stop
POST /api/v1/fikracore/simulations/{run_id}/replay

GET  /api/v1/fikracore/simulations/{run_id}/events
GET  /api/v1/fikracore/simulations/{run_id}/hypotheses
GET  /api/v1/fikracore/simulations/{run_id}/impact
GET  /api/v1/fikracore/simulations/{run_id}/knowledge-gaps
GET  /api/v1/fikracore/simulations/{run_id}/next-best-evidence

WS   /api/v1/fikracore/simulations/{run_id}/live

POST /api/v1/fikracore/simulations/{run_id}/actions
POST /api/v1/fikracore/zaki/chat
```

---

# 6. Scenario Selection

The scenario selector in the top bar must be backend-driven.

Example UI:

```text
[SCN-001] SGi Throughput Degradation & MTU Blackhole
```

On scenario selection:

```text
1. fetch scenario metadata
2. fetch topology snapshot
3. fetch current or last run state
4. update service/domain badges
5. reset stale UI state
```

Scenario metadata should include:

```json
{
  "id": "SCN-001",
  "display_name": "SGi Throughput Degradation & MTU Blackhole",
  "stage": "H4",
  "service": "4G LTE Data EPC",
  "domains": ["RAN", "Transport", "Mobile Core", "IMS", "OSS/BSS"],
  "status": "READY"
}
```

---

# 7. Simulation Lifecycle

When the user clicks Run:

```text
POST /api/v1/fikracore/simulations
```

Example request:

```json
{
  "scenario_id": "SCN-001",
  "speed": 1.0,
  "mode": "live"
}
```

Expected response:

```json
{
  "run_id": "RUN-20260911-001",
  "scenario_id": "SCN-001",
  "status": "RUNNING",
  "started_at": "2026-09-11T18:00:00Z"
}
```

After receiving `run_id`, connect to:

```text
WS /api/v1/fikracore/simulations/{run_id}/live
```

---

# 8. Live Simulation Journey

The horizontal journey must be dynamic.

Stages:

```text
1 Trigger
2 Signal Flood
3 Correlation
4 Hypothesis Testing
5 Knowledge Gap Check
6 Learning / Validation
7 Action / Recommendation
```

Each stage must receive:

```text
state
start time
end time
progress
summary
```

Example event:

```json
{
  "type": "simulation_stage",
  "stage": "correlation",
  "index": 3,
  "status": "ACTIVE",
  "summary": "Linking events across Transport and Mobile Core"
}
```

UI states:

```text
PENDING
ACTIVE
COMPLETED
FAILED
```

---

# 9. Live Simulation Timer

The top bar timer must use the backend run start time.

Display:

```text
Simulation Running
00:02:34
```

Do not increment a local timer without reconciling against backend timestamps.

Support:

```text
pause
resume
stop
simulation speed
```

---

# 10. Unified Live Event Stream

The left event stream must be live.

Event categories:

```text
alarm
metric
log
trace
change
ticket
action
hypothesis
```

Example event payload:

```json
{
  "type": "event",
  "event_id": "EVT-10028",
  "timestamp": "2026-09-11T10:42:01Z",
  "category": "alarm",
  "severity": "critical",
  "title": "SGi Path RTT Degradation >150ms",
  "domain": "Mobile Core",
  "entity_id": "sgw-01",
  "state": "OBSERVED"
}
```

The event stream must:

```text
append in timestamp order
highlight new events
allow filtering
preserve scroll position
support click-to-focus
```

---

# 11. Telecom Network Causal Graph

The center graph must be driven from live topology and reasoning state.

Domains shown in the reference design:

```text
RAN
Transport
Mobile Core
IMS
OSS / BSS
Customer Impact
```

Each entity should have:

```text
entity_id
display_name
domain
entity_type
health_state
reasoning_state
knowledge_state
confidence
impact_state
```

Example:

```json
{
  "entity_id": "tr-01",
  "display_name": "Transport Router-01",
  "domain": "Transport",
  "health_state": "DEGRADED",
  "reasoning_state": "ROOT_CANDIDATE",
  "confidence": 0.942
}
```

---

# 12. Graph States

Render these states:

```text
Healthy
Symptom / Impact
Root Candidate
Unknown
Confirmed
Rejected
Candidate Relationship
```

Graph state must update in real time when backend messages arrive.

---

# 13. Relationship Updates

Relationship state payload:

```json
{
  "type": "relationship_state",
  "source": "tr-01",
  "target": "sgw-01",
  "relationship": "ROUTES_THROUGH",
  "state": "CONFIRMED",
  "causal": true,
  "confidence": 0.94
}
```

Visual mappings:

```text
solid bright path   = confirmed
red causal line     = active failure path
dashed amber line   = candidate / unknown
muted blue line     = healthy dependency
grey faded line     = rejected
```

---

# 14. Confirmed Causal Path

The lower edge of the graph should show a live causal path summary.

Example:

```text
Confirmed Causal Path:
Transport Router-01
→ Serving Gateway-01
→ Packet Gateway-01
→ 4G LTE Data EPC

Path Confidence: 94.2%
```

This must be derived from backend structured state.

---

# 15. Hypothesis Evolution

The right panel must continuously update.

Payload example:

```json
{
  "type": "hypothesis_update",
  "hypothesis_id": "HYP-001",
  "rank": 1,
  "display_name": "IP Transport MTU Drop",
  "confidence": 0.942,
  "confidence_delta": 0.12,
  "status": "LEADING",
  "supports": [
    "Interface drops precede service impact",
    "Packet size mismatch on SGi bearer",
    "Blast radius consistent"
  ],
  "against": [
    "No physical fiber down alarm"
  ],
  "missing": [
    "Adjacent Transport Router-01 queue statistics"
  ]
}
```

The UI must show:

```text
rank changes
confidence changes
supports
against
missing evidence
rejected hypotheses
```

---

# 16. Falsification Visibility

When a hypothesis is rejected, it should remain visible.

Example:

```text
RAN Radio Congestion
2.1%
REJECTED
```

Do not remove rejected hypotheses from history.

---

# 17. What FikraCore Is Doing Now

This panel must come from the backend reasoning task state.

Example payload:

```json
{
  "type": "reasoning_tasks",
  "tasks": [
    {
      "name": "Correlating 12 events across domains",
      "status": "COMPLETED"
    },
    {
      "name": "Analyzing MTU change impact",
      "status": "COMPLETED"
    },
    {
      "name": "Tracing packet flow",
      "status": "RUNNING"
    },
    {
      "name": "Evaluating hypothesis confidence",
      "status": "RUNNING"
    }
  ]
}
```

Allowed states:

```text
PENDING
RUNNING
COMPLETED
FAILED
```

This panel is critical for showing visible intelligence.

---

# 18. Service Impact / Blast Radius

This panel must be live.

Example payload:

```json
{
  "type": "impact_update",
  "service": "4G LTE Data",
  "throughput_impact_pct": -72,
  "affected_users": 24000,
  "regions_affected": 3,
  "services_impacted": 2
}
```

Display:

```text
4G LTE Data
-72%

3 regions affected

~24,000 enterprise users
```

---

# 19. Knowledge Gap / Unknown Boundary

The knowledge-gap panel must consume H2-compatible state.

Example:

```json
{
  "type": "knowledge_gap_update",
  "gaps": [
    {
      "id": "KG-01",
      "label": "Transport Router-01 queue statistics",
      "priority": "HIGH",
      "reason": "Needed to confirm buffer behavior"
    },
    {
      "id": "KG-02",
      "label": "Similar incidents in this topology",
      "priority": "MEDIUM",
      "reason": "Check historical knowledge"
    }
  ]
}
```

Do not invent missing topology in the frontend.

---

# 20. Next-Best Evidence / Intelligence Actions

This panel must be action-capable.

Example action:

```json
{
  "action_id": "NBA-001",
  "display_name": "Get Transport Router-01 queue statistics",
  "status": "READY",
  "action_type": "QUERY"
}
```

Clicking `Run` should call:

```text
POST /api/v1/fikracore/simulations/{run_id}/actions
```

Example:

```json
{
  "action_id": "NBA-001"
}
```

The UI should then show:

```text
READY
RUNNING
COMPLETED
FAILED
```

---

# 21. Learning Capture

The bottom Learning Capture bar must use real H3 state.

Example:

```json
{
  "type": "learning_update",
  "candidate_count": 1,
  "summary": "MTU change on aggregation router can cause LTE data degradation through packet fragmentation and gateway drops",
  "confidence": 0.87,
  "status": "CANDIDATE"
}
```

Available actions:

```text
Capture Insight
Send for Validation
Inspect Candidate
```

Do not auto-promote learned knowledge.

---

# 22. Floating Zaki AI Copilot

Keep the floating Zaki widget in the lower-right.

Resting state:

```text
orb
online status
small glow
```

Expanded state:

```text
current scenario
current simulation stage
leading hypothesis
service impact
unknowns
next-best evidence
chat history
contextual prompt chips
```

---

# 23. Zaki Backend Integration

Use:

```text
POST /api/v1/fikracore/zaki/chat
```

Example request:

```json
{
  "run_id": "RUN-20260911-001",
  "scenario_id": "SCN-001",
  "message": "Why is Transport Router-01 the leading root candidate?"
}
```

The backend should ground Zaki in the same shared simulation state.

---

# 24. Zaki Guardrails

Zaki may:

```text
explain
summarize
compare
navigate
orchestrate actions
```

Zaki must not independently generate:

```text
root cause
confidence
topology
blast radius
knowledge state
confirmed relationships
learned knowledge
```

Those must come from FikraCore capability output.

---

# 25. Frontend State Model

Use one normalized frontend store.

Example:

```ts
interface SimulationStore {
  scenario: Scenario | null
  run: SimulationRun | null
  stages: SimulationStage[]
  events: SimulationEvent[]
  entities: Record<string, EntityState>
  relationships: Record<string, RelationshipState>
  hypotheses: HypothesisState[]
  reasoningTasks: ReasoningTask[]
  impact: ImpactState | null
  knowledgeGaps: KnowledgeGap[]
  nextBestActions: IntelligenceAction[]
  learning: LearningState | null
  zaki: ZakiState
}
```

Do not keep conflicting copies of the same state inside separate components.

---

# 26. WebSocket Message Router

Implement a central message router.

Example:

```ts
switch (message.type) {
  case "simulation_stage":
  case "event":
  case "entity_state":
  case "relationship_state":
  case "hypothesis_update":
  case "reasoning_tasks":
  case "impact_update":
  case "knowledge_gap_update":
  case "next_best_evidence":
  case "learning_update":
}
```

Each message updates the central store.

---

# 27. Initial Load vs Live Delta

On scenario load:

```text
REST snapshot
```

Then:

```text
WebSocket live deltas
```

On WebSocket reconnect:

```text
fetch latest full snapshot
reconcile
resume stream
```

---

# 28. Reconnection Safety

The UI must show:

```text
LIVE
CONNECTING
DEGRADED
DISCONNECTED
```

If live connectivity is lost:

```text
do not silently continue showing stale values as current
```

Show:

```text
Live data disconnected
Last update: 10:43:12
```

---

# 29. Backend Health Indicator

Top bar:

```text
telecombrain MCP: LIVE
```

This should come from actual health state.

Possible values:

```text
LIVE
DEGRADED
OFFLINE
```

---

# 30. Scenario / Simulation Status

Possible states:

```text
READY
RUNNING
PAUSED
COMPLETED
FAILED
STOPPED
```

---

# 31. Simulation Speed

Support:

```text
0.5x
1x
2x
5x
```

Speed changes should call backend simulation controls.

Do not change only frontend animation speed.

---

# 32. Replay Mode

Replay mode should consume recorded backend events.

Allow:

```text
play
pause
seek
speed
restart
```

The replay should reproduce the same state transitions as the original run.

---

# 33. Selectable Scenario Live Stats

When a user changes scenario, all stats must update for the newly selected scenario.

Do not leave stale values from the prior scenario.

Refresh:

```text
scenario metadata
topology
service impact
domain list
current/last simulation
event count
hypotheses
knowledge gaps
coverage
```

---

# 34. Scenario-Specific Knowledge

The UI may show context from `telecombrain` relevant to the selected scenario.

Example:

```text
Known Entities
Known Relationships
Similar Incidents
Known Service Dependencies
Knowledge Gaps
```

This should be fetched from the backend, not constructed in the frontend.

---

# 35. Scenario Search

Support search by:

```text
scenario name
scenario ID
service
domain
entity
incident type
```

---

# 36. Click-to-Focus Interaction

Clicking an event should:

```text
focus relevant entity in graph
highlight related hypothesis
show relevant evidence
```

Clicking a graph entity should:

```text
open entity details
filter related events
show relevant hypotheses
```

---

# 37. Cross-Panel Synchronization

All panels should share state.

Example:

```text
Click Transport Router-01
      ↓
graph highlights router
event stream filters related events
hypothesis panel highlights relevant hypothesis
knowledge-gap panel filters relevant gaps
Zaki context updates
```

This is required.

---

# 38. Human-Readable Naming

Use operator-friendly labels.

Examples:

```text
Transport Router-01
Serving Gateway-01
Packet Gateway-01
Online Charging
Policy Control
4G LTE Data
```

Canonical IDs belong in Technical View only.

---

# 39. Technical View

Add optional Technical View.

Show:

```text
canonical IDs
raw relationship types
evidence IDs
provider provenance
timestamps
confidence components
```

---

# 40. No Hidden Truth Leakage

Operational UI must never receive simulator Hidden Truth.

Allowed:

```text
Hidden Truth → Evaluator / Benchmark
```

Forbidden:

```text
Hidden Truth → Simulator live UI
Hidden Truth → Zaki
Hidden Truth → telecombrain
Hidden Truth → learning state
```

---

# 41. Loading States

Each major panel must handle:

```text
loading
empty
live
error
stale
```

Never render fake sample data while real backend loading is incomplete.

---

# 42. Error Handling

Display useful errors for:

```text
scenario not found
simulation start failed
WebSocket disconnected
entity unavailable
knowledge provider unavailable
action execution failed
Zaki unavailable
```

---

# 43. Suggested Frontend Component Structure

```text
SimulatorPage
├── SimulatorHeader
├── PrimaryNavigation
├── SimulationJourney
├── EventStreamPanel
├── CausalGraphPanel
├── HypothesisEvolutionPanel
├── ReasoningActivityPanel
├── ServiceImpactPanel
├── KnowledgeGapPanel
├── NextBestEvidencePanel
├── LearningCaptureBar
└── ZakiFloatingCopilot
```

---

# 44. Suggested Data Services

```text
scenarioService.ts
simulationService.ts
simulationSocket.ts
knowledgeService.ts
zakiService.ts
```

---

# 45. Suggested Hooks

```text
useScenarios()
useScenario(id)
useSimulation(runId)
useSimulationStream(runId)
useKnowledgeContext(scenarioId)
useZaki(runId)
```

---

# 46. Live Update Frequency

Prefer event-driven updates.

Do not poll every second unless no streaming mechanism exists.

If polling is required:

```text
2–5 second interval
```

and clearly identify it as fallback mode.

---

# 47. Performance

The UI should remain smooth with:

```text
100+ live events
50+ graph entities
100+ relationships
10+ hypotheses
multiple live updates per second
```

Use:

```text
memoization
batched state updates
virtualized event list
graph update throttling where necessary
```

---

# 48. Visual Style

Match the reference:

```text
dark navy/black operations workspace
thin cyan borders
cyan primary labels
green confirmation
red failure
amber uncertainty
purple learning
compact typography
dense but clean panel layout
```

Keep the design uncluttered.

---

# 49. Do Not Remove Functional Areas

Declutter through:

```text
spacing
typography
grouping
collapsible details
responsive hierarchy
```

Do not remove:

```text
Live Simulation Journey
Event Stream
Causal Graph
Hypothesis Evolution
Reasoning Activity
Service Impact
Knowledge Gaps
Next-Best Evidence
Learning Capture
Zaki
```

---

# 50. Acceptance Scenario

Use:

```text
SCN-001
SGi Throughput Degradation & MTU Blackhole
```

Expected journey:

```text
1. User selects SCN-001.
2. UI fetches scenario metadata.
3. UI fetches topology snapshot.
4. User clicks Run.
5. Backend returns run_id.
6. UI connects to live WebSocket.
7. Trigger stage activates.
8. Events begin arriving.
9. Graph nodes change state.
10. Correlation stage activates.
11. Hypotheses appear and confidence changes.
12. Wrong hypothesis is rejected.
13. Root candidate emerges.
14. Service impact updates.
15. Knowledge gap appears.
16. Next-best evidence action becomes available.
17. User executes action.
18. Backend returns new evidence.
19. Hypothesis confidence changes.
20. Learning candidate appears.
21. Zaki explains the current reasoning state.
22. Simulation reaches Action / Recommendation.
```

---

# 51. Definition of Done

The implementation is complete when:

```text
[ ] scenario selector is backend-driven
[ ] scenario metadata loads from backend
[ ] topology loads from backend
[ ] simulation can start from UI
[ ] run_id is persisted
[ ] WebSocket/SSE live stream connects
[ ] event stream updates live
[ ] simulation stages update live
[ ] graph entity states update live
[ ] graph relationship states update live
[ ] hypotheses update live
[ ] confidence values update live
[ ] rejected hypotheses remain visible
[ ] service impact updates live
[ ] knowledge gaps update live
[ ] next-best-evidence actions update live
[ ] next-best-evidence actions can be executed
[ ] learning state updates live
[ ] Zaki uses current run context
[ ] backend connectivity state is visible
[ ] scenario switching clears stale state
[ ] reconnect performs state resynchronization
[ ] no operational values are hard-coded
[ ] Hidden Truth leakage remains zero
```

---

# 52. Final Principle

> **Every number on screen must have a backend source.**

And:

> **Every live visual transition should represent an actual FikraCore state change.**

The finished UI should let the operator watch a selected network scenario evolve from raw signals to correlated context, competing hypotheses, validated causal reasoning, knowledge gaps, next-best evidence, learning, and action in real time.
