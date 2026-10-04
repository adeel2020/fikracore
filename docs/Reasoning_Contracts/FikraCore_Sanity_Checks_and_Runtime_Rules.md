# FikraCore — Sanity Checks & Dynamic Runtime Rules Specification

## 1. Purpose

This document defines the cross-cutting sanity validation and dynamic runtime-rule architecture for FikraCore and Zaki.

The design principles are:

1. **Contracts define meaning and structure.**
2. **Sanity validators enforce invariant consistency.**
3. **Runtime rules determine which dynamic checks apply at runtime.**
4. **Runtime evaluation derives operational state; it does not use scenario-specific hardcoded conclusions.**
5. **TaskEpisodeContract is the operational experience spine that records the results of the runtime process.**
6. **FikraCore remains authoritative for topology, evidence, correlation, causality, and canonical knowledge.**
7. **Zaki orchestrates operational interaction, governance, HITL, and explanation.**
8. **Simulator ground truth is isolated from FikraCore and Zaki.**
9. **UNKNOWN is a valid operational outcome when available evidence is insufficient.**

---

# 2. Architectural Principle

The system must distinguish:

```text
Contract
   ↓
Contract Invariants
   ↓
Runtime Rule Selection
   ↓
Applicable Runtime Checks
   ↓
Evidence / Graph / Tool Evaluation
   ↓
PASS / WARN / BLOCK
   ↓
Operational State
   ↓
Task Episode
   ↓
Dynamic Response
```

### Contract

Answers:

> What does this object mean and what must always be structurally/semantically true?

### Sanity Check

Answers:

> Is this contract instance internally and cross-contract consistent?

### Runtime Rule

Answers:

> Given the current event, context, state, domain, task, hypothesis, or action, what checks should execute now?

### Task Episode

Answers:

> What happened during this operational task over time?

### Dynamic Response

Answers:

> Based on the current validated state, evidence, hypotheses, actions, and knowledge, what should the system communicate or do now?

---

# 3. Non-Negotiable Dynamic Runtime Principle

## 3.1 No hardcoded operational truth

The following must never be encoded as scenario-specific logic:

- root cause
- leading hypothesis
- incident classification
- blast radius
- affected service
- domain attribution
- evidence interpretation
- remediation decision
- response text
- confidence
- final finding
- operational outcome

Forbidden pattern:

```python
if scenario_id == "SCN-001":
    root_cause = "Transport failure"
```

Also forbidden:

```python
if upf_cpu > 90:
    root_cause = "UPF overload"
```

A threshold may be a **runtime rule**, but crossing the threshold must create an observation or condition, not automatically become an RCA.

Correct:

```text
UPF CPU 97%
    ↓
Raw Evidence
    ↓
Runtime Rule
    ↓
Emerging Condition
    ↓
Pattern / Correlation
    ↓
Hypothesis
    ↓
Discrimination Probe
    ↓
Validation
    ↓
Finding / RCA only if causally validated
```

---

# 4. No-Mock Runtime Principle

Simulation may generate synthetic network data.

It may generate:

- telemetry
- alarms
- metrics
- logs
- traces
- topology
- changes
- tickets
- incidents
- hidden ground truth

However:

```text
                    SIMULATOR
                        │
          ┌─────────────┴─────────────┐
          │                           │
   Visible simulation             Hidden truth
       inputs                     / oracle
          │                           │
          ▼                           ▼
      Kafka / data                Evaluation
      generation                  only
          │
          ▼
      FikraCore
          │
          ▼
         Zaki
```

FikraCore and Zaki MUST NOT access hidden ground truth.

They must derive conclusions from:

- available evidence
- topology
- operational state
- graph relationships
- runtime rules
- historical knowledge
- diagnostic tools
- probe results
- human validation

If evidence is insufficient:

```text
UNKNOWN
```

is the correct result.

---

# 5. Sanity Validation Model

Sanity checks are **cross-cutting invariant validators**, not one giant `SanityCheckContract`.

Recommended structure:

```text
contracts/
└── sanity/
    ├── __init__.py
    ├── structural.py
    ├── references.py
    ├── temporal.py
    ├── lifecycle.py
    ├── semantics.py
    ├── topology.py
    ├── causality.py
    ├── authority.py
    ├── knowledge.py
    ├── indexes.py
    └── simulation.py
```

All validators return:

```text
PASS
WARN
BLOCK
```

---

# 6. Sanity Check Categories

## S1 — Structural Integrity

Checks:

- required fields exist
- field types are valid
- enum values are valid
- schema version is supported
- IDs follow required format
- timestamps use valid format
- nested objects satisfy their contract
- arrays do not contain invalid duplicates where prohibited

Applies to:

- all contracts

BLOCK examples:

```text
missing required episode_id
invalid lifecycle enum
unsupported schema version
invalid timestamp
```

---

# 7. S2 — Identity & Reference Integrity

Checks:

- IDs are unique within their namespace
- referenced entities exist
- references resolve to the correct entity type
- no dangling references
- no accidental circular references
- canonical entity is referenced rather than duplicated

Applies to:

- TaskEpisode
- Evidence
- Hypothesis
- Pattern
- Incident
- Relationship
- Index structures
- Playbooks
- Agents
- Domains

Hard gate:

```text
Reference → canonical entity
```

must resolve.

---

# 8. S3 — Temporal Consistency

Checks:

- timestamps are valid
- event ordering is coherent
- evidence belongs to the applicable time window
- episode start precedes actions
- actions precede their results
- validation does not precede the evidence it validates
- resolved time cannot precede start time
- stale emerging evidence is handled correctly
- historical knowledge is not presented as current state without temporal qualification

Example:

```text
Telemetry
  10:01:00

Hypothesis
  10:02:00

Probe
  10:03:00

Validation
  10:04:00
```

Invalid:

```text
Validation
  10:00:00
```

when its supporting evidence arrived at 10:01:00.

---

# 9. S4 — Lifecycle Integrity

Every stateful contract must define legal transitions.

Example Evidence lifecycle:

```text
RAW
 ↓
EMERGING
 ↓
VALIDATED
 ↓
RETIRED / EXPIRED
```

Hypothesis:

```text
PROPOSED
 ↓
TESTING
 ↓
LEADING
 ├──→ RULED_OUT
 └──→ CONFIRMED
```

Incident:

```text
DETECTED
 ↓
OPEN
 ↓
INVESTIGATING
 ↓
MITIGATING
 ↓
RESOLVED
 ↓
CLOSED
```

Pattern:

```text
CANDIDATE
 ↓
VALIDATING
 ↓
VALIDATED
 ↓
PROMOTED
 ↓
RETIRED
```

Knowledge:

```text
CANDIDATE
 ↓
REVIEW
 ↓
VALIDATED
 ↓
PROMOTED
 ↓
ACTIVE
 ↓
DEPRECATED
```

BLOCK illegal transitions.

---

# 10. S5 — Semantic Separation

The following distinctions MUST be enforced:

```text
Telemetry
    ≠
Evidence
    ≠
Correlation
    ≠
Emerging Condition
    ≠
Pattern
    ≠
Incident
    ≠
Hypothesis
    ≠
Leading Hypothesis
    ≠
Validated Finding
    ≠
Root Cause
```

Examples:

```text
CPU = 97%
```

is telemetry/evidence.

It is not automatically:

```text
UPF overload
```

And:

```text
UPF overload
```

is not automatically:

```text
root cause
```

A runtime validator must prevent semantic escalation without sufficient evidence.

---

# 11. S6 — Topology & Graph Integrity

Checks:

- relationship predicate is valid for subject/object types
- endpoints exist
- relationship scope is valid
- topology relationships are physically/logically possible
- redundancy relationships are consistent
- service paths are traversable
- blast-radius edges are anchored to real entities
- domain ownership is consistent
- relationship provenance exists

Example:

```text
GNB
  │
  │ N3
  ▼
UPF
```

A rule must not infer an invalid topology relationship simply because two entities appear in the same incident.

---

# 12. S7 — Causal & Evidence Integrity

Checks:

- claims have supporting evidence
- contradictory evidence is retained
- missing evidence is explicit
- evidence provenance exists
- evidence quality is known
- causal claims require stronger validation than observational claims
- weak evidence cannot create strong causal edges
- hypothesis confirmation requires sufficient validation

Required distinction:

```text
OBSERVED
CORRELATED
SUPPORTED
CONFIRMED
```

Recommended causal progression:

```text
Observation
   ↓
Correlation
   ↓
Hypothesis
   ↓
Discrimination
   ↓
Validated Finding
   ↓
Causal Confirmation
```

A ranked #1 hypothesis is NOT automatically the root cause.

---

# 13. S8 — Scope & Authority Integrity

Checks:

- agent operates within domain scope
- tool belongs to permitted domain
- action is within agent authority ceiling
- HITL requirement is enforced
- approver has required authority
- playbook scope matches target
- cross-domain actions require appropriate authorization
- disruptive actions cannot bypass HITL

Example:

```text
Transport Agent
    ↓
Transport diagnostic tools
    ↓
Transport-scoped authority
```

A transport agent must not silently execute an unrelated core remediation action.

---

# 14. S9 — Knowledge & Pattern Integrity

Checks:

- pattern has provenance
- pattern has supporting occurrences
- similarity is measurable
- historical episodes are traceable
- pattern scope is explicit
- cross-domain patterns identify participating domains
- promotion requires validation
- deprecated knowledge is not silently treated as current
- knowledge changes are versioned

Pattern ≠ Incident.

One pattern may correspond to:

```text
Pattern P1
 ├── Episode 101
 ├── Episode 137
 ├── Episode 202
 └── Episode 241
```

---

# 15. S10 — Index Integrity

Indexes are retrieval structures, not duplicate semantic bodies.

Example:

```text
PATTERN_INDEX
    │
    └── pattern_id ───────► Canonical Pattern Entity
```

Index may contain:

- entity ID
- type
- scope
- lightweight signature
- retrieval metadata
- timestamps
- status

It must NOT contain a second full copy of the canonical PatternContract.

Same principle applies to:

- INCIDENTS Index
- EPISODES Index
- PATTERNS Index
- PLAYBOOKS Index
- TOPOLOGY Index

---

# 16. S11 — Simulation / Oracle Isolation

Checks:

- hidden ground truth is inaccessible to FikraCore
- hidden ground truth is inaccessible to Zaki
- simulator generation does not inject RCA labels into evidence
- scenario IDs do not encode conclusions
- evaluator is isolated from runtime reasoning
- response generation cannot query the oracle
- scoring occurs outside the operational reasoning path

Hard BLOCK:

```text
FikraCore → HiddenGroundTruth
```

---

# 17. RuntimeRuleContract

Runtime rules should be first-class contracts.

Suggested location:

```text
services/agents/src/engine_stack/engines/telecom_brain/
└── investigation/
    └── runtime_rules/
        ├── __init__.py
        ├── base.py
        ├── registry.py
        ├── evaluator.py
        ├── selectors.py
        ├── evidence_rules.py
        ├── hypothesis_rules.py
        ├── topology_rules.py
        ├── incident_rules.py
        ├── action_rules.py
        ├── knowledge_rules.py
        └── simulation_rules.py
```

---

# 18. Runtime Rule Schema

Recommended fields:

```yaml
rule_id:
rule_version:
rule_type:
name:
description:

applies_to:
  - contract/entity type

trigger:
  event:
  state_change:
  task_type:
  lifecycle_transition:

scope:
  domains:
  services:
  entity_types:
  topology_scope:

preconditions:
  - condition

checks:
  - check

inputs:
  - evidence
  - graph
  - operational_context
  - historical_knowledge
  - tool_result

decision:
  pass:
  warn:
  block:

actions:
  on_pass:
  on_warn:
  on_block:

priority:
enabled:

valid_from:
valid_until:

owner:
provenance:
```

---

# 19. Runtime Rule Selection

Do NOT execute every rule on every event.

The runtime should select applicable rules based on:

```text
event type
+
contract type
+
lifecycle state
+
domain
+
entity type
+
task type
+
operational context
+
authority
+
current investigation stage
```

Example:

```text
INFO telemetry
   ↓
Rule selector
   ↓
Applicable rules:
   ├── evidence integrity
   ├── emerging evidence
   └── temporal clustering

Not selected:
   ├── RCA confirmation
   ├── remediation authorization
   └── knowledge promotion
```

---

# 20. Example — Emerging Evidence Runtime Rule

```yaml
rule_id: RULE-EMERGING-001
rule_type: EMERGING_EVIDENCE
applies_to:
  - RawEvidence

trigger:
  event:
    severity:
      - INFO
      - WARNING

preconditions:
  - source_is_valid
  - timestamp_is_valid

checks:
  - repeated_signal_within_window
  - deviation_from_baseline
  - temporal_clustering
  - spatial_clustering
  - cross_domain_correlation

decision:
  pass: CREATE_EMERGING_EVIDENCE
  warn: RETAIN_AS_RAW_EVIDENCE
  block: REJECT_INVALID_INPUT
```

Important:

INFO/WARNING does not automatically mean:

```text
incident
```

It may remain:

```text
Raw Evidence
```

or become:

```text
Emerging Evidence
```

depending on runtime evaluation.

---

# 21. Example — Hypothesis Runtime Rule

```yaml
rule_id: RULE-HYPOTHESIS-001
rule_type: HYPOTHESIS_EVALUATION

applies_to:
  - InvestigationHypothesis

trigger:
  lifecycle:
    - PROPOSED
    - TESTING
    - LEADING

checks:
  - supporting_evidence_count
  - contradictory_evidence_count
  - missing_evidence
  - topology_consistency
  - temporal_consistency
  - discrimination_probe_available

decision:
  pass: ALLOW_STATE_PROGRESS
  warn: KEEP_AS_LEADING
  block: PREVENT_CONFIRMATION
```

The rule does not decide:

```text
"Transport is the root cause."
```

It decides whether the hypothesis has sufficient basis to progress.

---

# 22. Example — RCA Confirmation Rule

```yaml
rule_id: RULE-RCA-001
rule_type: CAUSAL_VALIDATION

applies_to:
  - InvestigationHypothesis

preconditions:
  - hypothesis_status == LEADING

checks:
  - validated_supporting_evidence
  - contradictory_evidence_resolved
  - discrimination_probe_result
  - topology_consistency
  - temporal_causality
  - impact_consistency

decision:
  pass: ALLOW_CONFIRMED_FINDING
  warn: KEEP_AS_LEADING
  block: PREVENT_RCA_CONFIRMATION
```

The runtime generates the decision from evidence.

It does not contain the RCA itself.

---

# 23. Runtime Rule Evaluation Result

Every runtime evaluation should produce a traceable result.

Suggested structure:

```yaml
evaluation_id:
rule_id:
rule_version:
evaluated_at:

subject:
  entity_id:
  entity_type:

episode_id:

inputs:
  evidence_refs:
  graph_refs:
  context_refs:
  tool_result_refs:

checks:
  - check_id:
    result:
    value:
    threshold:
    evidence_refs:

decision:
  status: PASS | WARN | BLOCK

reason:
  structured_reason_codes:

actions_triggered:
  - action

evaluator_version:
```

This gives you explainability without hardcoding the explanation.

---

# 24. PASS / WARN / BLOCK Semantics

## PASS

The required condition is satisfied.

```text
PASS
→ continue lifecycle / action
```

## WARN

The system can continue, but uncertainty or incompleteness exists.

```text
WARN
→ continue with explicit uncertainty
```

## BLOCK

A hard invariant, safety constraint, or authority requirement is violated.

```text
BLOCK
→ prevent transition/action
```

Example:

```text
Hypothesis confirmation
    ↓
Insufficient causal evidence
    ↓
WARN or BLOCK depending on rule
    ↓
Cannot claim RCA
```

---

# 25. Runtime Rules vs Sanity Checks

| Concern | Sanity Validator | Runtime Rule |
|---|---|---|
| Required field | Yes | No |
| Valid enum | Yes | No |
| Reference exists | Yes | Sometimes |
| Timestamp validity | Yes | Sometimes |
| Emerging evidence detection | No | Yes |
| Pattern detection | No | Yes |
| Hypothesis progression | No | Yes |
| RCA confirmation gate | No | Yes |
| HITL authorization | No | Yes |
| Playbook precondition | No | Yes |
| Hidden oracle isolation | Yes | Yes where runtime boundary is involved |
| Knowledge promotion | Invariant checks | Dynamic promotion rules |

---

# 26. Runtime Rules Must Be Data-Driven

Avoid:

```python
if rule_id == "RULE-001":
    ...
elif rule_id == "RULE-002":
    ...
```

Prefer:

```text
Rule Registry
      ↓
Rule Definition
      ↓
Rule Selector
      ↓
Generic Rule Evaluator
      ↓
Contract / Tool / Graph adapters
      ↓
Evaluation Result
```

The evaluator should be generic.

Rules should be versioned data/configuration or declarative definitions wherever practical.

Complex rules may use controlled executable evaluators, but those evaluators must still be:

- versioned
- scoped
- testable
- observable
- auditable
- permission-controlled

---

# 27. Dynamic Response Architecture

Zaki responses must be generated from runtime state.

```text
TaskEpisode
     +
OperationalContext
     +
Validated Evidence
     +
Active Hypotheses
     +
Runtime Evaluation Results
     +
Graph Context
     +
Historical Knowledge
     +
Tool Results
     ↓
Response Context
     ↓
Zaki reasoning / response generation
     ↓
Dynamic response
```

No:

```python
scenario_id → response_text
```

No:

```python
incident_type → fixed RCA sentence
```

No mock response tables.

---

# 28. Dynamic Action Architecture

Actions must also be dynamically derived.

```text
Current State
     ↓
Applicable Rules
     ↓
Candidate Actions
     ↓
Safety / Authority Evaluation
     ↓
HITL Gate if required
     ↓
Tool Execution
     ↓
Execution Result
     ↓
New Evidence
     ↓
Re-evaluation
```

This creates a feedback loop:

```text
Observe
  ↓
Reason
  ↓
Probe
  ↓
Observe Result
  ↓
Re-evaluate
  ↓
Act
  ↓
Observe Result
  ↓
Learn
```

---

# 29. Runtime Rules and TaskEpisode

TaskEpisode does not own all rules.

It records their application.

Example:

```text
TaskEpisode TE-001
│
├── evidence_refs
├── hypothesis_refs
├── probe_refs
├── action_refs
├── finding_refs
│
└── runtime_evaluations
      ├── RULE-EVIDENCE-001 → PASS
      ├── RULE-EMERGING-001 → PASS
      ├── RULE-TOPOLOGY-003 → PASS
      ├── RULE-HYPOTHESIS-001 → WARN
      └── RULE-RCA-001 → BLOCK
```

The episode therefore becomes the durable operational experience record.

---

# 30. Runtime Rule Lifecycle

Runtime rules themselves need lifecycle management.

```text
DRAFT
 ↓
TESTING
 ↓
VALIDATED
 ↓
ACTIVE
 ↓
DEPRECATED
 ↓
RETIRED
```

A rule should not become ACTIVE without:

- schema validation
- unit tests
- representative scenario tests
- false-positive testing
- false-negative testing
- scope validation
- authority review where applicable
- version assignment

---

# 31. Rule Provenance

Every rule must identify:

```text
rule_id
rule_version
owner
created_at
updated_at
source
validation_status
effective_from
effective_until
```

For operational rules, provenance should answer:

> Why does this rule exist?

Possible sources:

```text
domain engineering knowledge
validated historical episode
vendor documentation
network engineering standard
approved MOP
regulatory requirement
human-authored operational policy
validated learned pattern
```

---

# 32. Runtime Rule Conflict Resolution

Multiple rules may apply simultaneously.

Example:

```text
Rule A → WARN
Rule B → PASS
Rule C → BLOCK
```

The runtime needs deterministic precedence.

Recommended:

```text
BLOCK
  >
WARN
  >
PASS
```

But rule priority and safety class must also be considered.

A lower-priority informational rule must never override a safety BLOCK.

Conflicts should be recorded:

```text
rule_conflict:
  rules:
  resolution:
  precedence_reason:
```

---

# 33. Runtime Rule Scope

Rules must support scope.

Example:

```yaml
scope:
  domains:
    - IP_TRANSPORT

  services:
    - N3

  entity_types:
    - ROUTER
    - VRF
```

Another rule may be:

```yaml
scope:
  domains:
    - PS_CORE
    - IP_TRANSPORT
```

This enables cross-domain rules without creating duplicated domain-specific rule engines.

---

# 34. Rule Evaluation Triggers

Possible triggers:

```text
EVENT_RECEIVED
STATE_CHANGED
EVIDENCE_CREATED
EVIDENCE_PROMOTED
PATTERN_DETECTED
INCIDENT_OPENED
HYPOTHESIS_CREATED
HYPOTHESIS_CHANGED
PROBE_COMPLETED
ACTION_REQUESTED
ACTION_COMPLETED
HITL_REQUESTED
HITL_APPROVED
HITL_REJECTED
EPISODE_CLOSURE
KNOWLEDGE_PROMOTION
```

The runtime selects only rules applicable to the trigger.

---

# 35. Runtime Rule Categories

Recommended initial categories:

```text
EVIDENCE
EMERGING_CONDITION
CORRELATION
PATTERN
INCIDENT
HYPOTHESIS
DISCRIMINATION
TOPOLOGY
BLAST_RADIUS
ACTION
SAFETY
AUTHORITY
HITL
PLAYBOOK
KNOWLEDGE
PROMOTION
SIMULATION
RESPONSE
```

Do not implement all categories immediately.

Start with the minimum needed for the MVP.

---

# 36. Dynamic Pattern Recognition

Pattern recognition should also be runtime-driven.

```text
Evidence
   ↓
PatternRecognitionContract
   ↓
Runtime Pattern Rules
   ↓
Feature extraction
   ↓
Signature matching
   ↓
Historical comparison
   ↓
Novelty / similarity
   ↓
Candidate Pattern
```

Pattern recognition must return a candidate rather than silently turning similarity into truth.

Example:

```text
Pattern match = 91%
```

does not mean:

```text
RCA = historical RCA
```

It means:

```text
Historical pattern may be relevant.
```

The current evidence still needs evaluation.

---

# 37. Runtime Relationship Creation

Relationships should also be governed dynamically.

For example:

```text
Evidence
   ↓
supports
   ↓
Hypothesis
```

may be created after evaluation.

But:

```text
Entity A
   ↓
CAUSED
   ↓
Entity B
```

requires stronger causal validation.

Therefore:

```text
Relationship Rule
   ↓
Check relationship type
   ↓
Check subject/object types
   ↓
Check evidence requirements
   ↓
Check provenance
   ↓
Create / reject / defer relationship
```

---

# 38. Runtime Rule Observability

Every rule evaluation should be observable.

Metrics:

```text
rule_evaluations_total
rule_pass_total
rule_warn_total
rule_block_total
rule_execution_latency
rule_error_total
rule_conflict_total
rule_false_positive_rate
rule_false_negative_rate
```

For investigation:

```text
Which rules fired?
Why?
What inputs did they use?
What did they conclude?
What changed afterwards?
```

---

# 39. Testing Strategy

Required tests should include:

```text
test_contract_invariants.py
test_reference_integrity.py
test_temporal_consistency.py
test_lifecycle_transitions.py
test_semantic_separation.py
test_graph_relationship_integrity.py
test_pattern_integrity.py
test_index_pointer_integrity.py
test_causal_evidence_integrity.py
test_authority_scope.py
test_knowledge_promotion_integrity.py
test_hidden_oracle_isolation.py
```

Runtime tests:

```text
test_runtime_rule_selection.py
test_runtime_rule_evaluation.py
test_runtime_rule_precedence.py
test_runtime_rule_scope.py
test_runtime_rule_lifecycle.py
test_emerging_evidence_rules.py
test_hypothesis_rules.py
test_rca_confirmation_rules.py
test_dynamic_action_rules.py
test_dynamic_response_generation.py
```

---

# 40. End-to-End Example

Input:

```text
INFO:
N3 packet-loss counter increases.

WARNING:
UPF latency increases.

INFO:
PE router interface errors increase.
```

The system must NOT immediately say:

```text
Root cause = PE router
```

Instead:

```text
Telemetry
   ↓
Raw Evidence
   ↓
Runtime Evidence Rules
   ↓
Emerging Evidence
   ↓
Temporal / topology correlation
   ↓
Pattern candidate
   ↓
Incident candidate if significance threshold is met
   ↓
TaskEpisode created/updated
   ↓
Hypotheses generated
```

Possible hypotheses:

```text
H1: Transport path degradation
H2: UPF local overload
H3: Shared timing issue
H4: Unknown
```

Runtime rules then determine which probes are useful.

For example:

```text
H1
 ↓
N3 path probe
 ↓
packet loss confirmed upstream
 ↓
H1 strengthened

H2
 ↓
UPF local resource probe
 ↓
no local saturation
 ↓
H2 weakened
```

Only after sufficient causal validation:

```text
Transport failure
   ↓
validated
   ↓
confirmed finding / RCA
```

Otherwise:

```text
Leading hypothesis: Transport path degradation
Root cause: UNKNOWN
```

That is a valid result.

---

# 41. Recommended Runtime Architecture

```text
                        ┌──────────────────────┐
                        │   Contract Registry  │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   Rule Registry      │
                        └──────────┬───────────┘
                                   │
Event ─────────────────────────────▼
                        ┌──────────────────────┐
                        │   Rule Selector      │
                        └──────────┬───────────┘
                                   │
                        applicable rules
                                   │
                        ┌──────────▼───────────┐
                        │   Rule Evaluator     │
                        └──────────┬───────────┘
                                   │
             ┌─────────────────────┼───────────────────┐
             ▼                     ▼                   ▼
        Contract              Graph/Topology       Tool Results
        Validators             Evaluation           / Probes
             │                     │                   │
             └─────────────────────┼───────────────────┘
                                   ▼
                        ┌──────────────────────┐
                        │ PASS / WARN / BLOCK  │
                        └──────────┬───────────┘
                                   │
                         ┌─────────▼─────────┐
                         │ Operational State │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │   Task Episode    │
                         └─────────┬─────────┘
                                   │
                         ┌─────────▼─────────┐
                         │       Zaki        │
                         │ Dynamic Response  │
                         └───────────────────┘
```

---

# 42. Final Architectural Rules

These should be treated as architecture-level invariants:

### R1 — No Hardcoded Operational Truth
Operational conclusions must never be encoded as scenario-specific logic.

### R2 — No Mocked Runtime Reasoning
Demo/simulator behavior must use the same reasoning path as the target architecture.

### R3 — Rules Are Data/Logic, Not Answers
A runtime rule determines how to evaluate a condition; it does not encode the resulting RCA.

### R4 — Contracts Define Semantics
Contracts define valid structures, states, references, and semantic boundaries.

### R5 — Runtime Determines Applicability
Only rules relevant to the current event/state/context should execute.

### R6 — Evidence Precedes Causality
No causal relationship or RCA without sufficient validation.

### R7 — Rank Is Not Truth
The leading hypothesis remains a hypothesis until validated.

### R8 — UNKNOWN Is Valid
Insufficient evidence must produce uncertainty, not fabricated certainty.

### R9 — TaskEpisode Records Experience
TaskEpisode binds the operational experience without owning the semantics of every other contract.

### R10 — One Canonical Graph
Indexes and capability structures reference canonical graph entities rather than duplicating them.

### R11 — Hidden Oracle Isolation
Simulator ground truth is unavailable to FikraCore/Zaki.

### R12 — Every Decision Is Traceable
Runtime decisions must identify their rule, version, inputs, evidence, and result.

### R13 — Safety Overrides Convenience
Authority, safety, and HITL BLOCK conditions cannot be bypassed by lower-priority rules.

### R14 — Dynamic Responses
Zaki responses must be generated from current operational context and validated runtime state.

### R15 — Learning Must Be Governed
Runtime observations can become learning candidates, but canonical knowledge requires validation and promotion.

---

# 43. Target Mental Model

The final system should behave like:

```text
        NETWORK
           │
           ▼
       OBSERVATION
           │
           ▼
        EVIDENCE
           │
           ▼
      RUNTIME RULES
           │
           ▼
       CORRELATION
           │
           ▼
         PATTERN
           │
           ▼
       HYPOTHESES
           │
           ▼
   DISCRIMINATION PROBES
           │
           ▼
       VALIDATION
           │
           ▼
        FINDING
           │
           ▼
      OPERATIONAL ACTION
           │
           ▼
        NEW EVIDENCE
           │
           └──────────────┐
                          ▼
                    RE-EVALUATION
                          │
                          ▼
                    TASK EPISODE
                          │
                          ▼
                         ZAKI
                          │
                          ▼
                  DYNAMIC RESPONSE
                          │
                          ▼
                      LEARNING
                          │
                          ▼
                 KNOWLEDGE PROMOTION
```

**The key architectural shift is:**

> **FikraCore should not contain a library of predetermined answers. It should contain contracts, canonical knowledge, runtime rules, tools, graph relationships, and reasoning mechanisms that dynamically derive the answer from the operational state.**
