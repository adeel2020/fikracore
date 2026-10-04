# FikraCore Contract-Driven Operational Reasoning

## Core principle

FikraCore uses a **contract-driven, stateful reasoning loop** in which each contract adds a stronger operational interpretation to the same Task Episode, culminating in validated learning that can be promoted back into FikraCore knowledge.

The implementation should be **traceable and closed-loop**.

## Contract sequence

1. **Behavior Contract** — Defines how FikraCore should reason and behave.
2. **Operational Context Contract** — Defines the current network and service context available to FikraCore.
3. **Emerging Condition Detection Contract** — Defines how FikraCore detects developing conditions before an incident.
4. **Hypothesis Contract** — Defines competing explanations, ranking, confidence, and status.
5. **Evidence Contract** — Defines evidence, provenance, quality, and supporting / contradicting / neutral / missing status.
6. **Finding / Validation Contract** — Defines when an inferred result becomes a validated operational finding.
7. **Outcome Contract** — Records what happened afterward: prevented, escalated, false positive, or unresolved.
8. **Task Episode Contract** — Captures the complete operational episode and connects observation, reasoning, validation, and outcome.
9. **Learning Contract** — Defines what reusable learning candidate can be extracted from the episode.
10. **Knowledge Promotion Contract** — Controls what validated learning is allowed into FikraCore operational knowledge.

## Conceptual flow

```text
BEHAVIOR
   ↓
OPERATIONAL CONTEXT
   ↓
EMERGING CONDITION
   ↓
HYPOTHESES
   ↕
EVIDENCE
   ↓
VALIDATION / FINDING
   ↓
OUTCOME
   ↓
TASK EPISODE
   ↓
LEARNING CANDIDATE
   ↓
KNOWLEDGE PROMOTION
   ↓
FIKRACORE OPERATIONAL KNOWLEDGE
```

This is **not a rigid waterfall**. The contracts are connected through shared state and events, with the Task Episode acting as the common state thread.

## Implementation model

Do not implement ten independent AI engines.

```text
                    ZAKI
          Intent / Voice / UI
                    │
                    ▼
            Task / Episode Context
                    │
                    ▼
          ┌─────────────────────┐
          │   CONTRACT LAYER    │
          │ Behavior / Context  │
          │ ECD / Hypothesis    │
          │ Evidence / Validate │
          │ Outcome / Episode   │
          │ Learning / Promote  │
          └──────────┬──────────┘
                     │
                     ▼
              ┌──────────────┐
              │  FIKRACORE   │
              │ Correlation  │
              │ Reasoning    │
              │ Testing      │
              │ Convergence  │
              │ Knowledge    │
              └──────────────┘
```

The contracts define the **interfaces, admissibility rules, state transitions, and evidence requirements**. FikraCore performs the underlying correlation and reasoning.

## Operational Context

INFO/WARNING alarms continuously enrich the operational context.

```text
INFO/WARNING + Metrics/KPIs + Logs/Traces + Changes
+ Topology + Service Dependencies + Historical Knowledge
                         ↓
                OPERATIONAL CONTEXT
```

A single warning such as `UPF-03 CPU = 82%` is not sufficient to conclude root cause.

FikraCore should enrich it with entity identity, topology, domain, service, dependencies, temporal sequence, current metrics, active changes, historical patterns, and relevant evidence gaps.

## Emerging Condition Detection

ECD asks:

> **Is something developing in the network that could become an incident?**

ECD consumes current operational context, recent observations, temporal patterns, topology/dependencies, service-impact signals, and validated historical knowledge.

Example output:

```yaml
emerging_condition:
  id: ECD-001
  status: DETECTED
  condition: "progressive N3 degradation affecting UPF-03"
  indicators:
    - N3_PACKET_LOSS
    - PFCP_RETRANSMISSIONS
    - UPF_CPU_HIGH
  affected_entities:
    - Router-R21
    - UPF-03
  hypotheses:
    - "transport degradation"
    - "UPF resource pressure"
  missing_evidence:
    - "N3 interface health"
```

**ECD must not directly declare a root cause.** It produces a condition, evidence, hypotheses, and gaps.

## Hypothesis and Evidence

Hypotheses remain hypotheses until sufficient evidence and validation exist.

```text
H1  UPF resource exhaustion       0.71
H2  Transport degradation         0.64
H3  Infrastructure issue          0.31
```

Evidence continuously updates those hypotheses:

**SUPPORTING / CONTRADICTING / NEUTRAL / MISSING / UNTRUSTED**

The system should preserve provenance and avoid treating duplicate evidence as independent confirmation.

## Validation / Finding

Validation is where a candidate interpretation can become a validated operational finding.

```text
Leading hypothesis
        ↓
Additional evidence
        ↓
Domain validation
        ↓
VALIDATED FINDING
```

A severe alarm or highly degraded node must not automatically become the root cause.

Root cause / root condition is a **validated result of the hypothesis → evidence → validation process**, not a separate reasoning contract.

## Outcome

Record the actual outcome:

**PREVENTED / ESCALATED_TO_INCIDENT / FALSE_POSITIVE / UNRESOLVED / PARTIALLY_EXPLAINED**

This is essential for measuring whether Emerging Condition Detection provides operational value.

## Task Episode

The Task Episode is the common state thread connecting all contracts.

```yaml
task_episode:
  episode_id: EP-001
  task:
    mode: EMERGING_CONDITION
  operational_context:
    context_revision: 184
  emerging_condition:
    id: ECD-001
  hypotheses:
    - H1
    - H2
    - H3
  evidence:
    supporting: [...]
    contradicting: [...]
    missing: [...]
  validation:
    status: VALIDATED
    finding_id: FIND-004
  outcome:
    status: ESCALATED_TO_INCIDENT
  learning:
    status: CANDIDATE
  knowledge_promotion:
    status: PENDING
```

The Episode ID should persist as the condition evolves into an incident.

This lets FikraCore reconstruct:

> What did we observe? What did we believe? What evidence changed the belief? What did the engineer validate? What happened? What did we learn?

## Closed-loop learning

```text
             INFO/WARNING
                  │
                  ▼
        Emerging Condition
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
    PREVENTED            ESCALATED
        │                   │
        │             Investigation
        │                   │
        └─────────┬─────────┘
                  ▼
          VALIDATED OUTCOME
                  │
                  ▼
         LEARNING CANDIDATE
                  │
                  ▼
        KNOWLEDGE PROMOTION
                  │
                  ▼
         FIKRACORE KNOWLEDGE
                  │
                  └──────► improves future
                           detection and
                           investigation
```

### What gets learned

Do not simply learn:

> `CPU warning = root cause`

Instead learn the complete validated operational pattern:

**Early observations + operational context + temporal sequence + topology/dependencies + hypotheses considered + supporting evidence + contradicting evidence + missing evidence + engineer validation + action + actual outcome**

This is closer to how an experienced NOC engineer develops operational intuition.

## Knowledge promotion

Learning should not automatically become authoritative knowledge.

```text
Task Episode
    ↓
Learning Candidate
    ↓
Validation / quality checks
    ↓
Recurrence / generalization checks
    ↓
Knowledge Promotion
    ↓
FikraCore Operational Knowledge
```

Rejected or insufficient learning remains traceable as evidence; it should not silently become memory.

## Pre-incident + post-incident operating modes

FikraCore should be positioned as **one brain with two operating modes**:

```text
                    FIKRACORE
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ▼                           ▼
EMERGING CONDITION              INCIDENT
DETECTION                       INVESTIGATION
          │                           │
 "What's developing?"          "What happened?"
          │                           │
 INFO/WARNING signals           Incident evidence
          │                           │
          └─────────────┬─────────────┘
                        ▼
                 COMMON REASONING
                        │
              Hypotheses / Evidence /
              Validation / Outcome
                        │
                        ▼
                     LEARNING
```

Do **not** create separate prediction and RCA brains.

Reuse the same Correlation Layer, Reasoning Engine, Evidence model, Hypothesis model, Knowledge Gap handling, and operational knowledge.

## Key architectural principle

> **FikraCore uses a contract-driven, stateful reasoning loop in which each contract adds a stronger operational interpretation to the same Task Episode, culminating in validated learning that can be promoted back into FikraCore knowledge.**

The result is:

**Progressive + Traceable + Governed + Closed-Loop**

rather than ten independent AI modules.
