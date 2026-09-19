# FikraCore Step 5 UI — Scenario / Run / Visualization Synchronization Fix

## Purpose

Fix the current simulator state-sync bug where changing the selected scenario updates the header metadata and `run_id`, but the visualization panels continue to display stale data from the previously selected scenario.

Observed failure pattern:

```text
Header Scenario changes
Run ID changes
BUT
Event Stream stays the same
Causal Graph stays the same
Hypotheses stay the same
Impact stays the same
Knowledge Gaps stay the same
Next-Best Evidence stays the same
Zaki context may stay the same
```

This is not acceptable for a reasoning simulator.

> **Every visible operational element must belong to the currently active `scenario_id` and `run_id`.**

---

# 1. Root Problem

The likely issue is that scenario metadata is being updated independently from the actual run-bound visualization state.

Typical broken flow:

```text
User selects scenario
        ↓
scenario_id updates
run_id updates
        ↓
old UI store remains populated
        ↓
old WebSocket may still be connected
        ↓
old topology / hypotheses / events remain visible
```

This causes stale state contamination.

---

# 2. Required Ownership Model

The authoritative hierarchy must be:

```text
Selected Scenario
      ↓
Selected / Created Run
      ↓
Authoritative Run Snapshot
      ↓
Frontend Simulation Store
      ↓
Live Stream for THAT run_id
      ↓
Incremental Deltas
```

The frontend must treat `run_id` as the authoritative runtime boundary.

---

# 3. Core Invariant

For every displayed simulation object:

```text
object.scenario_id == activeScenarioId
AND
object.run_id == activeRunId
```

This applies to:

```text
events
entities
relationships
topology
hypotheses
reasoning tasks
service impact
blast radius
knowledge gaps
next-best evidence
learning state
simulation stages
timers
Zaki context
```

If the object does not belong to the active scenario/run, it must not be displayed.

---

# 4. Scenario Switch Sequence

When the user selects a new scenario, execute this exact sequence:

```text
1. Mark UI as SWITCHING_SCENARIO
2. Disconnect old live stream
3. Invalidate old active run_id
4. Clear all scenario-specific frontend state
5. Fetch selected scenario metadata
6. Resolve current run or create/select run
7. Fetch authoritative full snapshot for that run
8. Validate snapshot scenario_id/run_id
9. Atomically hydrate the frontend store
10. Set activeScenarioId
11. Set activeRunId
12. Connect live stream for activeRunId
13. Update Zaki context
14. Mark UI as READY / RUNNING
```

Do not connect the live stream before the snapshot is loaded and validated.

---

# 5. Full State Reset

On scenario change, clear:

```text
events
entities
relationships
topology
hypotheses
reasoning tasks
service impact
blast radius
knowledge gaps
next-best evidence
learning state
simulation journey stages
selected entity
selected service
selected hypothesis
selected gap
selected evidence
elapsed timer
temporary drawers/modals
Zaki scenario-specific context
```

Do not preserve scenario-specific state from the previous run.

Global user preferences may remain:

```text
theme
panel sizes
response level
view density
saved filters if explicitly global
```

---

# 6. Frontend Switch Function

Recommended structure:

```ts
async function switchScenario(scenarioId: string) {
  setSyncState("SWITCHING_SCENARIO");

  disconnectSimulationStream();

  setActiveRunId(null);

  resetScenarioScopedState();

  const scenario = await scenarioService.getScenario(scenarioId);

  const run = await simulationService.resolveRunForScenario(scenario.id);

  const snapshot = await simulationService.getRunSnapshot(run.run_id);

  validateSnapshotIdentity(snapshot, scenario.id, run.run_id);

  hydrateSimulationState(snapshot);

  setActiveScenarioId(scenario.id);
  setActiveRunId(run.run_id);

  connectSimulationStream(run.run_id);

  updateZakiContext({
    scenarioId: scenario.id,
    runId: run.run_id
  });

  setSyncState("READY");
}
```

---

# 7. Snapshot Must Be Authoritative

Use one backend snapshot endpoint equivalent to:

```text
GET /api/v1/fikracore/simulations/{run_id}/state
```

The returned payload should contain all state necessary to render the UI consistently.

Recommended structure:

```json
{
  "scenario_id": "H4-WI-040",
  "run_id": "RUN-20260911170046279782",
  "status": "RUNNING",
  "stage": "correlation",
  "scenario": {},
  "journey": [],
  "events": [],
  "entities": [],
  "relationships": [],
  "hypotheses": [],
  "reasoning_tasks": [],
  "impact": {},
  "knowledge_gaps": [],
  "next_best_evidence": [],
  "learning": {},
  "updated_at": "2026-09-11T17:00:46Z"
}
```

The frontend should hydrate from this snapshot in one transaction.

---

# 8. Replace, Do Not Merge

Incorrect:

```ts
setState({
  ...oldState,
  scenario: newScenario,
  runId: newRunId
});
```

Correct:

```ts
setState(buildStateFromSnapshot(newSnapshot));
```

For a scenario switch, use **replace**, not incremental merge.

---

# 9. Live Stream Identity

Every live WebSocket/SSE message should include:

```json
{
  "scenario_id": "H4-WI-040",
  "run_id": "RUN-20260911170046279782",
  "type": "hypothesis_update"
}
```

The frontend must reject messages that do not match the active context.

---

# 10. Live Message Guard

```ts
function handleLiveMessage(message: LiveMessage) {
  if (message.scenario_id !== activeScenarioId) return;
  if (message.run_id !== activeRunId) return;

  applySimulationDelta(message);
}
```

Never apply stale messages from an old run.

---

# 11. Close Previous Stream

When scenario/run changes:

```text
unsubscribe old run
close old WebSocket/SSE
remove old listeners
cancel pending reconnection timer
```

Do not leave the previous stream alive in the background.

---

# 12. Prevent Race Conditions

If the user rapidly changes scenarios, a late response from an older selection must not overwrite the latest selection.

Use a request generation token or `AbortController`.

Example:

```ts
let scenarioSwitchVersion = 0;

async function switchScenario(id: string) {
  const version = ++scenarioSwitchVersion;

  const snapshot = await loadScenarioRun(id);

  if (version !== scenarioSwitchVersion) return;

  hydrateSimulationState(snapshot);
}
```

---

# 13. Sync State Machine

Use an explicit synchronization state:

```text
IDLE
SWITCHING_SCENARIO
LOADING_SNAPSHOT
CONNECTING_LIVE_STREAM
SYNCED
RESYNCING
DISCONNECTED
ERROR
```

The UI should visibly reflect these states.

---

# 14. UI During Scenario Switch

Do not show old operational data under the new scenario title.

Use:

```text
Scenario switching…
Loading H4-WI-040…
```

or skeleton loaders.

---

# 15. Identity Consistency Guard

Validate:

```text
header scenario_id
snapshot scenario_id
frontend active scenario_id
WebSocket scenario_id
Zaki scenario_id
```

and:

```text
header run_id
snapshot run_id
frontend active run_id
WebSocket run_id
Zaki run_id
```

All must match.

---

# 16. Out-of-Sync Protection

If a mismatch occurs, show:

```text
STATE OUT OF SYNC
Resynchronizing…
```

Then:

```text
disconnect stream
fetch latest full snapshot
validate
replace store
reconnect stream
```

---

# 17. Automatic Resynchronization

Trigger a full resync when:

```text
run identity mismatch
sequence gap detected
live stream reconnects
snapshot timestamp is stale
unknown entity is referenced by a live event
frontend detects impossible mixed state
```

---

# 18. Event Sequence Numbers

Recommended live message envelope:

```json
{
  "run_id": "RUN-102",
  "sequence": 145,
  "type": "event"
}
```

If:

```text
received sequence > lastSequence + 1
```

request a fresh snapshot.

---

# 19. Snapshot Version

Recommended:

```json
{
  "snapshot_version": 23
}
```

Use for reconciliation and debugging.

---

# 20. Scenario Definition vs Run State

Keep separate.

Scenario definition:

```text
name
domains
services
difficulty
supported capabilities
description
```

Run state:

```text
events
topology state
hypotheses
impact
stage
knowledge gaps
actions
elapsed time
```

---

# 21. Run Resolution

For the selected scenario explicitly resolve:

```text
active run
or
latest completed run
or
new run
```

Do not silently reuse the previous scenario's run.

---

# 22. Multiple Runs

Support:

```text
Scenario H4-WI-040
  ├── RUN-001 completed
  ├── RUN-002 completed
  └── RUN-003 running
```

Changing run must perform the same synchronization sequence as changing scenario.

---

# 23. Simulation Journey Sync

The stepper must come from the active run snapshot.

Do not reuse previous:

```text
stage
progress
completed steps
timestamps
```

---

# 24. Event Stream Sync

On scenario/run switch:

```text
clear event list
load active run events
subscribe to active run events
```

---

# 25. Causal Graph Sync

Rebuild or rehydrate the graph from the selected run's:

```text
entities
relationships
health states
reasoning states
candidate paths
confirmed paths
unknown boundaries
```

Do not reuse one fixed MTU graph for unrelated scenarios.

---

# 26. Hypothesis Sync

On run change:

```text
clear hypothesis list
load run-specific hypotheses
```

Preserve only selected-run:

```text
rank
confidence
supports
against
missing evidence
status
```

---

# 27. Impact Sync

Clear old values unless the new run actually reports them.

Do not retain example values such as:

```text
-72%
~24,000 users
3 regions
```

across scenarios.

---

# 28. Knowledge Gap Sync

Clear previous gaps and load active-run:

```text
gap IDs
gap type
boundary
priority
required evidence
state
```

---

# 29. Next-Best-Evidence Sync

Regenerate actions from the active run.

Do not preserve old:

```text
action IDs
statuses
results
```

---

# 30. Learning State Sync

Learning state must be active-run specific.

Clear previous candidate/validation/promotion state unless linked to the selected run.

---

# 31. Zaki Synchronization

Zaki must use the same active identity:

```text
scenario_id
run_id
workspace
simulation_stage
selected entity
selected hypothesis
selected gap
```

On scenario/run switch:

```text
clear old scenario-specific context
replace with new context
```

---

# 32. Zaki Identity Check

Before `/zaki/chat`:

```ts
if (
  context.scenarioId !== activeScenarioId ||
  context.runId !== activeRunId
) {
  rebuildZakiContext();
}
```

---

# 33. Backend Identity Contract

All run-specific responses should include:

```text
scenario_id
run_id
```

including:

```text
snapshot
events
hypotheses
impact
knowledge gaps
actions
learning state
```

---

# 34. Cache Safety

If using React Query, SWR, RTK Query, etc., query keys must include identity.

Correct:

```ts
["simulation-state", scenarioId, runId]
```

Incorrect:

```ts
["simulation-state"]
```

---

# 35. Component Local-State Audit

Audit components for hidden scenario-sensitive local state:

```text
cached graph nodes
event arrays
local hypothesis lists
impact values
selected nodes
drawer content
```

Move these to the shared run store or reset them on identity change.

---

# 36. Derived State

Recompute from active run:

```text
event counts
leading hypothesis
path confidence
affected users
knowledge gap count
stage completion
```

Do not reuse derived values across runs.

---

# 37. Timer Sync

Timer must bind to active-run:

```text
started_at
paused_at
status
backend elapsed time
```

Reset timer when run changes.

---

# 38. Run-Control Sync

Pause / Resume / Stop must use:

```text
activeRunId
```

Avoid stale captured run IDs in callbacks.

---

# 39. Shared Active Context

Recommended:

```ts
interface ActiveSimulationContext {
  scenarioId: string;
  runId: string;
  scenario: ScenarioDetails;
  run: RunDetails;
  snapshotVersion: number;
  lastUpdatedAt: string;
}
```

All panels should derive identity from this object.

---

# 40. Atomic Hydration

Avoid independent setters that can temporarily produce mixed state.

Prefer:

```ts
dispatch({
  type: "HYDRATE_RUN_SNAPSHOT",
  payload: snapshot
});
```

Reducer:

```ts
case "HYDRATE_RUN_SNAPSHOT":
  return {
    ...createEmptyRunState(),
    scenarioId: action.payload.scenario_id,
    runId: action.payload.run_id,
    events: action.payload.events,
    entities: normalizeEntities(action.payload.entities),
    relationships: normalizeRelationships(action.payload.relationships),
    hypotheses: action.payload.hypotheses,
    impact: action.payload.impact,
    knowledgeGaps: action.payload.knowledge_gaps,
    nextBestEvidence: action.payload.next_best_evidence,
    learning: action.payload.learning,
    journey: action.payload.journey,
    lastUpdatedAt: action.payload.updated_at
  };
```

---

# 41. Backend Safety

Do not change H1/H2/H3/H4 reasoning semantics.

Allowed backend changes:

```text
run snapshot serializer
scenario/run identity fields
sequence numbers
snapshot version
stream envelope
state endpoint
```

---

# 42. Development Diagnostics

Add development-only diagnostics:

```text
Active Scenario
Active Run
Snapshot Scenario
Snapshot Run
WebSocket Run
Snapshot Version
Last Sequence
Sync State
```

This should make stale-state bugs immediately visible.

---

# 43. Scenario-Switch Tests

Add:

```text
test_switch_scenario_clears_old_events
test_switch_scenario_clears_old_topology
test_switch_scenario_clears_old_hypotheses
test_switch_scenario_clears_old_impact
test_switch_scenario_clears_old_gaps
test_switch_scenario_clears_old_actions
test_switch_scenario_clears_old_learning
test_switch_scenario_resets_timer
test_switch_scenario_updates_zaki_context
```

---

# 44. Run-Switch Tests

Add:

```text
test_switch_run_rehydrates_snapshot
test_run_switch_disconnects_previous_stream
test_run_switch_connects_correct_stream
test_run_selector_preserves_scenario
```

---

# 45. Stale-Message Tests

Add:

```text
test_old_run_message_is_ignored
test_old_scenario_message_is_ignored
test_late_snapshot_cannot_overwrite_new_selection
test_sequence_gap_triggers_resync
```

---

# 46. Identity Tests

Add:

```text
test_header_scenario_matches_snapshot
test_header_run_matches_snapshot
test_zaki_identity_matches_active_run
test_all_panel_data_matches_active_run
```

---

# 47. Multi-Scenario Visualization Test

Use at least three visibly different scenarios:

```text
Scenario A — Transport / MTU incident
Scenario B — Knowledge-model insufficiency
Scenario C — What-If failover / blast radius
```

Verify that switching changes:

```text
topology
events
hypotheses
impact
knowledge gaps
actions
journey
Zaki context
```

---

# 48. Acceptance Walkthrough

```text
1. Load Scenario A.
2. Confirm its MTU topology and evidence.
3. Select Scenario B.
4. Confirm Scenario A events disappear.
5. Confirm Scenario A topology disappears.
6. Confirm Scenario B unknown-boundary state appears.
7. Confirm Scenario B-specific gaps/hypotheses appear.
8. Confirm Zaki references Scenario B.
9. Select Scenario C.
10. Confirm Scenario B state disappears.
11. Confirm forward propagation/blast-radius state appears.
12. Confirm run ID changes.
13. Confirm every panel is bound to the new run.
14. Rapidly switch A → B → C and confirm late responses cannot restore A/B.
```

---

# 49. Definition of Done

```text
[ ] selecting a scenario updates header and all body panels
[ ] selecting a run updates all body panels
[ ] old stream subscriptions are closed
[ ] stale messages are rejected
[ ] scenario/run changes replace state rather than merge stale data
[ ] no previous events remain
[ ] no previous topology remains
[ ] no previous hypotheses remain
[ ] no previous impact remains
[ ] no previous knowledge gaps remain
[ ] no previous next-best actions remain
[ ] no previous learning state remains
[ ] timer resets correctly
[ ] Zaki context updates correctly
[ ] header, snapshot, store, stream, and Zaki identities match
[ ] identity mismatch triggers resynchronization
[ ] race conditions cannot overwrite newer selection
[ ] different scenarios produce visibly different visualizations
[ ] H1–H4 reasoning semantics remain unchanged
```

---

# Final Synchronization Rule

> **Scenario selects the run. The run selects the snapshot. The snapshot replaces the visualization. The live stream may update only that run.**

> **No panel may display data that does not match the active `scenario_id` and `run_id`.**
