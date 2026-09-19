# FikraCore — Step 5 v3 Unified Capability & Simulator Experience Layer

## Purpose

Step 5 v3 turns the validated FikraCore reasoning platform into a unified operational product experience.

This revision explicitly anchors the user experience to the objectives and UI direction defined in:

```text
fikracore-simulator-master-prompt-v3.md
```

while preserving the unified capability architecture already established in Step 5 v2.

The validated foundation entering Step 5 is:

```text
H1 — Reason
H2 — Recognize the Unknown
H3 — Learn / Reuse
H4 — Predict / Resilience

Step 4.5 — Live gbrain MCP Smoke
Step 4.6 — Live MCP Parity & Benchmark Validation
Step 4.7 — Knowledge Inventory & Coverage Validation
```

The governing principle is:

> **One Telecom Brain. One Capability Layer. One Shared State. Multiple Consistent Experiences.**

And the primary UX principle is:

> **The UI must make FikraCore’s reasoning visible, not merely display results.**

---

# 1. Step 5 v3 Validation Question

Answer:

> Can every validated FikraCore capability be invoked consistently through CLI, Simulator UI, Curated Demo Mode, Mark / Zaki, and API, while the UI visibly represents hypothesis testing, falsification, knowledge gaps, validated learning, and proactive resilience without duplicating reasoning logic or creating conflicting state?

---

# 2. UX North Star

The Simulator UI must be designed from the objectives in:

```text
fikracore-simulator-master-prompt-v3.md
```

The UI should visibly support the following operational journey:

```text
What happened?
        ↓
Why did it happen?
        ↓
What evidence supports or contradicts that explanation?
        ↓
What do we not know?
        ↓
What validated knowledge should we retain?
        ↓
What could fail next?
        ↓
What should we protect or change?
```

Leadership shorthand:

```text
Investigate
Discover
Learn
Predict
```

H1–H4 remain validation-stage labels, not the primary operational navigation.

---

# 3. Core Outcome

The experience must embody:

> **From Observability to Context to Action**

through:

```text
Hypothesis
Falsification
Discovery
Validation
Learning
Proactive Resilience
```

---

# 4. Preconditions

Step 5 v3 begins only after:

```text
H1 SUPPORTED
H2 SUPPORTED
H3 SUPPORTED
H4 SUPPORTED

LIVE_MCP_SMOKE_SUPPORTED
LIVE_MCP_PARITY_SUPPORTED
KNOWLEDGE_INVENTORY_SUPPORTED
```

Current validated chain:

```text
Live gbrain MCP
→ telecombrain
→ Canonical Resolution
→ GbrainTelecomBrainProvider
→ H1 / H2 / H3 / H4
→ Knowledge Inventory
→ Mark / Zaki
```

---

# 5. Step 5 v3 Structure

Step 5 v3 has two coordinated implementation tracks:

```text
Step 5A — Unified Capability Architecture
Step 5B — Unified Simulator Experience
```

These must be implemented together against the same structured state.

---

# 6. Step 5A — Unified Capability Architecture

Step 5A includes:

```text
Unified capability registry
Unified command model
Shared scenario resolver
Shared naming resolver
Shared session/state model
Shared presentation model
API contract
Backward-compatible CLI wrappers
Role and permission boundaries
Observability
Auditability
Regression protection
```

---

# 7. Step 5B — Unified Simulator Experience

Step 5B includes:

```text
Investigate workspace
Discover workspace
Learn workspace
Predict workspace
Knowledge workspace
Scenario Simulator
Benchmark / Evaluation workspace
Curated Demo Mode
Embedded Mark / Zaki
```

The UI must not be organized primarily as:

```text
H1
H2
H3
H4
```

Those remain benchmark and demo labels.

---

# 8. Target Architecture

```text
                              FikraCore
                                 │
                     Unified Capability Layer
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
       CLI                  Simulator UI             Mark / Zaki
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                          API / Automation
                                 │
                     Shared Structured State
                                 │
                          KnowledgeProvider
                                 │
                         Live telecombrain
                                 │
                          gbrain MCP
```

---

# 9. Core Capability Registry

Create a single registry for:

```text
investigate
discover
learn
predict
simulate
inspect
present
benchmark
report
validate
```

Each capability defines:

```text
name
description
input schema
output schema
permissions
supports CLI
supports UI
supports Mark / Zaki
supports Demo Mode
supports API
read/write behavior
```

---

# 10. H1–H4 Mapping

```text
H1 — Reason
→ investigate

H2 — Recognize the Unknown
→ discover

H3 — Learn / Reuse
→ learn

H4 — Predict / Resilience
→ predict
```

Supporting shared capabilities:

```text
simulate
inspect
present
benchmark
report
validate
```

---

# 11. Primary Operator Navigation

Recommended top-level navigation:

```text
Home
Investigate
Discover
Learn
Predict
Knowledge
Simulator
Benchmarks
Zaki
```

Optional system/admin areas:

```text
Reports
Settings
Platform Health
```

---

# 12. UX Visual Direction

The Simulator UI must be:

```text
light
clean
telecom-operations focused
low-clutter
high-information-density without visual noise
```

Recommended design language:

```text
white / very light grey background
dark navy typography
subtle borders
limited accent colors
minimal glow
large central graph workspace
human-readable labels
clear state badges
```

Avoid:

```text
cyberpunk look
gaming-dashboard styling
excessive neon
too many cards
decorative animation that competes with reasoning
```

---

# 13. Main Simulator Screen

The main simulator screen should show:

```text
Scenario
Simulation Status
Service Impact
Domains Involved
Raw Alarms
Correlated Events
Current Hypotheses
Root Candidate
Confidence
Topology Gaps
Learning Status
Knowledge Source
```

Ground Truth must remain hidden during operational reasoning and become available only in evaluator / benchmark context.

---

# 14. Recommended Main Layout

```text
┌────────────────────────────────────────────────────────────────────┐
│ FikraCore   Investigate Discover Learn Predict Knowledge     Zaki │
├────────────────────────────────────────────────────────────────────┤
│ Scenario | Simulation Status | Service Impact | Domains | Source   │
├──────────────────┬───────────────────────────────────┬─────────────┤
│                  │                                   │             │
│ EVENT / TIMELINE │        CAUSAL / SERVICE GRAPH     │ HYPOTHESES  │
│                  │                                   │             │
│ Alarms           │    Service → Domain → Function    │ #1          │
│ Metrics          │     → Node → Transport Path       │ Confidence  │
│ Logs             │                                   │ Supports    │
│ Traces           │       Highlighted causal path     │ Against     │
│ Changes          │                                   │ Missing     │
│ Tickets          │                                   │ Test        │
│ Healthy Signals  │                                   │             │
├──────────────────┴───────────────────────────────────┴─────────────┤
│ Evidence | Unknowns | Knowledge Gaps | Learning | Resilience      │
└────────────────────────────────────────────────────────────────────┘
```

---

# 15. Central Causal / Service Graph

The central graph should represent the semantic model across:

```text
Service
→ Domain
→ Service Cluster
→ Network Function
→ Node
→ Pod / VM
→ Interface
→ Protocol
→ Infrastructure
→ Transport Path
→ Customer Segment
```

The graph should support filtering by:

```text
domain
service
entity type
relationship type
knowledge state
impact state
```

---

# 16. Required Graph Visual States

The UI must visually distinguish:

```text
ROOT CANDIDATE
SYMPTOM
HEALTHY
UNKNOWN
CANDIDATE RELATIONSHIP
CONFIRMED
REJECTED
```

These states must be tied to actual structured reasoning state.

Do not use decorative coloring without semantic meaning.

---

# 17. Relationship Visual States

Examples:

```text
Confirmed relationship
Candidate relationship
Rejected relationship
Unknown boundary
Observed propagation
Predicted propagation
```

Each should be visually distinct.

---

# 18. Hypothesis Panel — First-Class Component

The Hypothesis Panel must be a primary UI element.

For each hypothesis display:

```text
Rank
Human-readable hypothesis
Confidence
Causal role
Supporting evidence
Contradicting evidence
Missing evidence
Assumptions
Status
```

Example:

```text
#1 IP Transport
Confidence: 82%

SUPPORTS
✓ Interface errors precede impact
✓ Packet loss matches service degradation
✓ Shared upstream dependency
✓ Blast radius explained

AGAINST
✕ No physical-link-down alarm

MISSING
? Adjacent router counters

[Test Hypothesis]
```

---

# 19. Falsification Must Be Visible

The UI must make it obvious when a hypothesis is:

```text
supported
contradicted
retained
rejected
needs more evidence
```

A rejected hypothesis should remain visible in reasoning history because rejection is useful evidence.

---

# 20. Next-Best-Evidence Interaction

For uncertain hypotheses show:

```text
What evidence would reduce uncertainty most?
```

Suggested presentation:

```text
Next Best Evidence

1. Adjacent router counters
2. Traceroute / path trace
3. Interface error history
4. Change record correlation
```

Each evidence request should include:

```text
reason
expected information gain
cost/latency where available
```

---

# 21. Unified Timeline

The timeline should synchronize:

```text
Change Requests
Alarms
Metrics
Logs
Traces
Customer Impact
Hypothesis Creation
Evidence Requests
Human Validation
Recovery
```

Filters:

```text
domain
entity
service
event type
correlation ID
time window
```

---

# 22. Evidence Timeline Semantics

Timeline items should show:

```text
Observed
Inferred
Confirmed
Rejected
```

where appropriate.

The UI must preserve provenance.

---

# 23. Investigate Workspace

Primary question:

> **What happened and why?**

Show:

```text
incident/service impact
alarm storm collapse
correlated event groups
causal graph
hypothesis ranking
evidence support/contradiction
next-best evidence
root candidate
confidence
terminal state
```

Terminal states may include:

```text
EXPLAINED
PARTIALLY_EXPLAINED
UNRESOLVED
CONFLICTING_EVIDENCE
MODEL_INSUFFICIENT
INSUFFICIENT_EVIDENCE
```

---

# 24. Discover Workspace

Primary question:

> **What do we not know?**

This is the dedicated H2 / knowledge-gap experience.

Show:

```text
MODEL_INSUFFICIENT state
known path
unexplained residual
gap boundary
gap type
candidate relationship
next-best evidence
knowledge-state status
```

Example:

```text
MODEL INSUFFICIENT

Known:
Packet Gateway-01
→ Transport Router-01

Observed:
Traffic continues through an unexplained hop.

Gap Boundary:
Transport Router-01
→ ?
→ Data Center Gateway-01

Next Best Evidence:
Traceroute
Adjacent router counters
Topology inventory
```

---

# 25. Discover Workspace Safety

The UI must not display a hidden node or hidden link as confirmed merely because the simulator knows it.

Use:

```text
UNKNOWN
CANDIDATE
INFERRED
CONFIRMED
```

correctly.

---

# 26. Learn Workspace

Primary question:

> **What validated knowledge should we retain?**

Do not show generic AI learning percentages.

Use the operational learning lifecycle:

```text
Incident A
→ Knowledge Gap
→ Candidate Knowledge
→ SME / HITL Validation
→ Approved Knowledge
→ Promotion
→ Future Incident B
→ Before / After Comparison
```

---

# 27. Learning Status Model

Display:

```text
CANDIDATE
NEEDS_REVIEW
ACCEPTED
REJECTED
MODIFIED
PROMOTED
STALE
ROLLED_BACK
```

---

# 28. H3 Before / After View

The Learn workspace should compare:

```text
Before Learning
vs
After Validated Learning
```

Measure:

```text
root-cause rank
evidence requests
reasoning steps
false hypotheses
confidence convergence
knowledge reuse
```

---

# 29. Learning Dashboard Metrics

Where evidence exists, show:

```text
Validated Episodes
Scenario Coverage
Workflow Accuracy
Human Correction Rate
Confidence Calibration
Readiness
```

Do not create arbitrary learning percentages.

---

# 30. Predict Workspace

Primary question:

> **What could fail and what should we protect?**

H4 is a forward-reasoning experience.

Flow:

```text
Hypothetical Failure / Change
→ Forward Causal Propagation
→ Affected Services
→ Blast Radius
→ Critical Failure Surface
→ Redundancy / Failover / Capacity Risks
→ Mitigation
→ Re-simulate
```

---

# 31. Predict Graph Visual Mode

The central graph should switch from:

```text
Backward Incident Reasoning
```

to:

```text
Forward Failure Propagation
```

Visualize:

```text
trigger
propagation path
absorbed failover
failed failover
capacity bottleneck
shared dependency
service impact
customer impact
```

---

# 32. Critical Failure Surface View

Show:

```text
Key components
Shared dependencies
Single points of failure
Failover assumptions
Capacity constraints
Change-risk intersections
```

The UI should clearly distinguish:

```text
known vulnerability
simulated impact
uncertain dependency
```

---

# 33. Mitigation Comparison

Support side-by-side mitigation comparison:

```text
Mitigation A
Mitigation B
Mitigation C
```

Show:

```text
impact reduction
blast-radius reduction
risk reduction
cost / complexity placeholder where available
residual risk
```

---

# 34. Knowledge Workspace

Knowledge becomes a first-class UI area after Step 4.7.

Primary question:

> **What does FikraCore know right now?**

Show:

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

---

# 35. Current Knowledge Summary

The UI should be ready to display live values such as:

```text
132 pages
190 unique relationships
5 domains
6 services
73.5% overall coverage
PARTIALLY_COVERED
```

Current weak areas may include:

```text
Transport sparse
RAN sparse
OCS absent
Mobile Core ↔ OCS missing
IMS ↔ Transport missing
2 operational orphans
11.4% stale knowledge
```

Values must always come from live Step 4.7 inventory output.

---

# 36. Knowledge Health View

Recommended presentation:

```text
Overall Coverage: 73.5%
Status: Partially Covered

Strong:
Mobile Core

Sparse:
Transport
RAN

Missing:
OCS

Cross-Domain Gaps:
Mobile Core ↔ OCS
IMS ↔ Transport
```

---

# 37. Knowledge State Distribution

Where available show:

```text
CONFIRMED
INFERRED
CANDIDATE
REJECTED
STALE
UNKNOWN
```

Do not infer a state when the data does not support one.

---

# 38. Simulator Workspace

The Simulator workspace should provide:

```text
Scenario Library
Run Scenario
Custom Scenario
Replay Scenario
Compare Runs
Scenario Results
```

It should support both benchmark and ad-hoc simulation.

---

# 39. Scenario Library

Each scenario should expose:

```text
stable ID
display name
aliases
stage
capabilities
domains
services
difficulty
demo metadata
benchmark status
```

---

# 40. Human-Readable Scenario Resolution

Use:

```text
Exact ID
→ Exact Display Name
→ Exact Alias
→ Normalized Match
→ Semantic Match
→ Disambiguation
```

Never invent a scenario ID.

---

# 41. Scenario Page

Show:

```text
Scenario Name
Stable ID
Objective
Stage
Capability
Affected Domains
Affected Services
Difficulty
Knowledge Source
Current Status
Run
Inspect
Present
```

---

# 42. Benchmark Workspace

The Benchmark workspace should answer:

```text
Is FikraCore actually improving?
Is it calibrated?
Does it generalize?
Does it hallucinate?
Does learning help future incidents?
Does live MCP preserve reasoning parity?
```

---

# 43. Benchmark Metrics

Support the validated metric families:

```text
Root Cause Accuracy
Root Domain Accuracy
False Correlation Rate
Alarm Reduction Ratio
Blast-Radius Precision
Blast-Radius Recall
Time to First Useful Hypothesis
Evidence Queries Required
Human Correction Rate
Confidence Calibration
Topology-Gap Detection
Missing-Node Discovery
Missing-Edge Precision / Recall
False Relationship Rate
Story Factual Accuracy
Story Provenance Coverage
FCAPS Classification Accuracy
Workflow Recommendation Accuracy
Baseline vs Post-Learning Improvement
```

---

# 44. Mark / Zaki Embedding

Zaki should be embedded into the primary UI.

Recommended form:

```text
persistent right-side assistant
or
expandable bottom panel
```

Zaki should not be a separate product.

---

# 45. Mark / Zaki Responsibility

Zaki is:

```text
interaction
orchestration
presentation
voice/chat
```

Zaki is not:

```text
causal authority
topology source of truth
Hidden Truth evaluator
```

---

# 46. Zaki Functional Routing

Support requests such as:

```text
Tell me the incident story for INC-123
Show the journey for TT-984210
Why is Mobile Data impacted?
Test the Transport hypothesis
What evidence should we check next?
Run the MPLS Edge Router failure simulation
What would happen if this router failed during the change?
What does FikraCore know about Mobile Core?
Where are the biggest knowledge gaps?
```

Each must route to the correct shared capability.

---

# 47. Zaki Shared-State Rule

Zaki must consume the same structured state as the UI.

```text
Capability Engine
      ↓
Shared Structured State
      ├── Simulator UI
      ├── Curated Demo Mode
      └── Zaki
```

No separate reasoning implementation.

---

# 48. Incident Storyteller Integration

The Incident Storyteller should remain a distinct capability using shared FikraCore context.

It should consume:

```text
incident state
evidence
reasoning
validated conclusions
provenance
```

It must not become the authority for RCA.

---

# 49. Customer Ticket Journey Integration

Customer Ticket Journey should remain distinct but share:

```text
service context
incident context
topology
ticket state
provisioning evidence
impact state
```

through the same FikraCore knowledge context.

---

# 50. Curated Demo Mode

Curated Demo Mode must use the same backend and scenario state.

It may control:

```text
step-by-step reveal
highlighting
narration
technical detail
reset
replay
```

It must not change:

```text
reasoning
evidence
confidence
scenario truth
```

---

# 51. Curated Demo Journey

Recommended sequence:

```text
H1 — Reason
H2 — Recognize the Unknown
H3 — Learn
H4 — Predict
```

Presentation language:

```text
What happened?
What don't we know?
What did we learn?
What could fail next?
```

---

# 52. Simple vs Technical View

Support:

```text
Simple View
Technical View
```

Simple View:

```text
human-readable labels
service/business impact
concise explanations
```

Technical View:

```text
canonical IDs
raw link types
evidence IDs
scores
provenance
provider details
```

---

# 53. Human-Readable Naming Policy

Prefer:

```text
Transport Router-01
MPLS Edge Router-07
Data Center Gateway-01
User Plane Function-01
Packet Gateway-01
```

Canonical IDs remain available in Technical View.

---

# 54. Human-Readable Relationship Policy

Examples:

```text
DEPENDS_ON → Depends on
ROUTES_THROUGH → Routes through
HOSTED_ON → Hosted on
SUPPORTS_SERVICE → Supports service
MONITORED_BY → Monitored by
FAILS_OVER_TO → Fails over to
```

---

# 55. Shared Structured State

Recommended model:

```json
{
  "session": {},
  "scenario": {},
  "capability": {},
  "impact": {},
  "timeline": [],
  "topology": {},
  "evidence": [],
  "reasoning": {},
  "knowledge_gap": {},
  "learning": {},
  "resilience": {},
  "knowledge_inventory": {},
  "provenance": {},
  "presentation": {}
}
```

---

# 56. Shared Scenario Resolver

Use the same resolver in:

```text
CLI
Simulator UI
Curated Demo Mode
Zaki
API
```

---

# 57. Shared Naming Resolver

Use the same naming resolver in:

```text
CLI
Simulator UI
Curated Demo Mode
Zaki
Reports
API presentation payloads
```

---

# 58. CLI Goal

Primary operator-facing CLI:

```text
fikracore investigate
fikracore discover
fikracore learn
fikracore predict
fikracore simulate
fikracore inspect
fikracore present
fikracore benchmark
fikracore report
fikracore validate
```

Legacy commands remain supported as wrappers.

---

# 59. Existing CLI Compatibility

Current commands include:

```text
investigate
discover
evaluate
validate-candidate
validate
benchmark
diagnose-benchmark
diagnose-run
generate-h2-scenarios
validate-h2-scenarios
run-h2-benchmark
diagnose-h2-run
h2-report
h2-demo
generate-h3-learning-units
validate-h3-learning-units
promote-knowledge
rollback-promotion
run-h3-benchmark
h3-report
h3-demo
predict
inspect
mcp-smoke
benchmark-parity
inspect-parity
present
generate-h4-scenarios
validate-h4-scenarios
run-h4-benchmark
h4-report
h4-demo
```

Step 5 v3 must preserve backward compatibility.

---

# 60. Legacy Command Rule

Old commands become thin wrappers.

Example:

```text
fikracore run-h4-benchmark
        ↓
Legacy Wrapper
        ↓
Benchmark Capability
        ↓
BenchmarkService.run(stage="h4")
```

No duplicated logic.

---

# 61. Unified Learn Command

Support:

```bash
fikracore learn inspect <candidate>
fikracore learn validate <candidate>
fikracore learn promote <candidate>
fikracore learn rollback <promotion-id>
fikracore learn generate
```

Legacy mappings:

```text
validate-candidate → learn validate
promote-knowledge → learn promote
rollback-promotion → learn rollback
```

---

# 62. Unified Inspect Command

Support:

```bash
fikracore inspect knowledge
fikracore inspect knowledge --domain mobile-core
fikracore inspect knowledge --type incident
fikracore inspect knowledge --coverage
fikracore inspect knowledge --gaps
fikracore inspect knowledge --orphans
fikracore inspect knowledge --technical
fikracore inspect knowledge --json

fikracore inspect live-knowledge
fikracore inspect mcp
fikracore inspect parity SCN-001
fikracore inspect scenario SCN-001
fikracore inspect reasoning <run-id>
fikracore inspect topology <entity>
```

---

# 63. Unified Benchmark Command

Recommended:

```bash
fikracore benchmark h1
fikracore benchmark h2
fikracore benchmark h3
fikracore benchmark h4
fikracore benchmark parity
fikracore benchmark all
```

---

# 64. Unified Report Command

Recommended:

```bash
fikracore report h1
fikracore report h2
fikracore report h3
fikracore report h4
fikracore report parity
fikracore report knowledge
```

---

# 65. Unified Validate Command

Recommended:

```bash
fikracore validate scenarios --stage h2
fikracore validate learning-units
fikracore validate candidate <id>
fikracore validate knowledge-inventory
fikracore validate parity
```

---

# 66. Unified Simulate Command

Recommended:

```bash
fikracore simulate <scenario>
fikracore simulate generate --stage h2
fikracore simulate generate --stage h4
fikracore simulate replay <scenario>
```

---

# 67. Presentation Command

Recommended:

```bash
fikracore present <scenario>
fikracore present <scenario> --mode investigation
fikracore present <scenario> --mode demo
fikracore present --stage h2 --mode demo
fikracore present --stage h3 --mode demo
fikracore present --stage h4 --mode demo
```

---

# 68. API Layer

Expose:

```text
investigate()
discover_gap()
inspect_knowledge()
validate_knowledge()
promote_knowledge()
rollback_knowledge()
predict_what_if()
simulate()
inspect()
present()
benchmark()
report()
validate()
```

---

# 69. API Response Model

Recommended:

```json
{
  "request_id": "...",
  "capability": "predict",
  "scenario": {},
  "result": {},
  "knowledge_source": {},
  "provenance": {},
  "confidence": 0.0,
  "limitations": [],
  "presentation": {}
}
```

---

# 70. Knowledge Source Visibility

Show:

```text
Knowledge Source:
Live telecombrain via gbrain MCP
```

or:

```text
Knowledge Source:
Frozen Benchmark Snapshot
```

---

# 71. Unified Error Model

Use:

```text
SCENARIO_NOT_FOUND
AMBIGUOUS_SCENARIO
MODEL_INSUFFICIENT
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
KNOWLEDGE_PROVIDER_UNAVAILABLE
PERMISSION_DENIED
VALIDATION_REQUIRED
PROMOTION_BLOCKED
INVENTORY_UNAVAILABLE
```

---

# 72. Empty-Result Safety

Distinguish:

```text
EMPTY_VALID_RESULT
PAGE_NOT_FOUND
MCP_REQUEST_FAILED
AUTH_FAILED
TIMEOUT
PAGINATION_FAILED
```

Never treat provider failure as empty valid knowledge.

---

# 73. Read vs Write Separation

Separate:

```text
read-only reasoning
candidate creation
human validation
knowledge promotion
rollback
```

---

# 74. Role Model

Prepare for:

```text
Viewer
Domain Engineer
SME
Validator
Administrator
```

Suggested access:

```text
Viewer
→ inspect, present

Domain Engineer
→ investigate, discover, predict, simulate

SME / Validator
→ validate learned knowledge

Administrator
→ controlled promotion / rollback / configuration
```

---

# 75. H3 Governance

Preserve:

```text
candidate
validation
approval
promotion
reuse
rollback
audit
```

Human validation remains an operational governance decision, not Hidden Truth.

---

# 76. Observability

Track:

```text
capability
scenario
provider
duration
result state
confidence
error
evidence count
reasoning steps
interface source
```

Prepare for Grafana LGTM.

---

# 77. Auditability

Preserve:

```text
who invoked
what capability
which scenario
which knowledge version
which provider
which evidence
which result
which validation
which promotion
which recommendation
```

---

# 78. CLI / UI / Zaki Equivalence

Example:

```text
CLI:
fikracore predict "MPLS Edge Router Failure"

UI:
Predict → MPLS Edge Router Failure

Zaki:
"What if the MPLS edge router fails?"

API:
POST /predict
```

All invoke the same capability.

---

# 79. No Duplicate Reasoning Logic

Forbidden:

```text
CLI-specific RCA engine
UI-specific what-if engine
Zaki-specific scenario engine
demo-only root cause logic
separate knowledge inventory logic in UI
```

Allowed:

```text
different presentation
same capability execution
```

---

# 80. Hidden Truth Isolation

Forbidden:

```text
Hidden Truth → telecombrain
Hidden Truth → KnowledgeProvider
Hidden Truth → Zaki
Hidden Truth → Simulator operational state
Hidden Truth → learning promotion
```

Allowed:

```text
Hidden Truth → Evaluator
```

---

# 81. Recommended Module Structure

```text
telecom_brain/
├── capabilities/
│   ├── registry.py
│   ├── investigate.py
│   ├── discover.py
│   ├── learn.py
│   ├── predict.py
│   ├── simulate.py
│   ├── inspect.py
│   ├── benchmark.py
│   ├── report.py
│   ├── validate.py
│   └── present.py
├── presentation/
│   ├── naming.py
│   ├── scenario_resolver.py
│   ├── ui_adapter.py
│   └── zaki_bridge.py
├── knowledge/
│   ├── inventory.py
│   ├── coverage.py
│   └── provider.py
├── api/
│   └── capability_api.py
├── investigation/
│   └── cli.py
└── simulator/
```

Adapt to the existing repository.

---

# 82. UI Component Structure

Recommended frontend component families:

```text
AppShell
PrimaryNavigation
ScenarioHeader
ServiceImpactSummary
CausalGraph
HypothesisPanel
EvidenceTimeline
KnowledgeGapPanel
LearningLifecyclePanel
ResiliencePanel
KnowledgeHealthPanel
BenchmarkPanel
ZakiPanel
TechnicalDetailsDrawer
```

---

# 83. UI State Contract

The UI should never parse raw reasoning logs to infer state.

It should consume explicit structured state such as:

```text
hypothesis.status
evidence.support
evidence.contradiction
knowledge_gap.boundary
knowledge_gap.state
learning.status
resilience.propagation
```

---

# 84. Accessibility and Readability

Require:

```text
clear contrast
readable labels
keyboard-accessible navigation
tooltips for technical terms
no color-only semantics
responsive layout
```

Use icons + labels + state text together.

---

# 85. Performance Expectations

The UI should progressively render:

```text
scenario shell
knowledge context
graph
evidence
reasoning
```

Long-running simulation should expose progress rather than appear frozen.

---

# 86. Curated Demo Presentation Integrity

Demo Mode may simplify presentation but must not:

```text
remove contradicting evidence
inflate confidence
skip uncertainty
invent root cause
show Hidden Truth before evaluation
```

---

# 87. Benchmark / Demo Separation

Benchmark mode:

```text
scientific
measurable
evaluator-driven
```

Demo mode:

```text
guided
simplified
narrative
```

Both must use the same reasoning output.

---

# 88. Regression Baseline

Current baseline before Step 5:

```text
233 / 233 tests passing
```

Step 5 v3 must not reduce this.

---

# 89. Test Requirements — Capability Layer

Add:

```text
test_capability_registry
test_every_cli_command_bound_to_capability
test_legacy_cli_wrappers
test_shared_scenario_resolver
test_shared_naming_resolver
test_shared_state_model
test_cli_ui_zaki_same_capability
test_api_structured_output
test_error_model_consistent
test_permissions_enforced
test_read_write_boundaries
```

---

# 90. Test Requirements — UI Reasoning Integrity

Add:

```text
test_ui_shows_supporting_and_contradicting_evidence
test_ui_shows_rejected_hypothesis
test_ui_model_insufficient_state
test_ui_candidate_relationship_not_confirmed
test_ui_hidden_truth_not_visible_operationally
test_ui_h3_before_after_state
test_ui_h4_forward_propagation_state
test_ui_knowledge_inventory_state
test_zaki_uses_shared_state
test_demo_mode_does_not_change_reasoning
```

---

# 91. Test Requirements — Knowledge Experience

Add:

```text
test_knowledge_summary_uses_live_inventory
test_knowledge_gap_view_matches_step47
test_stale_knowledge_visible
test_orphan_entities_visible
test_cross_domain_gap_visible
```

---

# 92. Test Requirements — Compatibility

Preserve:

```text
H1 regressions
H2 regressions
H3 regressions
H4 regressions
Step 4.5 smoke
Step 4.6 parity
Step 4.7 inventory
legacy CLI
```

---

# 93. Definition of Done — Step 5A

Step 5A is complete when:

```text
[ ] one capability registry exists
[ ] investigate is unified
[ ] discover is unified
[ ] learn is unified
[ ] predict is unified
[ ] simulate is unified
[ ] inspect is unified
[ ] present is unified
[ ] benchmark is unified
[ ] report is unified
[ ] validate is unified
[ ] legacy CLI commands still work
[ ] every CLI command maps to capability layer
[ ] scenario resolver is shared
[ ] naming resolver is shared
[ ] API contract exists
[ ] error model exists
[ ] permissions exist
[ ] audit trail exists
```

---

# 94. Definition of Done — Step 5B

Step 5B is complete when:

```text
[ ] primary navigation uses Investigate / Discover / Learn / Predict
[ ] UI is light and low-clutter
[ ] causal/service graph is central
[ ] hypothesis panel shows Supports / Against / Missing
[ ] falsification is visible
[ ] timeline unifies evidence
[ ] MODEL_INSUFFICIENT has dedicated UX
[ ] knowledge gap boundary is visible
[ ] H3 shows validated learning lifecycle
[ ] H3 shows before / after improvement
[ ] H4 uses forward propagation UX
[ ] blast radius is visible
[ ] critical failure surface is visible
[ ] mitigations can be compared
[ ] Knowledge workspace is first-class
[ ] Step 4.7 inventory powers knowledge views
[ ] Zaki is embedded
[ ] Zaki uses shared state
[ ] Incident Storyteller integrates through shared context
[ ] Customer Ticket Journey integrates through shared context
[ ] Demo Mode uses same reasoning state
[ ] Hidden Truth remains hidden until evaluation
```

---

# 95. Step 5 v3 Decision

Classify:

```text
STEP5_SUPPORTED
STEP5_PARTIALLY_SUPPORTED
STEP5_NOT_SUPPORTED
```

---

# 96. STEP5_SUPPORTED Criteria

Use when:

```text
all primary capabilities use the shared capability layer
UI visibly represents reasoning and uncertainty
all interfaces consume the same structured state
legacy commands remain compatible
knowledge inventory is integrated
Zaki remains grounded
Hidden Truth leakage is zero
regression suite remains green
```

---

# 97. Final Report Questions

The final report must answer:

```text
1. Is there one capability registry?
2. Does every CLI command map to a capability?
3. Are legacy commands wrappers only?
4. Do CLI, UI, Zaki, and API call the same implementation?
5. Is the same scenario resolver used everywhere?
6. Is the same naming resolver used everywhere?
7. Is the central UI graph reasoning-aware?
8. Can users see supporting and contradicting evidence?
9. Can users see rejected hypotheses?
10. Can users see MODEL_INSUFFICIENT clearly?
11. Can users see knowledge-gap boundaries?
12. Can users see validated learning before/after?
13. Can users run forward What-If propagation?
14. Can users see blast radius and critical failure surface?
15. Can users inspect what FikraCore knows?
16. Can users inspect what FikraCore does not know?
17. Is Step 4.7 inventory used by UI and Zaki?
18. Does Curated Demo Mode preserve reasoning integrity?
19. Is Zaki grounded in shared state?
20. Is Hidden Truth leakage still zero?
21. Are all prior regressions green?
22. Is the platform ready for external integrations?
```

---

# 98. Expected Final CLI

```text
usage: fikracore [-h]
                 {investigate,discover,learn,predict,simulate,inspect,present,benchmark,report,validate}
                 ...

FikraCore — Telecom reasoning, learning and resilience platform

commands:
  investigate   Explain what happened and why
  discover      Identify missing or insufficient operational knowledge
  learn         Validate, promote and manage learned knowledge
  predict       Run proactive what-if and resilience analysis
  simulate      Execute simulator scenarios
  inspect       Inspect knowledge, topology, scenarios and reasoning
  present       Produce investigation or curated-demo presentation state
  benchmark     Run H1–H4 and integration benchmarks
  report        Generate benchmark and analysis reports
  validate      Validate scenarios, learning units and artifacts
```

Legacy commands may remain available but should not dominate help output.

---

# 99. Final Experience Principle

The product should communicate:

```text
Investigate
→ understand what happened

Discover
→ understand what is missing

Learn
→ retain validated knowledge

Predict
→ understand what could fail

Knowledge
→ understand what FikraCore knows
```

---

# 100. Final Architecture

```text
                         FikraCore
                            │
                 Unified Capability Layer
                            │
       ┌──────────────┬─────┴─────┬──────────────┐
       │              │           │              │
      CLI       Simulator UI     Zaki           API
       │              │           │              │
       └──────────────┴─────┬─────┴──────────────┘
                            │
                    Shared Structured State
                            │
                  KnowledgeProvider Layer
                            │
                    Live telecombrain
                            │
                       gbrain MCP
```

---

# Final Principle

> **FikraCore should have one brain, one capability implementation, one state model, one scenario model, and multiple consistent ways to interact with it.**

And:

> **The Simulator UI must make the reasoning journey visible: hypothesis → evidence → falsification → unknown → validated learning → proactive resilience.**

Step 5 v3 turns the validated reasoning stack into the unified FikraCore operational product experience.
