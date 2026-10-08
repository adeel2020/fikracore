# Pipeline 2 — Emerging Evidence → Preventive Intelligence

### Finalized implementation plan using the unified FikraCore principle

The implementation should **extend the existing FikraCore cognitive substrate**, not create a second preventive architecture.

The governing principle is:

> **Pipeline 2 owns preventive processing semantics; shared FikraCore contracts own reusable domain meaning.**

So Pipeline 2 reuses the existing Evidence, Pattern, Topology/Relationship, `OperationalContextContract`, `TaskEpisodeContract`, Remediation, Promotion, HITL, and Knowledge mechanisms wherever applicable.

---

# 1. Final runtime design

```text
LIVE NETWORK
    │
    ▼
2.1  Emerging Evidence Ingestion
    │
    ▼
2.2  Evidence Retrieval & Windowing
    │
    ▼
2.3  Canonical Normalization
    │
    ▼
2.4  Evidence Association & Deduplication
    │
    ▼
2.4a Evidence Sanity Gate
    │
    ▼
2.5  Temporal Accumulation & Trajectory
    │
    ▼
2.6  Emerging Condition Detection
    │
    ▼
2.7  Condition Identity & Lifecycle
    │
    ▼
2.8  Operational Context Assembly
    │
    ▼
     Existing OperationalContextContract
    │
    ▼
2.9  Preventive Inference
    ▲
    │
    ├── Topology / Relationships
    ├── Statistical Relationships / Baselines
    └── Impact Quantification
    │
    ▼
2.9a Inference Sanity Gate
    │
    ├──────────────► insufficient / contradictory
    │                  evidence → monitor / evidence gap
    │
    ▼
2.10 Preventive Insight
    │
    ▼
2.11 Preventive Action / Monitoring
    │
    ├──────────────► Incident threshold → Pipeline 1
    │
    ▼
2.12 Outcome Observation
    │
    ▼
2.13 Promotion Candidate
    │
    ▼
     Existing PromotionContract
    │
    ▼
2.14 HITL Validation
    │
    ▼
2.15 Knowledge Promotion
    │
    ▼
2.16 Knowledge Feedback
    │
    ├── Pattern recognition
    ├── Preventive signatures
    ├── Relationships
    └── Future inference
```

The **sanity gates are gates, not business-domain stages**. They should be implemented as shared validation capabilities.

---

# 2. Contract reuse matrix

This should be settled before writing Pipeline 2 code.

| Existing capability/contract         | Pipeline 2 use      | New contract?                                                             |
| ------------------------------------ | ------------------- | ------------------------------------------------------------------------- |
| Raw/Emerging/Validated Evidence      | Yes                 | **Reuse**                                                                 |
| Canonical normalization model        | Yes                 | **Reuse/extend only if necessary**                                        |
| PatternContract                      | Yes                 | **Reuse**                                                                 |
| Topology Relationship contracts      | Yes                 | **Reuse**                                                                 |
| OperationalContextContract           | Yes                 | **Reuse**                                                                 |
| TaskEpisodeContract                  | Yes                 | **Reuse**                                                                 |
| RemediationContract                  | Yes                 | **Reuse**                                                                 |
| PromotionContract                    | Yes                 | **Reuse**                                                                 |
| HITL governance                      | Yes                 | **Reuse**                                                                 |
| Knowledge structures                 | Yes                 | **Reuse**                                                                 |
| Emerging Condition                   | New semantic object | **New, but keep focused**                                                 |
| Condition lifecycle state            | Needed              | **Prefer part of condition model/state, not a parallel context contract** |
| Preventive Insight                   | New semantic output | **New if current contracts don't represent it**                           |
| Generic ReasoningContract            | Not needed          | **Do not create**                                                         |
| PreventiveOperationalContextContract | Not needed          | **Do not create**                                                         |
| PreventiveHITLContract               | Not needed          | **Do not create**                                                         |
| PreventivePromotionContract          | Not needed          | **Do not create**                                                         |

One important caveat: your existing `OperationalContextContract` should have a **generic operational subject**, rather than requiring every context to masquerade as an incident. That is the one contract refinement I would make before Pipeline 2 implementation.

---

# 3. Stage-by-stage implementation

## 2.1 — Emerging Evidence Ingestion

### Goal

Bring INFO/WARN signals into FikraCore without prematurely interpreting them.

### Input

Kafka events such as:

```json
{
  "event_id": "evt-123",
  "timestamp": "...",
  "source": "alarm-manager",
  "vendor": "vendor-a",
  "alarm_code": "A123",
  "severity": "WARN",
  "equipment_id": "RTR-21"
}
```

### Rules

Do:

* preserve source truth
* retain original alarm identity
* attach ingestion metadata
* support replay
* assign ingestion sequence/offset

Do not:

* infer RCA
* declare an emerging condition
* assign arbitrary confidence
* perform preventive reasoning in Kafka producers

### Output

`EmergingEvidence`

---

# 4. Stage 2.2 — Evidence Retrieval & Windowing

This stage should retrieve **both current and historical evidence**.

```text
                    Current signal
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
            Kafka                  LGTM
        live evidence       historical evidence
              │                     │
              └──────────┬──────────┘
                         ▼
                Retrieval Window
```

### Retrieval dimensions

* entity
* canonical/known identity
* time window
* domain
* service
* alarm/event family
* relevant metrics/KPIs
* logs/traces
* change records

### Important rule

Kafka and LGTM have different roles:

> **Kafka preserves/streams live evidence; LGTM supplies historical observability retrieval.**

Do not turn LGTM into the reasoning engine.

---

# 5. Stage 2.3 — Canonical Normalization

Map heterogeneous source representations to FikraCore's canonical network model.

Example:

```text
Vendor A: ROUTER_ALARM_77
Vendor B: LINK_WARN_009
Vendor C: RTR-PATH-DEG
             │
             ▼
Canonical entity: IP:PE:RTR-21
```

### Preserve both

```text
source_identity
canonical_identity
```

because source provenance is still required for validation and explanation.

### Acceptance criteria

Given the same logical network entity from different vendors, FikraCore should resolve them to the same canonical entity without erasing source-specific information.

---

# 6. Stage 2.4 — Evidence Association & Deduplication

This is more important than simply calling it "grouping."

### Deduplication

Remove repeated observations representing the same event.

### Association

Determine whether observations may belong together.

For example:

```text
WARN RTR-21
WARN RTR-21
WARN VRF-N3-01
WARN UPF-003
```

could result in:

```text
same observation → deduplicated

RTR-21 + VRF-N3-01
    → candidate association

UPF-003
    → independent until evidence justifies association
```

### Critical rule

```text
Temporal proximity ≠ condition membership
Same domain      ≠ condition membership
Same severity    ≠ condition membership
```

Association needs evidence.

This prevents unrelated live conditions from collapsing into one giant condition.

---

# 7. Stage 2.4a — Evidence Sanity Gate

This should be a **shared FikraCore validation capability**, not a Pipeline-2-only contract.

## Checks

### Identity

* entity exists or explicitly unresolved
* source identity valid
* canonical mapping valid

### Temporal

* timestamp valid
* event ordering plausible
* retrieval window correct

### Duplication

* event is not being counted repeatedly

### Provenance

* source known
* evidence traceable

### Freshness

* evidence has not exceeded allowed freshness

### Scope

* unrelated domains/entities have not been accidentally merged

### Completeness

* required attributes available

### Contradiction

* detect obvious contradictions between observations

### Outcomes

```text
VALID
DEGRADED / PARTIAL
INSUFFICIENT
CONTRADICTORY
REJECTED
```

Do **not** force `VALID` merely to keep the pipeline moving.

---

# 8. Stage 2.5 — Temporal Accumulation & Trajectory

This is one of the genuinely new capabilities of Pipeline 2.

The key question is no longer:

> "Did an alarm occur?"

It becomes:

> **"How is the condition evolving?"**

Track:

```text
recurrence
persistence
frequency
acceleration
duration
severity evolution
sequence
cross-entity propagation
performance relationship
```

Example:

```text
12:00     WARN
13:10     WARN
14:05     WARN
15:02     WARN
15:20     WARN
15:31     WARN
```

The important signal may be:

```text
inter-arrival time ↓
frequency ↑
```

rather than any individual alarm.

### Output

`EvidenceTrajectory`

This does not yet mean "failure is coming."

---

# 9. Stage 2.6 — Emerging Condition Detection

Now FikraCore determines whether the accumulated trajectory constitutes an actual **emerging condition**.

Possible conditions:

* recurrent transport instability
* rising CPU pressure
* signaling abnormality
* increasing packet loss
* storage latency degradation
* repeated dependency stress
* abnormal service-quality trajectory

### Important distinction

```text
Evidence trajectory
       ≠
Emerging condition
```

Detection requires sufficient evidence that the observations form a meaningful developing state.

### Output

`EmergingCondition`

---

# 10. Stage 2.7 — Condition Identity & Lifecycle

This is necessary for the **multi-condition/multi-incident** operating model.

Each condition needs its own identity.

Example:

```text
C-001
entity: RTR-21
type: transport instability
status: EMERGING

C-002
entity: UPF-007
type: resource pressure
status: MONITORING

C-003
entity: MSC-02
type: signaling abnormality
status: RESOLVED
```

### Lifecycle

I would initially support:

```text
DETECTED
EMERGING
MONITORING
ESCALATING
RESOLVED
DISMISSED
MERGED
SPLIT
ESCALATED_TO_INCIDENT
```

The last three are especially important.

### Why?

Because evidence can change the interpretation:

```text
C-001 + C-002
     ↓
new evidence
     ↓
actually same condition
     ↓
MERGE
```

or:

```text
C-003
     ↓
new evidence
     ↓
two unrelated causes
     ↓
SPLIT
```

Do not make conditions permanently immutable.

---

# 11. Stage 2.8 — Operational Context Assembly

This is **not a new context architecture**.

It assembles the existing:

> `OperationalContextContract`

for the current operational subject.

That subject can now be:

```text
Incident
EmergingCondition
Pattern
PreventiveInsight
```

depending on the context.

### Context sources

```text
EmergingCondition
      +
Evidence
      +
Topology
      +
Patterns
      +
Changes
      +
Services
      +
Domain information
      +
Historical episodes
      +
Performance context
```

### Output

**Existing `OperationalContextContract`**

This is what Zaki uses for cognitive augmentation.

---

# 12. Stage 2.9 — Preventive Inference

This is the core intelligence stage.

It should **consume**, rather than reimplement, the other analytical pipelines.

```text
                    Preventive Inference
                           ▲
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          │                │                │
       Pipeline 1       Pipeline 4       Pipeline 5
     Investigation     Statistical       Impact
     / Correlation     Relationship    Quantification
          │            / Baseline          │
          └────────────────┬───────────────┘
                           │
                    Existing knowledge
```

### Questions

* Is the condition abnormal?
* Is it persistent?
* Is it worsening?
* Is it historically significant?
* What can it plausibly evolve into?
* Which entities/services are exposed?
* What evidence supports that?
* What evidence contradicts it?
* What evidence is missing?
* Is preventive action justified?

### Avoid

* arbitrary confidence percentages
* unsupported causal claims
* future-data leakage
* pretending incomplete topology is complete

---

# 13. Stage 2.9a — Inference Sanity Gate

This is separate from evidence sanity.

Evidence can be valid while the inference is still bad.

### Checks

#### Evidence sufficiency

```text
Enough independent evidence?
```

#### Correlation/causation

```text
correlated ≠ causal
```

#### Baseline validity

Was the selected baseline actually appropriate?

#### Topology validity

```text
observed
known
inferred
unknown
```

must remain distinguishable.

#### Contradictory evidence

Example:

```text
alarm trajectory worsening
BUT
performance normal
AND
no dependency degradation
```

Inference must weaken or remain qualified.

#### Scope

Don't claim network-wide risk from evidence covering one entity.

#### Future leakage

Do not use evidence generated after the prediction point to make the prediction look successful.

#### Specificity

Don't make a more specific prediction than the evidence supports.

### Outcomes

```text
SUPPORTED
QUALIFIED
INSUFFICIENT
CONTRADICTED
ABSTAIN
```

`ABSTAIN` should be a first-class success state, not an error.

---

# 14. Stage 2.10 — Preventive Insight

This is the explainable operational output.

A strong schema should answer:

```text
condition
why_detected
supporting_evidence
trajectory
context
potential_evolution
potentially_impacted_entities
potentially_impacted_services
missing_evidence
recommended_monitoring
recommended_action
limitations
```

Example:

> Repeated N3 transport instability associated with RTR-21 is increasing in frequency over the last six hours. The trajectory is abnormal relative to baseline and intersects the UPF-003 service path. No confirmed service incident exists at this time. Continued progression may result in throughput degradation. Additional performance evidence is required to strengthen the assessment.

That is much safer than:

> "UPF will fail."

---

# 15. Stage 2.11 — Preventive Action / Monitoring

The output doesn't always need to be a remediation.

Possible outcomes:

```text
MONITOR
COLLECT_MORE_EVIDENCE
NOTIFY_DOMAIN
RECOMMEND_PREVENTIVE_ACTION
START_SIMULATION
ESCALATE
TRIGGER_INCIDENT_INVESTIGATION
```

### Pipeline 1 transition

Correcting the earlier numbering:

```text
Preventive condition
       ↓
threshold / confirmed service impact
       ↓
Incident Trigger
       ↓
Pipeline 1 — Investigation & Correlation
```

Pipeline 2 therefore becomes an **early-warning feeder into Pipeline 1**.

---

# 16. Stage 2.12 — Outcome Observation

This stage is essential if you want Pipeline 2 to actually learn.

Record:

```text
what did we predict?
what happened afterward?
when did it happen?
did degradation occur?
did an incident occur?
did preventive action work?
was the condition false?
```

Example:

```text
Prediction:
"Likely throughput degradation if trajectory continues"

Observed outcome:
"No degradation after mitigation"

Result:
Prediction partially/fully invalidated
```

This is the evidence that later supports knowledge promotion.

---

# 17. Stage 2.13 — Promotion Candidate

Only some outcomes should become knowledge.

Candidate criteria can include:

```text
repeatedly observed
validated outcome
operational relevance
sufficient evidence
novel or improved knowledge
reusable pattern
```

Possible candidate types:

```text
PRECURSOR_PATTERN
PREVENTIVE_SIGNATURE
RELATIONSHIP
PLAYBOOK
THRESHOLD_BEHAVIOR
TRAJECTORY_PATTERN
```

Use the **existing `PromotionContract`**.

---

# 18. Stage 2.14 — HITL Validation

Reuse the same HITL governance mechanism from Pipeline 1.

The validation target is different.

### Pipeline 1

```text
Is RCA/remediation correct?
```

### Pipeline 2

```text
Was the emerging condition real?
Was the trajectory meaningful?
Was the prediction supported by subsequent outcome?
Is this knowledge reusable?
```

### Important

HITL should not be mandatory for every preventive observation.

It should be policy-driven.

---

# 19. Stage 2.15 — Knowledge Promotion

Use the existing knowledge-promotion pathway.

Do not build a second preventive knowledge database.

Promote into the same FikraCore knowledge ecosystem:

```text
Patterns
Relationships
Playbooks
Preventive signatures
Validated operational knowledge
```

with provenance identifying the knowledge source.

---

# 20. Stage 2.16 — Knowledge Feedback

The feedback path should be explicit.

```text
Validated Knowledge
       │
       ├──► Pattern Recognition
       ├──► Preventive Signatures
       ├──► Relationship Knowledge
       ├──► Playbooks
       └──► Future Inference
```

This creates the learning cycle:

```text
Observe
  ↓
Accumulate
  ↓
Detect
  ↓
Infer
  ↓
Act
  ↓
Observe outcome
  ↓
Validate
  ↓
Learn
  ↓
Detect better next time
```

---

# 21. Multi-condition / multi-incident runtime model

This is not an optional feature. It should influence implementation from day one.

Your state model should allow:

```text
LIVE NETWORK
│
├── C-001  Emerging condition
├── C-002  Emerging condition
├── C-003  Monitoring
├── C-004  Escalating
│
├── I-001  Investigation
├── I-002  Mitigation
└── I-003  Closed
```

Conditions and incidents can coexist.

They can also interact:

```text
C-001 ──► I-001
C-002 ──► C-005
I-002 ──► C-006
```

Do not build a single global Pipeline 2 state.

Build **condition-scoped state** over a continuous event stream.

---

# 22. Shared sanity framework

Rather than creating Pipeline-2-specific validators, build a shared validation layer that both Pipeline 1 and Pipeline 2 can use.

```text
                 Shared Validation
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Evidence    Association   Inference
       sanity        sanity       sanity
```

Later it can also validate:

```text
Promotion candidate
Topology assumptions
Simulation results
Impact calculations
```

This maximizes reuse.

---

# 23. Recommended implementation order

I would **not implement 2.1–2.16 sequentially as sixteen independent features**.

Implement them in vertical slices.

## Phase 0 — Contract alignment

Before Pipeline 2 code:

```text
1. Review OperationalContextContract
2. Generalize operational subject if incident-specific
3. Confirm EmergingEvidence reuse
4. Confirm PatternContract reuse
5. Confirm TaskEpisodeContract reuse
6. Confirm PromotionContract reuse
7. Define shared sanity-check interfaces
```

This is the architectural foundation.

---

## Phase 1 — Build the minimum preventive detection loop

Implement:

```text
2.1 Ingestion
   ↓
2.2 Retrieval
   ↓
2.3 Canonicalization
   ↓
2.4 Association + Dedup
   ↓
2.4a Evidence Sanity
   ↓
2.5 Trajectory
   ↓
2.6 Emerging Condition
   ↓
2.7 Condition Lifecycle
```

At the end of Phase 1 you should be able to demonstrate:

> **Thousands of INFO/WARN events → multiple independent emerging conditions detected concurrently.**

This is the most important first milestone.

---

## Phase 2 — Cognitive context + preventive inference

Add:

```text
2.8 Operational Context Assembly
   ↓
Existing OperationalContextContract
   ↓
2.9 Preventive Inference
   ↓
2.9a Inference Sanity
   ↓
2.10 Preventive Insight
```

Milestone:

> FikraCore can explain **why a condition is emerging and what could happen next**, without pretending certainty.

---

## Phase 3 — Operational integration

Add:

```text
2.11 Preventive Action / Monitoring
       │
       └──► Pipeline 1
```

Milestone:

> Preventive detection can coexist with active incidents and escalate a condition into investigation when appropriate.

---

## Phase 4 — Learning loop

Add:

```text
2.12 Outcome Observation
2.13 Promotion Candidate
2.14 HITL
2.15 Knowledge Promotion
2.16 Feedback
```

Milestone:

> A preventive observation can eventually become validated reusable FikraCore knowledge.

---

# 24. Suggested internal implementation boundaries

I would structure the code around capabilities rather than around "Pipeline 2 contracts."

Conceptually:

```text
pipeline/
  preventive/
    ingestion/
    retrieval/
    normalization/
    association/
    trajectory/
    condition/
    inference/
    insight/
    action/
    outcome/

validation/
  evidence/
  association/
  inference/
  promotion/

contracts/
  existing/
    evidence/
    pattern/
    topology/
    operational_context/
    task_episode/
    remediation/
    promotion/

knowledge/
  patterns/
  relationships/
  playbooks/
  preventive/
```

The exact folder names can adapt to your current repository structure.

The important thing is:

> **Don't create `preventive/contracts/` containing duplicates of existing FikraCore contracts.**

---

# 25. What should be persisted?

At minimum:

### Evidence

Immutable.

```text
Raw / Emerging / Validated
```

### Trajectory

Mutable as new observations arrive.

```text
start
last_seen
frequency
trend
sequence
evidence_refs
```

### Emerging Condition

Stateful.

```text
condition_id
status
subject_entities
domains
evidence_refs
trajectory_ref
created_at
updated_at
relationships
```

### Operational Context

Assembled view, not necessarily the authoritative datastore.

### Preventive Insight

Versioned output associated with the condition.

### Outcome

Immutable observation of what happened after the prediction/action.

### Promotion Candidate

Existing promotion lifecycle.

---

# 26. The most important sanity rules to implement first

For your POC, I would prioritize these:

### Rule 1 — No unsupported condition

```text
Insufficient evidence
→ no emerging condition
```

### Rule 2 — No accidental merging

```text
Different entities
+ different trajectories
+ no supporting relationship
→ separate conditions
```

### Rule 3 — No causal overclaim

```text
Correlation
→ cannot automatically become causation
```

### Rule 4 — No arbitrary confidence

Use evidence quality/count/relationships and justified scores rather than invented percentages.

### Rule 5 — No future leakage

Prediction must only see evidence available **before prediction time**.

### Rule 6 — No false completeness

Unknown topology remains unknown.

### Rule 7 — Contradiction is a valid outcome

```text
supporting evidence
+
contradictory evidence
→ qualified / unresolved
```

### Rule 8 — Prediction must be falsifiable

A preventive insight should specify what future evidence would confirm or disconfirm it.

---

# 27. Definition of done for Pipeline 2

I would consider Pipeline 2 architecturally complete when it can demonstrate all of these in one live/replay test:

```text
1. Thousands of INFO/WARN events arrive.

2. Events are retained as source truth.

3. Historical evidence is retrieved from LGTM.

4. Vendor events normalize to canonical entities.

5. Duplicates are removed without losing provenance.

6. Unrelated signals remain separate.

7. Multiple trajectories evolve concurrently.

8. Multiple emerging conditions exist simultaneously.

9. Existing OperationalContextContract is populated for each
   relevant condition.

10. Pipeline 4 / baseline information can be consumed without
    reimplementing statistical analysis.

11. Pipeline 5 / impact information can be consumed without
    reimplementing impact quantification.

12. Preventive inference can abstain when evidence is insufficient.

13. Preventive insight explains evidence, trajectory, uncertainty,
    and possible evolution.

14. Preventive monitoring can escalate a condition into Pipeline 1.

15. Pipeline 1 incidents can coexist with Pipeline 2 conditions.

16. Outcomes are observed after predictions.

17. Validated outcomes can enter the existing PromotionContract.

18. Promoted knowledge feeds future prevention.
```

## Final architecture decision

I would now freeze Pipeline 2 as:

```text
2.1  Emerging Evidence Ingestion
2.2  Evidence Retrieval & Windowing
2.3  Canonical Normalization
2.4  Evidence Association & Deduplication
2.4a Evidence Sanity Gate
2.5  Temporal Accumulation & Trajectory
2.6  Emerging Condition Detection
2.7  Condition Identity & Lifecycle
2.8  Operational Context Assembly
     └─ Existing OperationalContextContract
2.9  Preventive Inference
     ├─ Topology / Relationships
     ├─ Statistical Relationships / Baselines
     └─ Impact Quantification
2.9a Inference Sanity Gate
2.10 Preventive Insight
2.11 Preventive Action / Monitoring
     └─ Incident Trigger → Pipeline 1
2.12 Outcome Observation
2.13 Promotion Candidate
     └─ Existing PromotionContract
2.14 HITL Validation
2.15 Knowledge Promotion
2.16 Knowledge Feedback
```

This preserves the critical stages while avoiding the architectural mistake of creating a **second cognitive stack beside Pipeline 1**. The two pipelines become complementary paths through the **same FikraCore knowledge, context, episode, governance, and learning substrate**.
