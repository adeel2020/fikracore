# FikraCore Step 5.2.2 — Zaki 2.0 Contextual Copilot UX & Interaction Model

## Purpose

Step 5, Step 5.1, Step 5.2, and the Step 5.2.1 attribution consistency correction are already implemented or defined.

This document defines the next additive evolution only:

> **Modernize Zaki from a side-chat assistant into a contextual telecom investigation copilot embedded directly into the FikraCore reasoning experience.**

This step must not rewrite the reasoning engine, simulation engine, live reasoning pipeline, or authoritative run model.

The backend remains the source of truth.

Zaki remains a contextual explainer, reasoning navigator, simulation/operational copilot, and governed action launcher. Zaki is not a root-cause authority, confidence calculator, domain-attribution authority, hidden-truth consumer, independent reasoning engine, or uncontrolled action executor.

---

## 1. Core Product Goal

Move from:

```text
separate chat panel
→ generic question
→ generic answer
```

to:

```text
user clicks a reasoning object
→ Zaki receives exact selected context
→ Zaki explains that object
→ user asks targeted follow-up
→ Zaki can invoke governed actions
```

Examples:

```text
click H1
→ explain H1

click Service Dependency
→ explain pathway activation

click IP Transport PRIMARY
→ explain authoritative attribution

click Knowledge Gap
→ explain missing context

click conduit
→ explain relation
```

---

## 2. Architectural Rule

Reuse existing:

```text
run_id
scenario_id / intent_id
source_mode
revision
sequence
SimulationRun / OperationalRun
Zaki bridge
Zaki endpoint
Neural Reasoning Map
Hypothesis Board
Knowledge Gaps
Next-Best Evidence
Domain Attribution
Validation
Learning
```

Do not create a second Zaki state model, second run context, frontend reasoning engine, Zaki-only hypothesis model, or Zaki-only attribution model.

---

## 3. Visual Design Language

### Cyan — Operational Structure

Use cyan for:

```text
entities
domains
services
network elements
stage names
phase names
reasoning pathways
canonical operational labels
```

Examples:

```text
IP Transport
Mobile Core
AMF-01
UPF-01
Enterprise APN
Service Dependency
Hypothesis Testing
Knowledge Gap Check
```

### Magenta — Focus / Attention

Use magenta for:

```text
selected entity
selected hypothesis
active stage
active pathway
scenario/intent/incident IDs
change IDs
ticket IDs
trace/pcap filenames
high-attention objects
```

Examples:

```text
H1 — Core Transport Router Failure
H4-WI-36
CR-7721
TT-984210
DTMFsipinfo.pcap
```

### Turquoise — Convergence / Trust

Use turquoise for:

```text
confirmed
validated
resolved
accepted
converged
recovered
trusted knowledge
successful completion
```

Examples:

```text
CONFIRMED
VALIDATED
RESOLVED
RECOVERED
SYNTHESIS CONVERGED
LEARNING PROMOTED
```

---

## 4. Color Transition Rules

### Entity

```text
normal → cyan
selected/focused → magenta
validated/confirmed → turquoise
```

### Stage

```text
inactive → dim cyan
active → magenta
complete → turquoise + check
blocked → magenta title + explicit BLOCKED badge
```

### Pathway

```text
dormant → dim cyan
active → magenta
resolved → turquoise
rejected → muted gray
```

### Hypothesis

```text
candidate/unranked → cyan
leading/testing → magenta
confirmed → turquoise
rejected → muted gray
```

---

## 5. Typography

Use a clear sans-serif for normal labels and narrative, and a clear monospace stack for technical IDs where appropriate.

Avoid decorative sci-fi body fonts, low-contrast thin text, excessive letter spacing, and blurred glow over text.

Recommended:

```text
entity/stage/pathway/hypothesis names → 600–700
body explanation → 400–500
metadata → 400
```

Glow should surround containers and conduits, not text.

---

## 6. Zaki Layout States

Support:

```text
COMPACT
EXPANDED
FOCUSED_CONTEXT
REPLAY
CONFLICT
```

### COMPACT

Show:

```text
ZAKI
copilot state
current stage
run status
```

### EXPANDED

Show:

```text
run context
selected context
short explanation
supporting evidence
missing context
next step
quick actions
input
```

### FOCUSED_CONTEXT

Prominently show the selected object and object-specific explanation.

### REPLAY

Clearly show:

```text
REPLAY MODE
```

### CONFLICT

Clearly show:

```text
CONFLICT DETECTED
```

---

## 7. Context Header

Example:

```text
ZAKI — OPERATIONAL COPILOT

Source:
LIVE OPERATIONS

Intent:
Enterprise APN Success Below Target

Run:
RUN-20260914-00127

Stage:
Hypothesis Testing

State:
RUNNING
```

Simulation mode should instead show Scenario and Simulation source.

---

## 8. Selected Context Contract

```ts
type ZakiSelectedContext = {
  context_type:
    | "EVIDENCE"
    | "PATHWAY"
    | "CONNECTION"
    | "HYPOTHESIS"
    | "KNOWLEDGE_GAP"
    | "NBE"
    | "DOMAIN_ATTRIBUTION"
    | "SERVICE_IMPACT"
    | "VALIDATION"
    | "LEARNING"
    | "STAGE"
    | "ENTITY"

  context_id: string
  display_name: string

  run_id: string
  revision: number

  metadata?: Record<string, unknown>
}
```

---

## 9. Context Selection Behavior

```text
UI object selected
→ store selected context
→ validate run/revision
→ update Zaki context
→ refresh quick prompts
→ render object-specific summary
```

Do not call the LLM merely because selection changed unless explanation is explicitly requested or a material proactive message is needed.

---

## 10. Click-to-Explain

### Hypothesis

Expose:

```text
state
confidence
supporting evidence
contradictions
missing evidence
active pathways
latest confidence delta
```

### Pathway

Expose:

```text
why active
which evidence activated it
which hypotheses it affects
current state
```

### Connection

Expose:

```text
source
target
relation type
reason
evidence
confidence delta
provenance
```

### Knowledge Gap

Expose:

```text
why it matters
what it blocks
affected hypothesis/pathway
required evidence
```

### Domain Attribution

Explain only authoritative backend attribution.

---

## 11. Response Structure

Default response sections:

```text
What Happened
Why It Matters
What Supports It
What Contradicts It
What Is Missing
What Happens Next
```

Only show relevant sections.

---

## 12. Example Response

```text
WHAT HAPPENED
H1 — Core Transport Router Failure is the leading hypothesis.

WHY IT MATTERS
Affected services share the same upstream IP Transport dependency.

WHAT SUPPORTS IT
• BGP adjacency instability
• packet loss on shared path
• dependency-path alignment

WHAT IS MISSING
• redundant MPLS path health

WHAT HAPPENS NEXT
Request backup-path telemetry and retest H1.
```

---

## 13. Quick Prompt Actions

Examples:

```text
Why?
What changed?
Show evidence
Show contradictions
What is missing?
What next?
Why is this active?
Why did confidence change?
Why is this domain PRIMARY?
What would change the conclusion?
```

Prompts must be context-sensitive.

---

## 14. Context-Specific Quick Prompts

### Hypothesis

```text
Why is H1 leading?
What supports H1?
What contradicts H1?
Why did confidence change?
What is still missing?
```

### Pathway

```text
Why is this pathway active?
Which evidence activated it?
Which hypothesis does it affect?
```

### Domain

```text
Why is this PRIMARY?
What evidence supports attribution?
Which hypothesis supports it?
```

### Knowledge Gap

```text
Why does this matter?
What is blocked?
What evidence resolves it?
```

### Stage

```text
Why are we here?
What must happen to advance?
Why are we blocked?
```

---

## 15. Proactive Micro-Briefs

Only for meaningful backend revision changes.

Examples:

```text
H1 ↑ 7%
New supporting evidence admitted.
```

```text
Knowledge gap detected
Backup-path health is unknown.
```

```text
Attribution conflict
Leading hypothesis and domain attribution disagree.
```

```text
Validation ready
Transport Engineer review is required.
```

Do not repeat unchanged state.

---

## 16. Revision-Diff Integration

```ts
type ZakiRevisionDiff = {
  previous_revision: number
  current_revision: number

  evidence_added?: string[]
  evidence_removed?: string[]
  pathways_activated?: string[]
  pathways_resolved?: string[]
  hypotheses_changed?: string[]
  gaps_added?: string[]
  gaps_resolved?: string[]
  attribution_changed?: boolean
  validation_changed?: boolean
  synthesis_changed?: boolean
  stage_changed?: boolean
}
```

Use it for "What changed?" and proactive micro-briefs.

---

## 17. Zaki State Model

```text
IDLE
OBSERVING
REASONING
NEEDS_EVIDENCE
CONFLICT_DETECTED
VALIDATION_REQUIRED
RECOMMENDATION_READY
REPLAY
```

States derive from authoritative backend run state.

---

## 18. State Mapping

Examples:

```text
active run, no block → REASONING
blocked for evidence → NEEDS_EVIDENCE
attribution conflict → CONFLICT_DETECTED
validation pending → VALIDATION_REQUIRED
action stage ready → RECOMMENDATION_READY
replay → REPLAY
```

---

## 19. Response Levels

Support:

```text
Executive
Operator
Engineer
Deep Technical
```

Executive focuses on impact, leading explanation, uncertainty, primary domain, decision.

Operator focuses on stage, evidence, pathways, hypotheses, gaps, and next action.

Engineer focuses on entities, dependencies, protocol/topology context, support/contradiction, and tests.

Deep Technical includes IDs, provenance, revision, sequence, provider, trace, and raw state references.

Human-readable names remain primary.

---

## 20. Structured Entity Highlighting

```ts
type HighlightedEntity = {
  id?: string
  display_name: string

  entity_type:
    | "NETWORK_ELEMENT"
    | "SERVICE"
    | "DOMAIN"
    | "PATHWAY"
    | "STAGE"
    | "PHASE"
    | "HYPOTHESIS"
    | "SCENARIO"
    | "INTENT"
    | "INCIDENT"
    | "CHANGE"
    | "TICKET"
    | "TRACE"
    | "KNOWLEDGE_GAP"

  visual_role:
    | "STRUCTURE"
    | "FOCUS"
    | "CONFIRMED"
}
```

Frontend mapping:

```text
STRUCTURE → cyan
FOCUS → magenta
CONFIRMED → turquoise
```

---

## 21. No Raw HTML from LLM

Zaki should return structured text, entities, sections, and governed actions.

Frontend owns rendering.

---

## 22. Structured Response Contract

```ts
type ZakiResponseV2 = {
  run_id: string
  revision: number

  source_mode: "SIMULATION" | "LIVE_INTENT"

  copilot_state:
    | "IDLE"
    | "OBSERVING"
    | "REASONING"
    | "NEEDS_EVIDENCE"
    | "CONFLICT_DETECTED"
    | "VALIDATION_REQUIRED"
    | "RECOMMENDATION_READY"
    | "REPLAY"

  response_level:
    | "EXECUTIVE"
    | "OPERATOR"
    | "ENGINEER"
    | "DEEP_TECHNICAL"

  selected_context?: ZakiSelectedContext

  sections: {
    title: string
    content: string
  }[]

  entities?: HighlightedEntity[]

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

## 23. Suggested Actions

Reuse the existing governed action model.

Examples:

```text
SHOW_EVIDENCE
SHOW_CONTRADICTIONS
FOCUS_HYPOTHESIS
FOCUS_PATHWAY
SHOW_GAP
REQUEST_EVIDENCE
SHOW_ATTRIBUTION
REQUEST_VALIDATION
```

Do not add autonomous remediation in Step 5.2.2.

---

## 24. Governed Action Rule

Zaki may suggest and invoke existing governed handlers.

Zaki must not directly mutate:

```text
hypothesis confidence
stage state
domain attribution
validation result
learning state
root cause
```

---

## 25. Conflict Experience

If the backend reports inconsistency:

```text
domain attribution conflict
revision mismatch
unsupported PRIMARY
stale attribution
```

show:

```text
CONFLICT DETECTED
```

Example:

```text
Current leading hypothesis points to IP Transport.

Authoritative domain attribution still shows RAN PRIMARY.

Attribution recomputation is required before domain ownership can be trusted.
```

---

## 26. Live vs Simulation Awareness

Header and responses must clearly distinguish:

```text
LIVE OPERATIONS
OFFLINE SIMULATION
```

Live mode may show Intent, Service, Severity, Latest Evidence Time.

Simulation mode may show Scenario and Replay Position.

---

## 27. Replay Experience

In replay:

```text
show REPLAY MODE
show replay revision
show replay position
```

Zaki must not look ahead beyond the replay cursor.

---

## 28. Compact-to-Expanded Interaction

```text
idle → compact orb/pill
meaningful event → compact pulse/brief
user clicks Zaki → expanded panel
user selects object → focused context
user closes → compact state retained
```

---

## 29. Floating Orb / Copilot Pill

Use subtle operational motion.

Recommended glow semantics:

```text
cyan → observing
magenta → reasoning/attention
turquoise → confirmed/ready/resolved
```

Animation must not obscure operational meaning.

---

## 30. Notification Discipline

Only notify proactively for:

```text
stage change
blocked state
material hypothesis change
new contradiction
knowledge gap
domain attribution change
validation required
recovery signal
terminal state
```

Do not notify for every telemetry event.

---

## 31. Neural Reasoning Map Integration

Selectable objects:

```text
Evidence
Pathway
Connection
Reasoning Core
Hypothesis
Gap
Validation
Learning
Domain Attribution
Affected Service
```

Selection updates Zaki context without changing backend reasoning.

---

## 32. Reasoning Core Selection

If Reasoning Core is selected, explain:

```text
current synthesis state
active pathways
leading hypothesis
contradictions
knowledge gaps
validation state
```

Do not expose hidden chain-of-thought. Use authoritative summarized reasoning state only.

---

## 33. Accessibility

Ensure:

```text
cyan readable on dark background
magenta readable on dark background
turquoise readable on dark background
neutral body text readable
selected state not color-only
status labels remain textual
```

Use icons, badges, and text labels in addition to color.

---

## 34. Performance

Do not trigger LLM calls for:

```text
hover
simple selection
panel open/close
every revision
every telemetry event
```

Prefer cached grounded summaries and structured metadata.

Invoke the model only when explanation is requested or a material proactive event requires it.

---

## 35. Caching

Cache grounded explanations by:

```text
run_id
revision
selected_context
response_level
```

Invalidate on revision/context/response-level change.

Never reuse across runs.

---

## 36. API Evolution

Prefer extending the existing Zaki endpoint.

Example:

```json
{
  "message": "Why is this pathway active?",
  "run_id": "RUN-20260914-00127",
  "revision": 214,
  "response_level": "ENGINEER",
  "selected_context": {
    "context_type": "PATHWAY",
    "context_id": "SERVICE_DEPENDENCY",
    "display_name": "Service Dependency"
  }
}
```

---

## 37. Server-Side Context Resolution

```text
request
→ validate run
→ validate revision
→ load authoritative selected object
→ load run state
→ build grounded context
→ generate response
→ return structured response
```

Do not trust arbitrary client-provided explanation content.

---

## 38. Modern Zaki Panel Structure

```text
HEADER
ZAKI — Operational Copilot
Source / Run / Stage / State

SELECTED CONTEXT
selected object
status
confidence if applicable

SUMMARY
short explanation

WHY
reason

SUPPORT
supporting evidence

CONTRADICTIONS
if any

MISSING
if any

NEXT
next-best evidence / next stage / validation

QUICK ACTIONS
context-specific buttons

ASK ZAKI
input
```

---

## 39. Example — Hypothesis Focus

```text
ZAKI — OPERATIONAL COPILOT

LIVE OPERATIONS
Hypothesis Testing • RUNNING

Selected
H1 — Core Transport Router Failure
94.2% • LEADING

Why it matters
Shared service impact aligns with the same upstream transport dependency.

Supporting Evidence
• BGP adjacency instability
• elevated packet loss
• dependency-path alignment

Missing
• redundant path health

Next
Request backup-path telemetry
```

Color semantics:

```text
IP Transport / AMF-01 / Service Dependency → cyan
H1 — Core Transport Router Failure → magenta
CONFIRMED / VALIDATED → turquoise
```

---

## 40. Example — Blocked Stage

```text
ZAKI — SIMULATION COPILOT

OFFLINE SIMULATION
Knowledge Gap Check • BLOCKED

Missing Context
Redundant MPLS Path Health Unknown

Affected Hypothesis
H1 — Core Transport Router Failure

Affected Pathway
Resilience & Failover

Next
Request backup-path telemetry
```

---

## 41. Example — Conflict

```text
ZAKI — CONFLICT DETECTED

Leading Hypothesis
H1 — Core Transport Router Failure

Authoritative Domain Attribution
RAN — PRIMARY

Reason
Current attribution is stale relative to the active hypothesis revision.

Next
Recompute attribution before trusting domain ownership.
```

---

## 42. Frontend Components

Prefer additive components:

```text
ZakiCompactOrb
ZakiContextHeader
ZakiSelectedContextCard
ZakiResponseSections
ZakiQuickActions
ZakiEntityToken
ZakiConflictBanner
ZakiReplayBadge
ZakiResponseLevelSwitcher
```

Reuse the current Zaki container where possible.

---

## 43. Frontend State

```ts
type ZakiUIState = {
  mode: "COMPACT" | "EXPANDED"
  selected_context?: ZakiSelectedContext
  response_level: "EXECUTIVE" | "OPERATOR" | "ENGINEER" | "DEEP_TECHNICAL"
  last_response_revision?: number
}
```

Do not duplicate authoritative run state here.

---

## 44. Backend Tests

Add focused tests:

```text
test_zaki_v2_selected_context_scoped_to_active_run
test_zaki_v2_selected_context_scoped_to_revision
test_zaki_v2_hypothesis_explanation_grounded
test_zaki_v2_pathway_explanation_grounded
test_zaki_v2_connection_explanation_grounded
test_zaki_v2_gap_explanation_grounded
test_zaki_v2_domain_explanation_uses_authoritative_attribution
test_zaki_v2_conflict_response
test_zaki_v2_replay_no_lookahead
test_zaki_v2_response_level
test_zaki_v2_structured_entities
test_zaki_v2_no_raw_html
test_zaki_v2_suggested_actions_governed
```

---

## 45. Frontend Tests

Add:

```text
test_zaki_compact_to_expanded
test_click_hypothesis_sets_zaki_context
test_click_pathway_sets_zaki_context
test_click_connection_sets_zaki_context
test_click_gap_sets_zaki_context
test_click_domain_sets_zaki_context
test_zaki_quick_actions_change_by_context
test_zaki_entity_structure_color_cyan
test_zaki_focus_color_magenta
test_zaki_confirmed_color_turquoise
test_zaki_body_text_not_overcolored
test_zaki_conflict_banner
test_zaki_replay_badge
test_zaki_response_level_switch
test_zaki_context_switch_clears_old_object
```

---

## 46. Visual Acceptance Tests

Verify:

```text
entity names are crisp
stage names are crisp
phase names are crisp
pathway names are crisp
cyan/magenta/turquoise remain distinguishable
labels readable at standard zoom
no excessive glow over text
body text stays neutral
selected state is obvious
confirmed state is obvious
```

---

## 47. Regression Gate

Before implementation:

```text
run Step 5 baseline
run Step 5.1 suite
run Step 5.2 suite
run Step 5.2.1 consistency tests
record baseline
```

After implementation, all prior tests must remain green.

Reject implementation if it breaks:

```text
authoritative run state
simulation orchestration
live reasoning
domain attribution
Zaki grounding
revision consistency
replay
hidden truth isolation
```

---

## 48. Definition of Done

```text
[ ] Zaki no longer feels like a disconnected side chat
[ ] any major reasoning object can become Zaki selected context
[ ] Zaki explains selected object from authoritative backend state
[ ] quick prompts are context-sensitive
[ ] responses use short operational sections
[ ] proactive micro-briefs only occur on material changes
[ ] cyan is used for operational structure
[ ] magenta is used for focus/attention
[ ] turquoise is used for confirmed/validated/resolved
[ ] entity/stage/phase/pathway names use clear typography
[ ] structured entity highlighting replaces raw HTML
[ ] conflict states are explicit
[ ] Live and Simulation context are clearly distinguished
[ ] replay has no lookahead
[ ] response levels work
[ ] Zaki actions remain governed
[ ] no new reasoning engine is introduced
[ ] all previous tests remain green
```

---

## Final Principle

> **Zaki 2.0 should not be a chatbot beside FikraCore.**

> **Zaki should be the contextual interface to FikraCore's reasoning.**

> **The backend reasons. The run state records. The UI visualizes. Zaki explains the exact object the operator is looking at.**

> **Cyan shows operational structure. Magenta shows current focus. Turquoise shows confirmed convergence.**
