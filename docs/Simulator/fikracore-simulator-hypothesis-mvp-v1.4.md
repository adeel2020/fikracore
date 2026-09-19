# FikraCore Simulator — Hypothesis / Investigation MVP v1.4

## Purpose of this revision

This document revises **`fikracore-simulator-hypothesis-mvp-v1.3.md`** to align the Hypothesis / Investigation Engine with the current FikraCore architecture decision:

> Use **one existing gbrain `telecombrain`** for all operational knowledge and use cases.

This revision does **not** redesign the hypothesis reasoning model.

It preserves the core v1.3 reasoning behavior and updates how the engine accesses operational knowledge.

---

# 1. Role

You are building the **FikraCore Hypothesis / Investigation Engine** for a telecom Dark NOC simulation and validation environment.

This component consumes operational evidence from synthetic scenarios and reasons against the operational knowledge available in the existing **FikraCore `telecombrain`**.

The engine must:

- observe evidence;
- generate competing hypotheses;
- correlate evidence across domains;
- test hypotheses;
- falsify weak explanations;
- request next-best evidence;
- identify unexplained residual;
- detect model insufficiency;
- support Discovery Mode;
- return RCA, PARTIAL, UNKNOWN, or MODEL_INSUFFICIENT when appropriate.

The engine is the **system under test**.

The Benchmark Evaluator is the **examiner**.

Do not merge those roles.

---

# 2. Current Implementation Sequence

The simulator build sequence is:

```text
Step 1  Reference Multi-Domain Operator Model
Step 2  100-Scenario Catalog
Step 3  Scenario Generator
Step 3.5 telecombrain Canonicalization & Backward-Compatible Migration
Step 4  Hypothesis / Investigation Engine   ← THIS DOCUMENT
Step 5  Scenario Integrity Validator
Step 6  RCA Benchmark Evaluator
```

Step 3.5 is an implementation prerequisite.

It is **not** a new runtime component.

Runtime order remains:

```text
Reference Operator Model
        +
100 Scenario Catalog
        ↓
Scenario Generator
        ↓
Scenario Integrity Validation
        ↓
Operational Evidence
        ↓
Hypothesis Engine
        ↓
InvestigationResult
        ↓
Benchmark Evaluator
        ↑
Hidden Ground Truth
```

---

# 3. Companion Artifacts

When present in the repository, treat the following as authoritative companion contracts:

```text
fikracore-reference-multidomain-operator-model-prompt-v1.md
fikracore-100-scenario-catalog-v1.md
fikracore-scenario-generator-prompt-v1.md
telecombrain-canonicalization-backward-compatible-migration-codex-prompt.md
```

Do not ignore or overwrite these contracts.

If this document conflicts with a live, verified gbrain MCP capability or canonicalization contract, prefer the live system and document the discrepancy.

---

# 4. Core Architecture Decision

There is **one operational brain**:

```text
telecombrain
```

Do not create or imply another production operational brain.

The following are semantic layers inside the same brain:

```text
telecombrain
│
├── Topology
├── Operational Evidence
├── Incidents
├── Correlation
├── Customer Tickets
├── Storytelling
├── Learning
├── Procedures
├── KPIs
└── Assets
```

These are logical knowledge layers only.

They are not separate brains.

---

# 5. Non-Negotiable Epistemic Boundary

Preserve the strongest simulator boundary.

## Simulation World

Contains complete synthetic reality:

- full topology;
- root condition;
- trigger;
- propagation;
- hidden relationships;
- generated evidence;
- injected noise.

## Operational Evidence

Contains only what an engineer or agent could observe.

It may be:

- incomplete;
- noisy;
- delayed;
- contradictory;
- stale;
- missing.

## FikraCore `telecombrain`

Represents what operations currently know.

It may be:

- incomplete;
- stale;
- partially wrong;
- missing relationships;
- missing topology;
- historically evolved.

## Hypothesis Engine

May access only:

- operational evidence;
- FikraCore `telecombrain` operational knowledge;
- operational hypothesis state.

## Evaluator

May compare final operational output against Hidden Ground Truth.

Allowed:

```text
Hidden Ground Truth → Evaluator ← Operational Prediction
```

Forbidden:

```text
Hidden Ground Truth → Hypothesis Engine
```

Forbidden:

```text
Hidden Ground Truth → telecombrain
```

> Ground truth evaluates the experiment. It does not teach the operational system.

Enforce this boundary in code and tests.

---

# 6. Major Change from v1.3

Do **not** model the operational knowledge source as a standalone:

```text
FikraCore Operational Graph
```

or:

```text
operational_graph_path
```

The operational knowledge source is the existing gbrain:

```text
telecombrain
```

The engine must access it through an abstraction such as:

```python
class FikraCoreKnowledgeProvider:
    ...
```

or:

```python
class TelecomBrainProvider:
    ...
```

The exact class name may vary.

The architectural contract must remain the same.

---

# 7. Knowledge Provider Contract

Implement a replaceable provider interface.

Recommended shape:

```python
class KnowledgeProvider:
    def get_page(self, slug: str):
        ...

    def get_links(self, slug: str):
        ...

    def get_backlinks(self, slug: str):
        ...

    def traverse(
        self,
        slug: str,
        depth: int,
        direction: str = "both",
        link_type: str | None = None
    ):
        ...

    def search(self, query: str):
        ...

    def query(self, ...):
        ...
```

Production implementation:

```text
GbrainTelecomBrainProvider
        ↓
gbrain MCP
        ↓
telecombrain
```

Test implementation:

```text
InMemoryKnowledgeProvider
```

A local/in-memory graph is allowed for deterministic testing.

It must **not** be treated as a second production brain.

---

# 8. Canonical Resolver

All entity/page lookups must support backward-compatible canonical resolution.

Implement:

```python
class CanonicalResolver:
    def resolve(self, slug: str) -> str:
        ...
```

Expected behavior:

```text
legacy slug
    ↓
CanonicalResolver
    ↓
canonical slug
```

If no mapping exists:

```text
return original slug
```

The resolver must support:

- exact legacy mappings;
- cycle detection;
- chained aliases;
- missing canonical target detection;
- deterministic behavior;
- optional provenance.

Recommended result:

```python
CanonicalResolution(
    requested_slug: str,
    resolved_slug: str,
    changed: bool,
    resolution_type: str,
    provenance: str | None
)
```

---

# 9. Read Compatibility

All operational reads should resolve canonical identity before traversal.

Conceptually:

```text
requested slug
      ↓
CanonicalResolver
      ↓
canonical slug
      ↓
KnowledgeProvider
      ↓
get_page / links / backlinks / traversal
```

This is required so historical references from:

- Incident Storyteller;
- Customer Ticket Journey;
- Correlation;
- Stories;
- Story Runs;
- Learning;
- old incident aliases

continue to work.

Historical content must not need destructive rewriting.

---

# 10. Canonical New-Write Policy

After canonicalization:

```text
READ:
legacy + canonical accepted

WRITE:
canonical only
```

If the Hypothesis Engine writes future operational artifacts such as:

- candidate hypothesis;
- validated relationship;
- investigation artifact;
- evidence link;
- future learning artifact

the reference must use canonical slugs.

Do not create new references using legacy namespace patterns.

---

# 11. GeneratedRunInput Contract

Revise the v1.3 input contract.

Do not require:

```text
operational_graph_path
```

as the primary operational knowledge source.

Recommended contract:

```python
class GeneratedRunInput(BaseModel):
    run_id: str
    scenario_id: str
    difficulty_profile: str
    seed: int

    alarms_path: str | None = None
    logs_path: str | None = None
    metrics_path: str | None = None
    kpis_path: str | None = None
    traces_path: str | None = None
    changes_path: str | None = None
    tickets_path: str | None = None
    recovery_path: str | None = None
    source_profiles_path: str | None = None
```

Operational knowledge is obtained from:

```text
KnowledgeProvider
```

not from a required second graph file.

---

# 12. Optional Frozen Knowledge Snapshot

For reproducible benchmark runs, allow an optional frozen snapshot adapter.

Example:

```text
telecombrain live
      ↓
snapshot/export
      ↓
FrozenTelecomBrainProvider
```

This may be useful to reproduce a benchmark at a known knowledge state.

It must still follow the same `KnowledgeProvider` interface.

It is a test/runtime snapshot, not another brain.

---

# 13. Scenario Scope

Continue using representative scenarios from the 100-scenario catalog.

The MVP should include at least:

```text
S1 — Clean/simple domain fault
S2 — Cross-domain Transport → PS
S3 — Noise + misleading change
S4 — Missing operational knowledge / topology relationship
S5 — Correct result is UNKNOWN
```

Allow difficulty profiles:

```text
L1
L2
L3
L4
L5
```

Do not reduce the design to only one clean scenario.

---

# 14. Scenario S1 — Simple Domain Fault

Purpose:

Validate baseline hypothesis mechanics.

Expected behavior:

```text
operational evidence
      ↓
candidate hypotheses
      ↓
support / contradiction tests
      ↓
best supported operational explanation
```

The engine must not access ground truth while reasoning.

---

# 15. Scenario S2 — Cross-Domain Fault

Example hidden reality:

```text
Transport degradation
      ↓
packet loss / path degradation
      ↓
PS connectivity degradation
      ↓
session failures
      ↓
Mobile Data degradation
```

The engine should infer the most plausible upstream cause using:

- operational evidence;
- available service/topology knowledge in `telecombrain`;
- temporal precedence;
- blast radius;
- dependency path;
- negative evidence;
- change context;
- independent telemetry.

---

# 16. Scenario S3 — Noise and Misleading Change

Use the same causal family as S2, but inject:

- duplicate alarms;
- unrelated evidence;
- delayed upstream alarm;
- unrelated pod restart;
- unrelated recent change;
- varied alarm order;
- partial evidence.

Purpose:

Test whether the engine avoids:

- alarm-count bias;
- earliest-alarm bias;
- proximity-to-change bias;
- symptom-as-root-cause bias.

---

# 17. Scenario S4 — Missing FikraCore Knowledge

This scenario becomes especially important with the live `telecombrain`.

Example hidden world:

```text
UPF-03
   ↓
Router-R21
   ↓
MPLS-PE7
   ↓
DC-GW2
```

Operational `telecombrain` knows:

```text
UPF-03
   ↓
Router-R21
   ↓
[UNKNOWN]
   ↓
DC-GW2
```

Expected behavior:

```text
known hypotheses fail to explain material observations
        ↓
unexplained residual remains
        ↓
FikraCore model challenged
        ↓
DISCOVERY_MODE
        ↓
candidate missing relationship
        ↓
next-best independent evidence requested
        ↓
candidate remains unverified
```

The engine must **not** invent:

```text
Router-R21 → MPLS-PE7
```

as confirmed knowledge.

---

# 18. Candidate Knowledge States

Use states such as:

```text
CONFIRMED
SUPPORTED
INFERRED
CANDIDATE
REJECTED
STALE
UNKNOWN
```

A candidate relationship discovered during investigation must remain non-authoritative until validated.

---

# 19. Scenario S5 — UNKNOWN

Provide intentionally insufficient evidence.

Expected terminal state:

```text
UNRESOLVED
```

or:

```text
INSUFFICIENT_EVIDENCE
```

or:

```text
MODEL_INSUFFICIENT
```

depending on the actual reason.

Do not force RCA.

Correct abstention is a successful outcome.

---

# 20. Evidence Contract

At minimum support:

```yaml
evidence_id:
event_time:
ingestion_time:
domain:
entity:
canonical_entity:
entity_type:
service:
evidence_type:
value:
source:
source_vendor:
source_native_entity:
source_reliability:
freshness:
observed_or_inferred:
```

Preserve source-native identity separately from canonical identity.

Do not destroy vendor/source-native identifiers.

---

# 21. Evidence Provenance

Every material reasoning claim must point back to:

- evidence IDs;
- topology/knowledge relationships used;
- assumptions;
- inferred vs observed state;
- source reliability.

The engine must distinguish:

```text
OBSERVED
INFERRED
CONFIRMED
REJECTED
```

Do not present inferred facts as observed facts.

---

# 22. Hypothesis Contract

Recommended:

```yaml
hypothesis_id:
statement:
candidate_root_domain:
candidate_root_entity:
canonical_root_entity:
causal_role:
assumptions: []
expected_observations: []
supporting_evidence: []
contradicting_evidence: []
missing_evidence: []
knowledge_relationships_used: []
status:
hypothesis_confidence:
causal_confidence:
explanation_coverage:
```

---

# 23. Causal Roles

Support at least:

```text
ROOT
TRIGGER
CONTRIBUTING_CONDITION
PROPAGATION_MECHANISM
AMPLIFIER
SYMPTOM
COINCIDENTAL
UNKNOWN
```

Do not assume every incident has one simplistic cause.

Support:

- common cause;
- multiple causes;
- contributing conditions;
- amplification;
- propagation.

---

# 24. Cross-Domain Correlation Method

Use:

> Topology- and Service-Aware Causal Event Correlation

The investigation should:

1. collapse alarm/evidence floods;
2. identify impacted service;
3. resolve canonical entities;
4. traverse available operational dependencies upstream;
5. create a causal event graph;
6. generate competing root-cause hypotheses;
7. score hypotheses;
8. use negative evidence to eliminate branches;
9. test the strongest hypotheses;
10. stop or enter Discovery Mode when the model cannot explain observations.

---

# 25. Hypothesis Scoring

Score candidate hypotheses using multiple dimensions.

Consider:

```text
temporal precedence
upstream position
blast-radius coverage
service dependency relevance
change relevance
independent telemetry
historical support
negative evidence
symptom-likelihood penalty
knowledge confidence
evidence freshness
source reliability
```

Do not reduce scoring to alarm count.

---

# 26. Negative Evidence

Negative evidence is first-class.

Examples:

```text
expected alarm absent
healthy neighboring node
healthy redundant path
stable dependency KPI
successful transaction on alternate path
no related change
```

Negative evidence should reduce or eliminate hypotheses.

---

# 27. Assumption Ledger

Maintain assumptions explicitly.

Recommended states:

```text
CONFIRMED
SUPPORTED
UNCERTAIN
UNTESTED
CONTRADICTED
REJECTED
```

A failed hypothesis should record which assumption failed.

Do not discard failed explanations silently.

---

# 28. Unexplained Residual

For the current best explanation calculate:

```text
observations explained
observations contradicted
observations unexplained
expected observations missing
```

A simple ratio/coverage score is sufficient for MVP.

If material unexplained residual remains:

```text
do not force RCA
```

Permit:

```text
MODEL_INSUFFICIENT
```

---

# 29. Discovery Mode

Enter Discovery Mode when:

- leading hypotheses are falsified;
- explanation coverage remains low;
- material evidence contradicts known dependencies;
- no known topology path explains propagation;
- significant observations remain unexplained.

Discovery Mode should:

1. identify violated assumptions;
2. list unexplained observations;
3. state that operational knowledge may be incomplete;
4. request next-best topology/path evidence;
5. generate candidate relationship hypotheses;
6. keep candidates non-authoritative;
7. permit MODEL_INSUFFICIENT.

---

# 30. Next-Best Evidence

The engine should request evidence that maximizes expected uncertainty reduction.

Consider:

```text
information gain
cost
latency
risk
reliability
availability
```

Do not request every possible piece of evidence.

Prioritize the next evidence most likely to discriminate leading hypotheses.

---

# 31. Human Validation

No full HITL platform is required for this MVP.

Provide simple actions such as:

```text
validate candidate REL-001
reject candidate REL-001
```

Record:

```text
candidate
supporting evidence
validator
decision
reason
timestamp
```

Human validation is a governance gate.

It is not simulator ground truth.

---

# 32. Knowledge Update Rule

The Hypothesis Engine must not automatically write candidate topology into `telecombrain`.

Allowed:

```text
Candidate Relationship
    ↓
Evidence
    ↓
Human / SME Validation
    ↓
Validated Knowledge
    ↓
telecombrain
```

Forbidden:

```text
Candidate Relationship
    ↓
automatic promotion
    ↓
telecombrain
```

---

# 33. Topology Integration

The Hypothesis Engine must be topology-ready.

Future canonical relationships may include:

```text
depends-on
connected-to
routes-through
carried-by
hosted-on
runs-on
backhauled-by
powered-by
fails-over-to
supports-service
part-of-failure-domain
charges-via
authenticates-via
resolves-via
timed-by
uses-database
uses-cache
uses-message-bus
```

Do not assume every relationship exists.

Use only what `telecombrain` currently knows.

Missing edges are part of the experiment.

---

# 34. Canonical Entity Handling

When evidence references a source-native entity:

```text
MME01
mme-01
Huawei-MME-A
mobile-core/network-functions/mme-01
```

the system should attempt:

```text
source-native identity
        ↓
entity resolution
        ↓
canonical slug
```

Preserve both identities.

Do not overwrite raw source identifiers.

---

# 35. Existing Use-Case Compatibility

The implementation must not break:

```text
Incident Storyteller
Customer Ticket Journey
Correlation
Story Runs
Learning
Playbooks
Query Assets
```

The Hypothesis Engine should consume canonical resolution services rather than require these existing components to rewrite historical data.

---

# 36. Existing Story Artifacts

Historical stories may contain legacy slugs.

That is acceptable.

Do not rewrite old stories merely to replace identifiers.

At read time:

```text
historical slug
    ↓
CanonicalResolver
    ↓
current canonical entity
```

This preserves provenance and history.

---

# 37. Existing Ticket Artifacts

Customer Ticket Journey references must continue working.

The Hypothesis Engine may use ticket context as evidence or impact context when available.

Do not change ticket semantics during this MVP.

---

# 38. LLM Usage

Use deterministic Python for:

```text
graph traversal
canonical resolution
timestamp logic
evidence counting
scenario input parsing
seeded behavior
scoring where defined
metric calculation
hidden-truth evaluation
```

LLM may assist with:

```text
candidate hypothesis wording
assumption explanations
next-best-evidence suggestions
failed-hypothesis explanation
investigation summary
```

Every LLM claim must:

- cite evidence IDs; or
- be explicitly marked as hypothesis/inference.

Never let the LLM fabricate a missing topology relationship as fact.

---

# 39. Primary Metrics

Track at least:

1. Root Cause Top-3 Accuracy
2. Wrong Hypotheses Correctly Falsified
3. Evidence Requests Before Terminal Decision
4. Steps / Time to First Useful Hypothesis
5. Forced-RCA Rate when UNKNOWN is correct
6. Explanation / Provenance Quality

Secondary diagnostics:

```text
terminal state
explanation coverage
unexplained residual
topology-gap detection
repeated falsified hypothesis count
candidate relationship count
canonical-resolution failures
```

---

# 40. Baseline Comparison

Compare at least:

## Baseline A

```text
earliest severe alarm
```

or:

```text
highest alarm-count domain
```

## Method B

FikraCore hypothesis reasoning using:

```text
telecombrain
canonical identities
topology/service context
positive evidence
negative evidence
falsification
next-best evidence
```

Run both against the same hidden reality.

Do not force Method B to win.

If the hypothesis approach does not materially outperform the baseline, report it.

---

# 41. Reproducibility

Every run must record:

```text
scenario_id
run_id
seed
difficulty_profile
knowledge_provider_type
telecombrain snapshot/version if available
canonicalization mapping version
evidence inputs
```

This is important because `telecombrain` may evolve over time.

---

# 42. Investigation Result Contract

Recommended:

```python
class InvestigationResult(BaseModel):
    run_id: str
    scenario_id: str

    terminal_state: str

    ranked_hypotheses: list
    selected_hypothesis_id: str | None

    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    missing_evidence: list[str]

    explanation_coverage: float | None
    unexplained_observations: list[str]

    knowledge_gaps: list
    candidate_relationships: list

    canonical_entities_used: list[str]

    reasoning_summary: str
    provenance: list
```

Do not put Hidden Ground Truth inside this result.

---

# 43. Terminal States

Support:

```text
EXPLAINED
PARTIALLY_EXPLAINED
UNRESOLVED
INSUFFICIENT_EVIDENCE
CONFLICTING_EVIDENCE
MODEL_INSUFFICIENT
```

A terminal result should explain why the investigation stopped.

---

# 44. Knowledge Provider Failure Handling

If gbrain MCP is unavailable:

```text
do not silently substitute invented knowledge
```

Allow one of:

```text
explicit provider failure
frozen snapshot provider
in-memory test provider
```

The provider used must be recorded in the run metadata.

---

# 45. gbrain MCP

Discover actual MCP capabilities before coding tightly against assumed tools.

Likely relevant operations include:

```text
get_page
list_pages
search
query
get_links
get_backlinks
traverse_graph
```

Use only tools actually exposed by the live MCP server.

Do not invent unsupported parameters such as a `graph` argument if the tool contract does not expose one.

---

# 46. Repository Shape

Adapt to the existing project, but a useful structure is:

```text
fikracore-hypothesis-mvp/
├── README.md
├── pyproject.toml
│
├── src/fikracore_mvp/
│   ├── contracts.py
│   ├── evidence.py
│   ├── knowledge/
│   │   ├── base.py
│   │   ├── gbrain_provider.py
│   │   ├── snapshot_provider.py
│   │   └── in_memory_provider.py
│   │
│   ├── canonical/
│   │   └── resolver.py
│   │
│   ├── hypotheses.py
│   ├── investigator.py
│   ├── correlation.py
│   ├── discovery.py
│   ├── evidence_selector.py
│   ├── scoring.py
│   └── cli.py
│
├── tests/
│   ├── test_hidden_truth_boundary.py
│   ├── test_canonical_resolution.py
│   ├── test_gbrain_provider.py
│   ├── test_s1_baseline.py
│   ├── test_s2_cross_domain.py
│   ├── test_s3_noise.py
│   ├── test_s4_topology_gap.py
│   ├── test_s5_unknown.py
│   └── test_existing_use_case_compatibility.py
│
└── results/
```

Do not create microservices.

---

# 47. Minimal Technology Stack

Prefer:

```text
Python 3.12
Pydantic
NetworkX where useful for local reasoning structures
JSON/YAML
JSONL evidence
deterministic Python evaluator
CLI-first
pluggable LLM interface
```

Do not require:

```text
Kafka
Grafana LGTM
Neo4j
Kubernetes
Docker Compose
React
distributed services
```

for the reasoning MVP.

These may be production integrations later.

---

# 48. NetworkX Clarification

NetworkX is allowed for:

- local hypothesis event graphs;
- deterministic traversal tests;
- scenario test fixtures;
- temporary investigation structures.

NetworkX must not be described as the production FikraCore operational brain.

Production operational knowledge remains:

```text
gbrain telecombrain
```

---

# 49. Current End-to-End Runtime Position

```text
Reference Multi-Domain Operator Model
              +
       100-Scenario Catalog
              ↓
       Scenario Generator
              ↓
   Scenario Integrity Validation
              ↓
      OPERATIONAL EVIDENCE
              │
              │
              │          FikraCore
              │        telecombrain
              │             │
              │     CanonicalResolver
              │             │
              │    KnowledgeProvider
              │             │
              └───────┬─────┘
                      ↓
┌────────────────────────────────────┐
│ FikraCore Hypothesis Engine        │
│                                    │
│ Observe                            │
│ Hypothesize                        │
│ Correlate                          │
│ Test                               │
│ Falsify                            │
│ Request Next-Best Evidence         │
│ Discovery / RCA / UNKNOWN          │
└────────────────────────────────────┘
                      ↓
             InvestigationResult
                      ↓
              Benchmark Evaluator
                      ↑
              Hidden Ground Truth
```

---

# 50. Definition of Done

The v1.4 Hypothesis Engine is complete when:

```text
[ ] no second operational brain is created
[ ] operational_graph_path is not a required production input
[ ] KnowledgeProvider abstraction exists
[ ] gbrain telecombrain provider exists
[ ] CanonicalResolver is integrated
[ ] legacy entity references remain readable
[ ] new operational references use canonical IDs
[ ] existing Incident Storyteller remains compatible
[ ] Customer Ticket Journey remains compatible
[ ] S1 works
[ ] S2 cross-domain reasoning works
[ ] S3 survives noise/misleading change
[ ] S4 detects topology/model gap
[ ] S4 does not auto-write candidate edge
[ ] S5 can correctly return UNKNOWN
[ ] Hidden Truth cannot enter operational reasoning
[ ] provenance is preserved
[ ] baseline comparison exists
[ ] deterministic tests exist
[ ] provider/snapshot version is recorded
```

---

# 51. Explicitly Out of Scope

Do not implement in this step:

```text
full production topology ingestion
complete operator CMDB integration
Kafka deployment
Grafana LGTM deployment
full HITL platform
multi-agent orchestration
automatic skill learning
proactive What-If resilience
production UI
Zaki voice orchestration
mass schema cleanup
destructive legacy slug deletion
```

Those belong to later phases.

---

# 52. Important Future Boundary

The proper telecom topology will be built in the same `telecombrain`.

Future architecture:

```text
                   FikraCore
                 telecombrain
                      │
     ┌────────────────┼────────────────┐
     │                │                │
  Topology        Operations       Knowledge
     │                │                │
 Functions         Incidents        Procedures
 Services          Evidence         Runbooks
 Transport         Correlation      Learning
 Hosting           Tickets          KPIs
 Sites             Stories          Protocols
 Failure Domains
     │                │                │
     └────────────────┼────────────────┘
                      │
              Hypothesis Engine
```

The simulator Hidden Truth Graph remains separate and evaluator-only.

---

# 53. Execution Instructions for Codex

Proceed in this order:

```text
1. Inspect the existing repository
2. Read companion contracts
3. Inspect the canonicalization implementation
4. Discover live gbrain MCP capabilities
5. Implement KnowledgeProvider abstraction
6. Implement/consume CanonicalResolver
7. Remove production dependency on operational_graph_path
8. Preserve local graph only as test adapter
9. Implement/refactor hypothesis reasoning
10. Add scenario tests
11. Add hidden-truth boundary tests
12. Add backward-compatibility tests
13. Run all tests
14. Produce a concise implementation report
```

Do not mutate `telecombrain` topology automatically as part of the Hypothesis Engine.

Do not rewrite existing story/ticket history.

Do not simplify the architecture by creating another operational graph.

---

# Final Goal

The Hypothesis Engine must reason against:

```text
Operational Evidence
        +
FikraCore telecombrain
        ↓
Canonical identities
        ↓
Topology / Services / Operational Knowledge
        ↓
Causal Hypothesis Reasoning
        ↓
RCA / PARTIAL / UNKNOWN / MODEL_INSUFFICIENT
```

while preserving:

```text
Hidden Ground Truth → Evaluator only
```

and preserving all existing FikraCore use cases.

One brain.

One canonical identity model.

No storyteller breakage.

No customer-ticket breakage.

No competing operational graph.

Ready for the next stage of full multi-domain telecom topology.
