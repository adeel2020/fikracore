# FikraCore UI Build Prompt — Neural Reasoning Map Experience

## Goal

Build the FikraCore Step 5 investigation UI to match the supplied reference image and the finalized product model.

This is **not another AI dashboard**.

The experience must feel like a **live, explainable telecom reasoning system** in motion, with a visually central Neural Reasoning Map showing how operational evidence activates reasoning pathways, how Intelligence Synthesis combines them, how H1–H4 hypotheses emerge and change, how gaps block confidence, and how validation, learning, and domain attribution progress.

The UI shell already exists. Preserve it. Upgrade the central reasoning experience and synchronize all surrounding panels to the same authoritative backend run state.

---

# 1. Preserve Existing Step 5 Shell

Keep:

```text
Top navigation
Scenario selector
Run ID
Run status
telecombrain MCP status
Pause / Stop
Live Simulation Journey
Unified Live Event Stream
Hypothesis Board
Knowledge Gaps
Service Impact
Next Best Evidence
Investigation Timeline
Zaki AI
Scenario Context
```

Do not redesign the entire application shell.

---

# 2. Main Layout

Use the following large-screen layout:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Top Navigation / Scenario / Run / Status / Controls                        │
├──────────────────────────────────────────────────────────────────────────────┤
│ Live Simulation Journey                                                     │
├───────────────┬──────────────────────────────────────────────┬───────────────┤
│ Live Event    │ Neural Reasoning Map                         │ Hypothesis    │
│ Stream        │                                              │ Board + Gaps  │
│               │                                              │               │
├───────────────┼──────────────────────────────────────────────┼───────────────┤
│ Scenario      │ Service Impact | NBE | Timeline             │ Zaki          │
│ Context       │                                              │               │
└───────────────┴──────────────────────────────────────────────┴───────────────┘
```

The Neural Reasoning Map is the visual center of gravity.

---

# 3. Visual Style

Use the supplied reference image as the primary styling reference.

Style:

```text
dark navy / deep blue background
thin cyan panel borders
glowing node halos
soft neon cyan, green, amber, purple, red accents
high contrast white labels
compact mono/technical secondary text
rounded dark glass panels
subtle inner shadows
restrained glow
```

Avoid:

```text
flat enterprise-dashboard cards
large white surfaces
generic KPI tiles
overly bright gradients
random sci-fi decoration
```

The design should feel:

```text
telecom-native
alive
operational
explainable
high-signal
```

---

# 4. Neural Reasoning Map Structure

The center must use this exact conceptual order:

```text
EVIDENCE
→ REASONING PATHWAYS
→ INTELLIGENCE SYNTHESIS
→ HYPOTHESES
→ VALIDATION & LEARNING
→ DOMAIN ATTRIBUTION
```

Important correction:

> **Hypotheses come after Intelligence Synthesis in the visual flow.**

The map should not show a separate oversized "Operational Conclusion" node.

Intelligence Synthesis is the central convergence layer.

---

# 5. Evidence Column

Display human-readable evidence categories:

```text
Alarms
Logs
Metrics
Traces
Changes
Tickets
User Impact
```

Each item shows:

```text
category icon
display name
count/status
active glow if currently contributing
```

Examples:

```text
Alarms — 3 active
Logs — 2 events
Metrics — 2 anomalies
Traces — 1 trace
Changes — 1 recent
Tickets — 1 customer
User Impact — Multiple reports
```

Evidence must be operationally grounded.

Do not show opaque IDs as visible labels.

---

# 6. Reasoning Pathways Column

Show:

```text
Operational Evidence
Service Dependency
Subscriber Journey
Change & Configuration
Traffic & Capacity
Control & Signaling
Resilience & Failure
Historical Pattern
Knowledge Enrichment
```

These are analytical perspectives, not telecom domains.

Visible pathway labels must remain human-readable.

---

# 7. Cross-Connections Between Evidence and Reasoning Pathways

This is a critical visual feature.

Do not use one-to-one simplistic links.

Use **many-to-many cross-connections**.

Examples:

```text
Alarms
→ Operational Evidence
→ Service Dependency
→ Change & Configuration

Logs
→ Operational Evidence
→ Subscriber Journey
→ Historical Pattern

Metrics
→ Traffic & Capacity
→ Service Dependency
→ Operational Evidence

Traces
→ Control & Signaling
→ Subscriber Journey
→ Resilience & Failure

Changes
→ Change & Configuration
→ Historical Pattern
→ Service Dependency

Tickets
→ Subscriber Journey
→ Knowledge Enrichment

User Impact
→ Subscriber Journey
→ Traffic & Capacity
→ Historical Pattern
```

Every visible connection must correspond to backend-authoritative state.

No random decorative lines.

---

# 8. Connection Visual Language

Use a single visual system.

Do not combine PCB circuitry and arrows as two unrelated styles.

Use:

> **structured organic neural conduits**

Characteristics:

```text
smooth curved splines
clear anchors
limited crossings
stable geometry
thin faint cyan base relation
brighter active glow
moving light pulse for current data flow
```

Semantic states:

```text
faint cyan
= valid dormant relationship

bright cyan
= currently active reasoning relationship

green pulse
= supporting a hypothesis

red pulse
= contradicting a hypothesis

amber pulse
= unresolved / needs evidence

purple pulse
= historical / learned context

grey faded
= rejected / inactive
```

Keep the geometry stable over time.

Only activation/glow/pulse should change.

---

# 9. Intelligence Synthesis

Place a large circular glowing FikraCore core at the visual center.

Title:

```text
FikraCore
Intelligence Synthesis
```

Subtitle:

```text
Converging multi-domain analysis
Creating a unified understanding
```

The center should visually absorb active reasoning pathways and emit synthesized outputs toward H1–H4.

The central node should pulse subtly when synthesis state changes.

Possible backend synthesis states:

```text
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
PARTIALLY_EXPLAINED
STRONGLY_SUPPORTED
ROOT_CANDIDATE
MODEL_INSUFFICIENT
```

Do not rely on a single numeric convergence score.

---

# 10. Hypotheses

Place H1–H4 directly after Intelligence Synthesis.

Use standard visible labels:

```text
H1 — MPLS Edge Router-07 Failure
H2 — SGW Overload
H3 — DNS Latency Issue
H4 — Policy Misconfiguration
```

Show:

```text
confidence
delta
status
leading marker
```

Example:

```text
H1 68% ↑ +7% LEADING
H2 28% ↓ -5%
H3 18% ↓ -2%
H4 12% ↓ -1%
```

Unknown confidence must render as:

```text
Unranked
```

not `0%`.

---

# 11. Hypothesis Connections

The output from Intelligence Synthesis to hypotheses must be visually distinct from Evidence→Pathway connections.

Use stronger glow and fewer lines.

Each synthesis→hypothesis connection should indicate:

```text
current support level
confidence trend
active testing state
```

Leading hypothesis:

```text
green glow
stronger path
```

Weakening hypothesis:

```text
blue/grey
reduced intensity
```

Rejected hypothesis:

```text
grey faded but still inspectable
```

---

# 12. Validation & Learning

Keep this area after hypotheses.

Validation visible state example:

```text
Transport Engineer Review Pending
```

Supported statuses:

```text
PENDING
ACCEPTED
REJECTED
MODIFIED
NEED_MORE_EVIDENCE
```

Learning visible states:

```text
No validated learning yet
Validated Learning Candidate
Ready for Promotion
```

Learning must remain gated behind validation.

---

# 13. Domain Attribution

Keep domain attribution at the far right / end of the reasoning journey.

Do not show domains as a source column.

Visible labels:

```text
Primary Domain — IP Transport
Contributing Domain — Mobile Core
Affected Domain — RAN
Affected Domain — DNS / Core Infrastructure
```

Use roles:

```text
PRIMARY
CONTRIBUTING
AFFECTED
INVOLVED
MONITOR_ONLY
NOT_RELEVANT
```

Domain attribution must appear only when backend reasoning supports it.

---

# 14. Live Simulation Journey

Preserve the existing top stepper.

Display human-readable labels:

```text
Trigger
Signal Flood
Correlation
Hypothesis Generation
Hypothesis Testing
Knowledge Gaps
Validation
Action
```

If backend uses more detailed internal states, keep them internal.

Use:

```text
green = complete
cyan = active
amber = blocked
grey = not started
```

Never advance by timer alone.

---

# 15. Live Event Stream

Keep the left-side event stream.

Use exact event names, e.g.:

```text
MPLS Edge Router-07 Failure Detected
Traffic drop on MPLS path
Service degradation alert
Customer impact report
Path trace confirms failure
BGP session state changed
Recent configuration change
CPU high on Router-07
```

Each event should show:

```text
timestamp
type
display name
short source/context
```

Do not mix reasoning events into this stream.

---

# 16. Knowledge Gaps

Keep the right-side Knowledge Gaps panel.

Use exact human-readable gap names.

Examples:

```text
Redundant MPLS path health unknown
Router-07 hardware health metrics missing
Recent change impact validation pending
```

Each gap can have:

```text
severity
affected hypothesis
affected pathway
required evidence
```

---

# 17. Next Best Evidence

Keep the lower center panel.

Example actions:

```text
Get Router-07 redundant path status
Retrieve detailed Router-07 health metrics
Validate recent change configuration
Check downstream device status
```

Status:

```text
READY
PENDING
IN_PROGRESS
COMPLETED
FAILED
```

Operator-triggered evidence requests only.

---

# 18. Service Impact

Keep the Service Impact panel.

Example:

```text
Enterprise APN      -55%  Severe
Internet Services   -42%  Degraded
VPN Services        -38%  Degraded
Voice (VoLTE)       +8%   Normal
```

Use explicit certainty internally:

```text
UNKNOWN
OBSERVED
ESTIMATED
INFERRED
CONFIRMED
```

Do not preload final impact from simulator truth.

---

# 19. Investigation Timeline

Keep the timeline.

Show:

```text
Incident detected
Multi-domain correlation
Knowledge gap detected
Requesting additional evidence
Awaiting response
Validation started
Domain attribution updated
Learning candidate created
```

Timeline entries must come from backend reasoning events.

---

# 20. Zaki AI

Keep Zaki on the lower-right.

Zaki should summarize exact backend state.

Example:

```text
The current analysis indicates MPLS Edge Router-07
as the leading cause with 68% confidence.

A key missing piece is the status of the redundant MPLS path.
Shall I fetch that now?
```

Suggested actions:

```text
Explain this
Show evidence
Test H2
What next?
```

Zaki never invents reasoning state.

---

# 21. Backend Synchronization

The entire UI must be a projection of one authoritative `InvestigationRun`.

Recommended:

```json
{
  "run_id": "RUN-...",
  "stage": "KNOWLEDGE_GAP_CHECK",
  "revision": 184,
  "sequence": 392,
  "evidence": [],
  "reasoning_pathways": [],
  "connections": [],
  "synthesis": {},
  "hypotheses": [],
  "knowledge_gaps": [],
  "next_best_evidence": [],
  "impact": {},
  "validation": {},
  "learning": {},
  "domain_attribution": {},
  "reasoning_focus": {}
}
```

Every panel consumes the same revision.

---

# 22. Human-Readable Naming Rule

Visible UI must never lead with opaque IDs.

Use:

```text
exact evidence name
exact pathway name
H1 / H2 / H3 / H4
exact knowledge gap name
exact validated fact
exact domain name
```

Opaque IDs remain internal for:

```text
audit
trace
deduplication
API references
debugging
```

---

# 23. Live Update Contract

Use snapshot + SSE/WebSocket.

Initial:

```text
GET /api/v1/fikracore/runs/{run_id}/snapshot
```

Live events:

```text
evidence_added
connection_activated
pathway_discovered
pathway_activated
hypothesis_created
hypothesis_updated
confidence_changed
gap_detected
evidence_requested
evidence_received
hypothesis_retested
synthesis_updated
validation_requested
validation_completed
domain_attribution_updated
learning_candidate_created
reasoning_focus_changed
```

Each event must include:

```text
run_id
revision
sequence
timestamp
```

---

# 24. Animation Rules

Animate only after backend state is accepted.

Correct flow:

```text
backend changes state
→ event emitted
→ frontend validates revision
→ store updates
→ visual pulse animates
```

Never let animation drive reasoning.

---

# 25. Cross-Connection Interaction

Clicking any Evidence→Pathway line must open an explanation.

Example:

```text
Alarms
→ Service Dependency
```

Explain:

```text
Why active:
Three affected services share the same upstream MPLS path.
```

Example:

```text
Changes
→ Change & Configuration
```

Explain:

```text
Why active:
CR-7721 completed 6 minutes before degradation.
```

This is mandatory.

---

# 26. Focus and Progressive Disclosure

Default:

```text
show active evidence
show active pathways
show H1–H4
show material gaps
show synthesis
show current domain attribution
```

On hover:

```text
emphasize local neighborhood
```

On click:

```text
expand relation detail
dim unrelated links
```

Do not display every dormant relation at full opacity.

---

# 27. Responsive Behavior

Desktop:

```text
3-column shell
full Neural Reasoning Map
```

Smaller widths:

```text
event stream collapsible
hypothesis/gap panel collapsible
map remains central
details move below map
```

Do not reduce the map to a tiny static thumbnail.

---

# 28. Acceptance Scenario

Use:

```text
H4-WT-001
MPLS Edge Router Failure
```

Expected state:

```text
Stage: Knowledge + Gap Check
H1: MPLS Edge Router-07 Failure — 68% leading
H2: SGW Overload — 28%
H3: DNS Latency Issue — 18%
H4: Policy Misconfiguration — 12%

Knowledge Gaps:
Redundant MPLS path health unknown
Router-07 hardware health metrics missing
Recent change impact validation pending

Primary Domain:
IP Transport
```

The map must show active cross-connections consistent with this run.

---

# 29. Required Frontend Tests

```text
test_shell_preserved
test_neural_reasoning_map_renders
test_evidence_to_pathway_many_to_many_links
test_active_connections_backend_driven
test_hypotheses_after_synthesis
test_h1_h4_visible_labels
test_gap_names_human_readable
test_domain_attribution_far_right
test_connection_click_explains_reason
test_stale_revision_rejected
test_reduced_motion
test_no_hydration_errors
```

---

# 30. Definition of Done

```text
[ ] existing Step 5 shell preserved
[ ] Neural Reasoning Map is central
[ ] Evidence appears before Reasoning Pathways
[ ] Intelligence Synthesis appears before Hypotheses
[ ] H1–H4 appear after synthesis
[ ] many-to-many Evidence→Pathway cross-connections are visible
[ ] every cross-connection is backend-authoritative
[ ] active lines illuminate dynamically
[ ] geometry remains stable
[ ] no random decorative links
[ ] Knowledge Gaps remain visible
[ ] Validation & Learning remain stage-gated
[ ] Domain Attribution stays at the end
[ ] all visible labels are human-readable
[ ] all panels use the same backend revision
[ ] Zaki reflects exact run state
[ ] UI feels live and explainable, not like another AI dashboard
```

---

# Final Product Principle

> **The Neural Reasoning Map is the live visual explanation of FikraCore's running investigation.**

> **Evidence activates reasoning pathways, Intelligence Synthesis converges those pathways, hypotheses emerge and evolve, gaps expose uncertainty, validation governs trust, and domain attribution appears only when the reasoning supports it.**
