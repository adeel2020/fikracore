Exactly. **Zaki was implicit in the previous picture, but he should be explicit.** The cleanest conceptual placement is:

> **FikraCore = semantic authority**
> **Operational Context = runtime world Zaki is allowed to perceive**
> **Task Episode = cognitive work spine**
> **Zaki = cognitive operator / agent that perceives, reasons, communicates, delegates and acts within those contracts**
> **Contracts = boundaries and shared state between Zaki and the operational system**

So Zaki should **not** be drawn as another contract layer underneath OperationalContext. He is the **cognitive runtime that operates across the architecture**.

Here is the fuller architecture.

```text id="z8m4k2"
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                         F I K R A C O R E                                    ║
║                     SEMANTIC / OPERATIONAL TRUTH                             ║
║                                                                              ║
║  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐     ║
║  │   Entities  │  │ Relationships│  │   Topology   │  │    Services    │     ║
║  ├─────────────┤  ├──────────────┤  ├──────────────┤  ├────────────────┤     ║
║  │ Domains     │  │ Dependencies │  │ Procedures   │  │ Protocols      │     ║
║  │ Error Codes │  │ Patterns     │  │ Resilience   │  │ Network Rules  │     ║
║  │ Validated Operational Knowledge / Canonical Graph                   │     ║
║  └───────────────────────────────────────────────────────────────────-─┘     ║
║                                                                              ║
║       "What exists?"     "How is it related?"     "What is known?"           ║
║                                                                              ║
╚═══════════════════════════════╤══════════════════════════════════════════════╝
                                │
                                │ semantic resolution
                                │ topology / dependency / domain truth
                                ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                    OPERATIONAL CONTEXT CONTRACT                             ║
║                     "WHAT MATTERS RIGHT NOW?"                              ║
║                                                                            ║
║  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌─────────────┐ ║
║  │ CONTEXT        │ │ TEMPORAL       │ │ EXECUTION      │ │ AUTHORITY   │ ║
║  │ ID / Version   │ │ Time Window    │ │ Mode           │ │ Visibility  │ ║
║  │ Scenario       │ │ Current Time   │ │ Production     │ │ Scope       │ ║
║  │ Run            │ │ Recent Changes │ │ Simulation     │ │ Role        │ ║
║  └────────────────┘ └────────────────┘ └────────────────┘ └─────────────┘ ║
║                                                                            ║
║  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌─────────────┐ ║
║  │ CURRENT STATE  │ │ INCIDENTS      │ │ EVIDENCE       │ │ GAPS        │ ║
║  │ Health         │ │ Active         │ │ Alarms         │ │ Missing     │ ║
║  │ Degradation    │ │ Ownership      │ │ Metrics        │ │ Telemetry   │ ║
║  │ Services       │ │ Stage          │ │ Logs           │ │ Unknowns    │ ║
║  │ Capacity       │ │ Impact         │ │ KPIs           │ │ Ambiguity   │ ║
║  └────────────────┘ └────────────────┘ └────────────────┘ └─────────────┘ ║
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │ Authorized operational snapshot / context envelope                  │  ║
║  └──────────────────────────────────────────────────────────────────────┘  ║
╚══════════════════════════════════╤═════════════════════════════════════════╝
                                   │
                                   │ context presented to Zaki
                                   ▼
                    ╔═══════════════════════════════╗
                    ║                               ║
                    ║             Z A K I           ║
                    ║                               ║
                    ║       COGNITIVE NOC AGENT     ║
                    ║                               ║
                    ╚═══════════════════════════════╝
                                   │
             ┌─────────────────────┼────────────────────────┐
             │                     │                        │
             ▼                     ▼                        ▼
      ┌───────────────┐    ┌────────────────┐      ┌────────────────┐
      │ PERCEPTION    │    │   COGNITION    │      │ INTERACTION    │
      │               │    │                │      │                │
      │ ingest        │    │ reason         │      │ explain        │
      │ observe       │    │ correlate      │      │ answer         │
      │ filter        │    │ hypothesize    │      │ storyteller    │
      │ contextualize │    │ validate       │      │ voice          │
      │ detect        │    │ assess impact  │      │ prosody        │
      └───────────────┘    └────────────────┘      └────────────────┘
             │                     │                        │
             └─────────────────────┼────────────────────────┘
                                   │
                                   ▼
                    ╔══════════════════════════════╗
                    ║       TASK EPISODE           ║
                    ║                              ║
                    ║        COGNITIVE SPINE       ║
                    ║                              ║
                    ║ "WHAT IS ZAKI DOING ABOUT    ║
                    ║       THE SITUATION?"        ║
                    ╚══════════════════════════════╝
                                   │
          ┌────────────────────────┼─────────────────────────┐
          │                        │                         │
          ▼                        ▼                         ▼
 ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
 │    REASONING    │      │    DELEGATION   │      │      HITL       │
 │                 │      │                 │      │                 │
 │ Intent          │      │ Specialist      │      │ Human SME       │
 │ Observations    │      │ Domain Agent    │      │ Authority       │
 │ Evidence Set    │      │ Task Scope      │      │ Validation      │
 │ Hypotheses      │      │ Findings        │      │ Correction      │
 │ RCA             │      │ Return Evidence │      │ Approval        │
 │ Causal Chain    │      │ Correlation     │      │ Escalation      │
 │ Validation      │      │                 │      │ Override        │
 └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │      DECISION      │
                         │                    │
                         │ What is believed?  │
                         │ What is proven?    │
                         │ What remains open? │
                         │ What should happen?│
                         └─────────┬──────────┘
                                   │
                                   ▼
                    ╔══════════════════════════════╗
                    ║       ACTION BOUNDARY        ║
                    ╚══════════════════════════════╝
                                   │
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
      ┌──────────────┐      ┌──────────────┐      ┌───────────────┐
      │ REMEDIATION  │      │    WHAT-IF   │      │   EXECUTION   │
      │ Strategy     │      │ Simulation   │      │ Action        │
      │ Risk         │      │ Counterfactual│     │ Probe         │
      │ Rollback     │      │ Capacity     │      │ Change        │
      └──────────────┘      └──────────────┘      └───────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │      OUTCOME       │
                         │                    │
                         │ Action result      │
                         │ Hypothesis result  │
                         │ Recovery state     │
                         │ Service impact     │
                         │ Residual risk      │
                         │ Human assessment   │
                         └─────────┬──────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                            LEARNING                                         ║
║                                                                            ║
║  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────┐  ║
║  │ EPISODIC       │ │ SEMANTIC       │ │ PROCEDURAL     │ │ PATTERNS   │  ║
║  │ Memory         │ │ Memory         │ │ Memory         │ │            │  ║
║  │ What happened  │ │ What is known  │ │ How to do it   │ │ Recurrence │  ║
║  │ Incident       │ │ Relationships  │ │ Workflow       │ │ Signatures │  ║
║  │ Episode        │ │ Facts          │ │ Skill          │ │ Correlation│  ║
║  └────────────────┘ └────────────────┘ └────────────────┘ └────────────┘  ║
║                                                                            ║
║                    VALIDATION → PROMOTION → KNOWLEDGE                      ║
╚══════════════════════════════════════╤═══════════════════════════════════════╝
                                       │
                                       │ validated knowledge
                                       ▼
                              ┌────────────────────┐
                              │    FIKRACORE       │
                              │                    │
                              │ semantic truth     │
                              │ updated knowledge  │
                              │ validated pattern  │
                              │ operational memory │
                              └────────────────────┘
```

## Now add the contract architecture around Zaki

The above is the **runtime cognitive flow**. The contracts form the boundaries around it:

```text id="3g7v1q"
                           FIKRACORE
                      Semantic Authority
                             │
                             ▼
              ┌──────────────────────────────┐
              │ OperationalContextContract  │
              │                              │
              │ Context Identity             │
              │ Scope                        │
              │ Temporal                     │
              │ Mode                         │
              │ Authorization                │
              │ Current State                │
              └──────────────┬───────────────┘
                             │
                             ▼
                            ZAKI
                    Cognitive NOC Runtime
                             │
          ┌──────────────────┼────────────────────┐
          │                  │                    │
          ▼                  ▼                    ▼
     PERCEPTION          COGNITION           INTERACTION
          │                  │                    │
          │                  ▼                    │
          │          TaskEpisodeContract          │
          │                  │                    │
          │       ┌──────────┼───────────┐        │
          │       ▼          ▼           ▼        │
          │   Reasoning  Delegation     HITL      │
          │       │          │           │        │
          └───────┼──────────┼───────────┼────────┘
                  │          │           │
                  ▼          ▼           ▼
             Evidence     Domain      Human
             Contracts     Agents     Contracts
                  │          │           │
                  └──────────┼───────────┘
                             │
                             ▼
                         OUTCOME
                             │
                             ▼
                         LEARNING
                             │
                             ▼
                    Validated Knowledge
                             │
                             ▼
                         FikraCore
```

### The incident branch expands like this

```text id="8v2p6r"
OperationalContext
       │
       ▼
IncidentContextContract
       │
       ├── references → IncidentContract
       │
       ├── Investigation State
       │
       ├── Active Evidence Window
       │
       ├── Diagnostic Gaps
       │
       ├── Service Impact
       │
       ├── Blast Radius
       │
       ├── Hypothesis Ranking
       │       │
       │       ├── Root Cause Analysis
       │       └── Causal Propagation
       │
       ├── Recovery State
       │       │
       │       ├── Remediation Strategy
       │       └── What-If Simulation
       │
       └── Task Episodes
               │
               ├── Episode 1: Detection
               ├── Episode 2: Correlation
               ├── Episode 3: RCA
               ├── Episode 4: Validation
               ├── Episode 5: Remediation
               └── Episode 6: Recovery Verification
```

This gives an important distinction:

```text
IncidentContract
       │
       │ "What incident exists?"
       ▼
INC-042
       │
       ├── identity
       ├── lifecycle
       ├── status
       ├── timestamps
       └── durable incident state

IncidentContextContract
       │
       │ "What do we currently understand
       │  about INC-042?"
       ▼
       ├── current investigation stage
       ├── current evidence
       ├── current hypotheses
       ├── current impact
       ├── current gaps
       └── current authority

TaskEpisodeContract
       │
       │ "What did Zaki / humans / agents
       │  do about INC-042?"
       ▼
       ├── intent
       ├── observations
       ├── reasoning
       ├── delegation
       ├── validation
       ├── action
       ├── outcome
       └── learning
```

## And Zaki's internal architecture

This is the part I would make explicit in your overall system design:

```text
                         ┌───────────────────────┐
                         │         ZAKI          │
                         │   Cognitive NOC SME   │
                         └───────────┬───────────┘
                                     │
       ┌─────────────────────────────┼─────────────────────────────┐
       │                             │                             │
       ▼                             ▼                             ▼
┌───────────────┐            ┌────────────────┐            ┌────────────────┐
│ CONTEXT       │            │ COGNITIVE      │            │ COMMUNICATION  │
│ PROCESSOR     │            │ ENGINE         │            │ ENGINE         │
│               │            │                │            │                │
│ context       │            │ correlation    │            │ answer         │
│ resolution    │            │ reasoning      │            │ storytelling   │
│ relevance     │            │ hypothesis     │            │ voice          │
│ temporal      │            │ RCA            │            │ prosody        │
│ state         │            │ validation     │            │ explanation    │
└───────┬───────┘            └───────┬────────┘            └───────┬────────┘
        │                            │                             │
        └────────────────────────────┼─────────────────────────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │   TASK ORCHESTRATOR  │
                         │                      │
                         │ episode management   │
                         │ stage progression    │
                         │ delegation           │
                         │ HITL gates            │
                         │ outcome capture      │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
        Domain Agents         Tool / MCP Layer       Human SME
              │                     │                     │
              ▼                     ▼                     ▼
       CS / PS / VAS /        OSS / telemetry /      Validation /
       RAN / IP / etc.        external systems        approval
```

### Cross-cutting contracts surround this runtime

They should **not be interpreted as a sequential pipeline**:

```text
                  ┌─────────────────────────────────────┐
                  │         ZAKI BEHAVIORAL             │
                  │                                     │
                  │ reasoning behavior                   │
                  │ evidence behavior                    │
                  │ uncertainty behavior                 │
                  │ escalation behavior                  │
                  └─────────────────────────────────────┘

      ┌─────────────────────────────────────────────────────────┐
      │                    GOVERNANCE FABRIC                     │
      │                                                         │
      │ Authority • Approval • Ownership • Provenance           │
      │ Security • Authorization • Audit • Policy               │
      └─────────────────────────────────────────────────────────┘

      ┌─────────────────────────────────────────────────────────┐
      │                    PROSODY FABRIC                       │
      │                                                         │
      │ Pacing • Stage Barriers • Interruption • Voice         │
      │ Presentation • Response Timing                          │
      └─────────────────────────────────────────────────────────┘

      ┌─────────────────────────────────────────────────────────┐
      │                    MCP CONNECTIVITY                     │
      │                                                         │
      │ Tools • Resources • External Context • Authorization   │
      └─────────────────────────────────────────────────────────┘

                              ↓
                           ZAKI
```

## The deepest conceptual model

I would summarize the entire FikraCore + Zaki architecture with **six layers of meaning**:

```text
┌──────────────────────────────────────────────────────────────┐
│  1. SEMANTIC TRUTH                                           │
│     FikraCore                                                │
│     "What exists and what is known?"                         │
├──────────────────────────────────────────────────────────────┤
│  2. OPERATIONAL REALITY                                      │
│     OperationalContext                                       │
│     "What is relevant right now?"                            │
├──────────────────────────────────────────────────────────────┤
│  3. COGNITIVE ACTOR                                          │
│     Zaki                                                     │
│     "How do we understand and work this situation?"          │
├──────────────────────────────────────────────────────────────┤
│  4. COGNITIVE EXPERIENCE                                     │
│     TaskEpisode                                              │
│     "What did we observe, reason, validate and do?"          │
├──────────────────────────────────────────────────────────────┤
│  5. OPERATIONAL CONSEQUENCE                                  │
│     Outcome                                                  │
│     "What actually happened?"                                │
├──────────────────────────────────────────────────────────────┤
│  6. ORGANIZATIONAL LEARNING                                  │
│     Memory → Validation → FikraCore                          │
│     "What should Zaki and the system know next time?"        │
└──────────────────────────────────────────────────────────────┘
```

So **Zaki is not merely sitting between OperationalContext and TaskEpisode**.

More accurately:

> **OperationalContext is the world presented to Zaki. Zaki is the cognitive actor operating within that world. TaskEpisode is the persistent spine recording Zaki's cognitive work. FikraCore is the semantic authority that grounds Zaki's understanding. Outcome tells the system what actually happened, and Learning feeds validated knowledge back into FikraCore.**

That makes the architecture much closer to a **cognitive NOC operating system** than a collection of independent contracts.
