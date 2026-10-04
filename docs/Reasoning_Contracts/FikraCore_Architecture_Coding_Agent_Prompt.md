# FikraCore — Canonical Knowledge Graph & Contract Architecture
## Coding Agent Implementation Prompt

### Mission

Implement FikraCore as a **single canonical operational knowledge graph** for telecom NOC intelligence.

The graph must support:

- Network topology and dependencies
- Operational incidents and evidence
- Pattern recognition
- Historical reasoning pathways
- Hypotheses and findings
- Knowledge lifecycle and controlled knowledge promotion
- What-if / simulation scenarios
- Change-impact and vulnerability analysis
- Provenance, validation, scope, confidence, and lifecycle state
- MCP/external connectivity without bypassing governance

> **Core principle: One canonical graph, many capability clusters.**

Do not create a separate knowledge graph or datastore for every capability.

---

# 1. System Architecture

```text
                         FIKRACORE
                    CANONICAL GRAPH
                           |
        +------------------+------------------+
        |                  |                  |
     TOPOLOGY          OPERATIONS          KNOWLEDGE
        |                  |                  |
   Network entities    Incidents          Patterns
   Dependencies       Evidence            Pathways
   Services           Hypotheses          Knowledge claims
        |                  |                  |
        +------------------+------------------+
                           |
                    CAPABILITY CLUSTERS
                           |
       +-------------------+-------------------+
       |                   |                   |
 Pattern Recognition   Reasoning/RCA     Simulation/What-if
 Incident Intelligence Change Impact     Knowledge Lifecycle
 Governance            MCP/Integration
```

All clusters operate on the same graph.

---

# 2. Entity Model

## 2.1 Network entities

Examples:

- Network
- Domain
- Service
- ServiceCluster
- Node
- Pod
- UPF
- AMF
- SMF
- gNodeB
- TransportRouter
- VRF
- Storage
- KubernetesCluster
- Interface
- Protocol
- Application

These describe the actual network/system architecture.

## 2.2 Incident

An incident is one concrete operational occurrence.

Example:

```yaml
id: INC-00123
type: INCIDENT
status: INVESTIGATING
detected_at: ...
resolved_at: ...
severity: MAJOR
summary: UPF-003 throughput degradation
affected_entities:
  - UPF-003
evidence_refs:
  - EVD-1001
  - EVD-1002
```

Incidents are operational records, not knowledge.

## 2.3 Evidence

Evidence represents an observed artifact:

- Alarm
- Metric
- KPI
- Log
- Trace
- PCAP
- Ticket
- Change record
- Engineer observation

Every evidence object must have provenance and timestamp.

## 2.4 Hypothesis

A hypothesis is a proposed explanation.

```text
HYP-001
Shared Storage-A failure caused UPF-003 degradation
```

A hypothesis must never automatically become truth.

## 2.5 Finding

A finding is an investigation result. It is stronger than a hypothesis but is not automatically reusable knowledge.

---

# 3. Pattern Model

A Pattern represents a reusable recurring operational structure.

Example:

```yaml
id: PAT-001
type: PATTERN

name: shared-storage-upf-degradation

description: >
  Recurring operational structure where storage degradation
  is associated with UPF throughput degradation.

signature:
  symptoms:
    - throughput_degradation
  dependencies:
    - shared_storage
  affected_service:
    - UPF

matching_criteria:
  required_entities:
    - UPF
    - shared_storage
  required_signals:
    - storage_degradation
    - throughput_degradation

scope:
  domains:
    - 5GC

status: CANDIDATE
```

Do NOT store all incidents inside the pattern node.

Instead:

```text
PAT-001
  |
  +-- MATCHES -- INC-001
  +-- MATCHES -- INC-017
  +-- MATCHES -- INC-042
  +-- MATCHES -- INC-105
```

Recurrence should be **derived from these relationships**.

Do not use a manually maintained recurrence counter as the source of truth. A cached count is acceptable only as a derived/indexed value.

---

# 4. Incident and Pattern Index Nodes

Optional collection/index nodes:

```text
INCIDENTS
   |
   +-- INC-001
   +-- INC-002
   +-- INC-003

PATTERNS
   |
   +-- PAT-001
   +-- PAT-002
   +-- PAT-003
```

These are navigation/index structures only.

They must not contain the intelligence of every incident or pattern.

---

# 5. Pattern Recognition

Pattern recognition is a runtime capability.

```text
New Incident
     |
     v
Normalize incident
     |
     v
Extract operational signature
     |
     v
Search existing patterns
     |
     +---- MATCH ----> create MATCHES relationship
     |
     +---- NO MATCH -> keep incident unmatched
                         |
                         v
                  candidate pattern discovery
```

Matching should consider:

- Affected entities
- Symptoms
- Alarms
- KPIs
- Metrics
- Logs
- Topology context
- Dependency structure
- Failure mode
- Temporal behavior
- Domain
- Service
- Protocol/error characteristics

Topology similarity alone must not automatically imply operational-pattern similarity.

---

# 6. Relationships

Relationships are first-class architecture elements.

## Topology

```text
CONNECTED_TO
DEPENDS_ON
CONTAINS
HOSTS
SERVES
ROUTES_TO
PART_OF
USES
```

## Operational

```text
AFFECTS
OBSERVED_ON
CAUSED_BY
CORRELATED_WITH
ASSOCIATED_WITH
```

## Evidence

```text
SUPPORTS
CONTRADICTS
DERIVED_FROM
HAS_EVIDENCE
```

## Pattern

```text
MATCHES
INSTANCE_OF
DERIVED_FROM_PATTERN
CORROBORATES
```

## Knowledge

```text
VALIDATES
PROMOTES
SUPERSEDES
DEPRECATES
CONFLICTS_WITH
```

## Scenario

```text
ASSUMES
EVALUATES
PROJECTS
SIMULATES
IMPACTS
```

Relationship semantics must be explicitly defined.

Example:

```text
Evidence --SUPPORTS--> Hypothesis
Incident --MATCHES--> Pattern
Scenario --EVALUATES--> UPF-003
```

---

# 7. Canonical

`CANONICAL` is a lifecycle/status concept, not an entity type.

Do not create:

```text
CanonicalUPF
CanonicalPattern
CanonicalIncident
```

Instead:

```yaml
status: CANONICAL
```

Canonical means:

> FikraCore has accepted this representation as the authoritative reusable representation within a defined scope.

Canonical does not mean:

- universally true
- permanent
- immutable
- valid for every situation

Canonical objects can later become:

```text
REVALIDATION_REQUIRED
DEPRECATED
SUPERSEDED
```

---

# 8. Incident Lifecycle

Use a lifecycle specific to operational cases:

```text
DETECTED
   |
OPEN
   |
TRIAGED
   |
INVESTIGATING
   |
+--+----------------+
|                   |
RESOLVED            ESCALATED
|                   |
+--------+----------+
         |
       CLOSED
```

Optional:

```text
REOPENED
```

Important:

> Closing an incident does not mean that knowledge has been promoted.

The incident remains a historical operational record.

---

# 9. Pattern Lifecycle

```text
DISCOVERED
    |
CANDIDATE
    |
VALIDATING
    |
VALIDATED
    |
CANONICAL
    |
+---+------------------+
|                      |
DEPRECATED          SUPERSEDED
```

A pattern can remain a candidate.

Not every pattern must become canonical.

---

# 10. Knowledge Lifecycle

Keep this separate from incident lifecycle.

```text
OBSERVED
   |
DISCOVERED
   |
CANDIDATE
   |
VALIDATING
   |
VALIDATED
   |
CANONICAL
   |
REVALIDATION_REQUIRED
   |
DEPRECATED / SUPERSEDED
```

Knowledge promotion must be controlled by contracts.

---

# 11. Topology Learning Lifecycle

Topology learning is different from pattern recognition.

Example:

```text
UPF-003 --DEPENDS_ON--> Storage-A
```

If the relationship did not previously exist:

```text
DISCOVERED
    |
CANDIDATE
    |
VALIDATED
    |
CANONICAL
```

Topology learning describes what exists.

Pattern learning describes recurring operational behavior.

---

# 12. Scenario / What-if Lifecycle

Scenarios represent simulations, not operational truth.

```text
DRAFT
  |
READY
  |
RUNNING
  |
COMPLETED
  |
ARCHIVED
```

Scenario outputs must explicitly be marked:

```text
SIMULATED
PROJECTED
```

Never silently write simulation results into canonical operational truth.

Example:

```text
SCN-WIF-001
  |
  +-- ASSUMES --> Storage-A FAILED
  |
  +-- EVALUATES --> UPF-003
  |
  +-- PROJECTS --> throughput degradation
```

---

# 13. Contract Architecture

Contracts are executable governance rules.

A contract defines:

- Purpose
- Inputs
- Outputs
- Preconditions
- Postconditions
- Allowed state transitions
- Required evidence
- Required provenance
- Validation rules
- Relationship constraints
- Scope
- Failure behavior
- Audit requirements
- Version
- Owner

Example:

```yaml
contract_id: pattern.match.v1

purpose:
  Match an incident against an operational pattern.

inputs:
  - incident_id
  - pattern_id
  - operational_signature

preconditions:
  - incident.status in [TRIAGED, INVESTIGATING, RESOLVED]
  - pattern.status in [CANDIDATE, VALIDATED, CANONICAL]

rules:
  - signature similarity must meet configured threshold
  - topology context must be compatible
  - temporal context must be compatible

outputs:
  - MATCHES relationship
  - match_score
  - matched_features
  - provenance

side_effects:
  - append audit event
```

---

# 14. Task Episode Contract — The Spine

The Task Episode Contract is the orchestration spine connecting all contracts.

It does not contain every domain rule.

It establishes the execution context:

```text
                    TASK EPISODE
                         |
        +----------------+----------------+
        |                |                |
      Intent           Context          Scope
        |                |                |
        +----------------+----------------+
                         |
                  Contract Registry
                         |
        +----------------+----------------+
        |                |                |
 Incident Contract  Pattern Contract  Knowledge Contract
        |                |                |
 Evidence Contract  Reasoning Contract Scenario Contract
        |                |                |
        +----------------+----------------+
                         |
                  CANONICAL GRAPH
```

Task Episode fields:

```yaml
episode_id
task_type
intent
actor
session
tenant
scope
time_window
entities_in_scope
input_refs
evidence_refs
contract_refs
actions
state
outputs
audit_refs
parent_episode_id
```

The Task Episode Contract enforces:

- identity
- scope
- permissions
- temporal context
- correlation/context ID
- contract versions
- allowed operations
- auditability
- state transitions
- output references
- handoff/continuation

It answers:

> What task are we performing, on what scope, with what evidence, under which contract versions, and what did we produce?

---

# 15. Contract Families

Implement independently versioned contracts:

### A. Task Episode Contract
Execution context and orchestration.

### B. Incident Contract
Incident creation, update, escalation, resolution, closure.

### C. Evidence Contract
Evidence ingestion, provenance, timestamps, source identity and integrity.

### D. Pattern Recognition Contract
Rules for matching incidents to patterns.

### E. Pattern Discovery Contract
Rules for creating candidate patterns from recurring incidents.

### F. Hypothesis Contract
Creation and evidence linkage.

### G. Validation Contract
Validation of findings/claims.

### H. Knowledge Promotion Contract
Controls transition from validated finding/pattern to canonical reusable knowledge.

### I. Topology Learning Contract
Controls adding/changing topology relationships.

### J. Scenario Contract
Controls what-if simulations and prevents simulation results from silently changing real topology.

### K. Reasoning Pathway Contract
Controls creation, reuse and versioning of investigation pathways.

### L. Change Impact Contract
Evaluates proposed changes against topology, dependencies, incidents, patterns and knowledge.

### M. Deprecation/Supersession Contract
Controls retirement/replacement of canonical knowledge.

---

# 16. Capability Clusters

## Cluster 1 — Network Understanding

- Topology ingestion
- Topology validation
- Dependency discovery
- Service mapping
- Current network state

## Cluster 2 — Incident Intelligence

- Incident ingestion
- Incident normalization
- Incident correlation
- Incident timeline
- Evidence management
- Incident closure

## Cluster 3 — Pattern Recognition

- Signature extraction
- Similarity matching
- Existing pattern matching
- Candidate pattern discovery
- Recurrence derivation
- Pattern evolution

## Cluster 4 — Reasoning / Investigation

- Hypothesis generation
- Historical pathway retrieval
- Evidence validation
- RCA reasoning
- Cross-domain correlation
- Leading hypothesis vs confirmed root cause

## Cluster 5 — Knowledge Lifecycle

- Finding creation
- Validation
- Knowledge candidate creation
- Promotion
- Canonicalization
- Versioning
- Conflict detection
- Deprecation

## Cluster 6 — Simulation / What-if

- Scenario creation
- Assumption management
- Failure simulation
- Impact projection
- Vulnerability analysis
- Change impact analysis

## Cluster 7 — Governance

- Contract registry
- Contract evaluation
- Authorization
- Provenance
- Audit trail
- Lifecycle enforcement
- Conflict management

## Cluster 8 — Integration / MCP

- Kafka
- OSS/BSS
- Grafana/LGTM
- Ticketing
- Notification systems
- MCP servers/tools
- External APIs

All clusters operate against the same graph.

---

# 17. Boundary Rules

### Incident != Pattern

Incident = one concrete occurrence.

Pattern = reusable recurring operational structure.

### Pattern != Knowledge

Pattern = recurring structure.

Knowledge = validated reusable claim/relationship.

### Evidence != Hypothesis

Evidence = observation.

Hypothesis = proposed explanation.

### Hypothesis != Root Cause

A hypothesis is not confirmed until validation criteria are satisfied.

### Simulation != Reality

Scenario results are projections and must not silently modify canonical operational truth.

### Topology != Operational Pattern

Topology describes what exists/how systems connect.

Patterns describe how operational behavior recurs.

### Contract != Schema

Schema defines structure.

Contract defines behavior, constraints, validation and allowed transitions.

### Capability != Data Store

Pattern recognition is a capability, not a separate database.

---

# 18. Historical Reasoning Pathway

A reasoning pathway captures a reusable investigation structure.

Do not store hidden LLM chain-of-thought.

Example:

```yaml
pathway_id: RP-005
name: storage-to-upf-degradation-investigation

trigger_signature:
  - UPF throughput degradation
  - storage anomalies

steps:
  - inspect_storage_health
  - correlate_upf_metrics
  - inspect_kubernetes_events
  - validate_dependency
  - assess_blast_radius

required_evidence:
  - storage_metrics
  - UPF_KPI
  - topology_dependency

scope:
  domain: 5GC
```

A new incident can retrieve the pathway as an investigation scaffold and validate each step against current evidence.

---

# 19. Example Pattern

Historical incidents:

```text
INC-001
Storage-A degradation
UPF-003 throughput degradation

INC-017
Storage-B degradation
UPF-007 throughput degradation

INC-042
Storage-A latency increase
UPF-003 throughput degradation
```

Pattern:

```text
PAT-001
Shared-storage degradation associated with UPF degradation
```

Graph:

```text
INC-001 ----MATCHES----\
                        \
INC-017 ----MATCHES----- PAT-001
                        /
INC-042 ----MATCHES----/
```

The pattern summarizes recurring structure.

It does not replace the incidents.

---

# 20. Canonical Identity Rule

There must be one authoritative identity for a network entity.

Do not create:

```text
PatternUPF-003
ScenarioUPF-003
IncidentUPF-003
RCAUPF-003
```

Use the same:

```text
UPF-003
```

and connect contextual entities:

```text
UPF-003
  |
  +-- AFFECTED_BY --> INC-001
  +-- AFFECTED_BY --> INC-042
  +-- REFERENCED_BY --> PAT-001
  +-- EVALUATED_BY --> SCN-001
  +-- DEPENDS_ON --> Storage-A
```

---

# 21. Provenance

Every learned or promoted relationship must be traceable.

Minimum provenance:

```yaml
source_type
source_id
observed_at
created_at
created_by
evidence_refs
contract_id
contract_version
episode_id
validation_refs
scope
```

This allows Zaki to answer:

> Why does FikraCore believe this?

without exposing hidden model reasoning.

---

# 22. Versioning

Version all mutable artifacts:

- Schemas
- Contracts
- Patterns
- Reasoning pathways
- Knowledge claims
- Lifecycle transitions

Canonical does not mean immutable.

Use explicit versions such as:

```text
PAT-001 v1
PAT-001 v2
```

---

# 23. Conflict Handling

Never overwrite conflicting knowledge silently.

Example:

```text
PAT-001
Storage degradation -> UPF degradation

PAT-021
Storage degradation does not explain degradation
under condition X
```

Represent conflict explicitly:

```text
CONFLICTS_WITH
```

and invoke the appropriate validation/revalidation contract.

---

# 24. Suggested Implementation Order

The coding agent should implement in this order:

## Phase 1 — Architecture foundation

1. Repository/module boundaries
2. Canonical entity model
3. Relationship vocabulary
4. Lifecycle enums/state machines
5. Provenance model
6. Version model

## Phase 2 — Graph schema

Implement schemas for:

- Network entities
- Incident
- Evidence
- Hypothesis
- Finding
- Pattern
- ReasoningPathway
- KnowledgeClaim
- Scenario
- TaskEpisode
- AuditEvent

## Phase 3 — Contract framework

Implement:

- Contract interface/base class
- Contract registry
- Contract versioning
- Preconditions
- Postconditions
- State transition validation
- Audit hooks
- Contract execution result

Then implement the contract families listed above.

## Phase 4 — Incident flow

Implement:

```text
Detect
 -> Create incident
 -> Attach evidence
 -> Update lifecycle
 -> Close incident
```

## Phase 5 — Pattern recognition

Implement:

```text
Incident
 -> Signature
 -> Pattern search
 -> Match
 -> MATCHES relationship
```

and unmatched incident handling.

## Phase 6 — Pattern discovery

Implement:

```text
Unmatched/repeated incidents
 -> similarity analysis
 -> candidate pattern
 -> PATTERN node
 -> links to incidents
```

## Phase 7 — Reasoning pathways

Implement pathway creation, versioning and retrieval.

## Phase 8 — Knowledge lifecycle

Implement:

```text
Observed
 -> Candidate
 -> Validating
 -> Validated
 -> Canonical
```

through contracts.

## Phase 9 — What-if / simulation

Implement scenarios without modifying canonical operational truth.

## Phase 10 — MCP/integration

Expose controlled interfaces through MCP.

MCP tools must invoke contracts rather than bypassing them.

---

# 25. Required Interfaces

Create interfaces/contracts similar to:

```text
GraphRepository
EntityRepository
RelationshipRepository

IncidentService
EvidenceService
PatternService
PatternRecognitionService
PatternDiscoveryService
ReasoningPathwayService
KnowledgeService
ScenarioService

ContractEngine
ContractRegistry
LifecycleEngine
ProvenanceService
AuditService

TaskEpisodeService
```

Keep domain services separate from storage implementation.

---

# 26. Required Contract Interface

Illustrative:

```typescript
interface Contract<TInput, TOutput> {
  id: string;
  version: string;

  validate(input: TInput, context: ContractContext): ValidationResult;

  execute(
    input: TInput,
    context: ContractContext
  ): ContractResult<TOutput>;

  allowedTransitions(): TransitionRule[];
}
```

Do not make contracts depend directly on UI or LLM implementation.

---

# 27. Required Pattern Interface

Illustrative:

```typescript
interface PatternRecognitionService {
  extractSignature(
    incidentId: string,
    episode: TaskEpisode
  ): Promise<OperationalSignature>;

  findMatches(
    signature: OperationalSignature
  ): Promise<PatternMatch[]>;

  recordMatch(
    incidentId: string,
    patternId: string,
    match: PatternMatch
  ): Promise<void>;

  discoverCandidates(
    scope: PatternDiscoveryScope
  ): Promise<PatternCandidate[]>;
}
```

---

# 28. Required Knowledge Interface

Illustrative:

```typescript
interface KnowledgeLifecycleService {
  createCandidate(input: KnowledgeCandidate): Promise<KnowledgeClaim>;

  validate(
    knowledgeId: string,
    validation: ValidationInput
  ): Promise<ValidationResult>;

  promote(
    knowledgeId: string,
    contractContext: ContractContext
  ): Promise<KnowledgeClaim>;

  deprecate(
    knowledgeId: string,
    reason: string
  ): Promise<void>;
}
```

---

# 29. Storage Boundary

The graph repository must be replaceable.

Do not tightly couple domain logic to a specific graph database API.

Use:

```text
Domain Model
     |
Application Services
     |
Contracts
     |
Repository Interfaces
     |
Graph Adapter
     |
GBrain / graph storage
```

The GBrain adapter is an implementation detail.

---

# 30. Critical Engineering Rules

1. Do not duplicate canonical network entities per capability.
2. Do not put all incident details into an INCIDENTS index node.
3. Do not put all pattern details into a PATTERNS index node.
4. Do not manually maintain recurrence as the source of truth.
5. Do not treat every incident as knowledge.
6. Do not treat every pattern as canonical.
7. Do not let an LLM directly mutate canonical truth.
8. All state transitions must go through contracts.
9. All promoted knowledge must have provenance.
10. Simulation results must remain separate from operational truth.
11. Hypotheses must remain distinguishable from confirmed root causes.
12. Evidence must remain distinguishable from inference.
13. Canonical is a state, not a node type.
14. Capability clusters share the canonical graph.
15. MCP tools must respect the same contracts.
16. Contract versions must be auditable.
17. Conflicting knowledge must be represented, not silently overwritten.
18. Historical reasoning pathways are reusable scaffolds, not hidden chain-of-thought.
19. Recurrence is derived from graph relationships.
20. Design for thousands of incidents and patterns without duplicating topology.

---

# 31. Acceptance Criteria

The implementation is acceptable when the following can be demonstrated:

### A. Topology

```text
UPF-003 --DEPENDS_ON--> Storage-A
```

exists as one canonical topology relationship.

### B. Incident

A new incident can be created and connected to UPF-003 without modifying the topology entity.

### C. Pattern

A pattern can be created independently.

### D. Matching

Multiple incidents can connect to the same pattern:

```text
INC-001 --MATCHES--> PAT-001
INC-017 --MATCHES--> PAT-001
INC-042 --MATCHES--> PAT-001
```

### E. Recurrence

Pattern recurrence can be derived by querying MATCHES relationships.

### F. Unmatched incident

An incident without a pattern remains valid and searchable.

### G. Pattern discovery

Repeated similar incidents can produce a candidate pattern.

### H. Lifecycle

Incident lifecycle and knowledge lifecycle are independent.

### I. Canonical state

A validated topology relationship or pattern can become CANONICAL through a contract.

### J. Simulation

A what-if scenario can reference UPF-003 without changing real topology.

### K. Auditability

Every promotion/state transition records:

- episode
- contract
- contract version
- evidence
- provenance
- timestamp
- actor/system

---

# 32. Final Design Principle

The intended architecture is:

```text
                 ZAKI / AGENTS / USERS
                         |
                    TASK EPISODE
                         |
                  CONTRACT ENGINE
                         |
        +----------------+----------------+
        |                |                |
   CAPABILITY        CAPABILITY       CAPABILITY
    CLUSTERS          CLUSTERS         CLUSTERS
        |                |                |
        +----------------+----------------+
                         |
                  FIKRACORE GRAPH
                         |
       +-----------------+------------------+
       |                 |                  |
    TOPOLOGY          OPERATIONS        KNOWLEDGE
       |                 |                  |
   Network truth      Incidents          Patterns
   Dependencies      Evidence           Pathways
   Services          Hypotheses         Claims
       |                 |                  |
       +-----------------+------------------+
                         |
                    PROVENANCE
                    AUDIT TRAIL
```

**Schema defines what exists.**

**Contracts define what is allowed.**

**Task Episode is the execution spine.**

**The canonical graph is the shared source of truth.**

**Capability clusters operate on the graph rather than creating separate knowledge silos.**

**Lifecycle state distinguishes observed, candidate, validated, canonical, simulated, deprecated, and other operational states.**

**Pattern recognition discovers recurring structures from incidents.**

**Knowledge promotion is a controlled governance step, not automatic incident storage.**
