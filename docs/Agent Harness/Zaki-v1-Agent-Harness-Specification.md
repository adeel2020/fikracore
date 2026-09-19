# Zaki v1 Agent Harness Specification

**Project:** FikraCore / Dark NOC  
**Document:** Zaki v1 Agent Harness Specification & Implementation Plan  
**Status:** Proposed implementation baseline  
**Date:** 2026-09-19  
**Scope:** Telecom operator Dark NOC, built around the existing FikraCore execution flow

---

## 0. Executive Intent

Zaki v1 is the **Dark NOC Agent Harness** around the existing FikraCore investigation backend.

The purpose of v1 is **not** to replace, duplicate or redesign FikraCore reasoning. The current FikraCore execution method remains the authoritative operational reasoning flow. Zaki adds the operator-facing and agent-runtime capabilities needed to execute that flow safely across telecom domains, tools, engineers, shifts and future autonomous workflows.

The implementation must therefore follow this principle:

> **FikraCore reasons. Domain Agents operate. Zaki orchestrates, governs and explains.**

The current backend plan already defines a modular Correlation Engine, Hypothesis & Reasoning Engine, convergence, domain attribution, next-best evidence, operator validation and knowledge promotion. Zaki v1 shall call these capabilities rather than recreate them.

This specification is intentionally staged. The current backend is partially implemented for experimentation and benchmarking. **Full implementation of the broader Zaki harness is gated by successful FikraCore benchmarks and regression results.**

---

# 1. Source-of-Truth Architecture

## 1.1 Existing FikraCore execution flow

The existing implementation plan defines the investigation flow as:

```text
Stage 1  TELEMETRY INGESTION
   ↓
Stage 2  CORRELATION ENGINE
   ├─ 2.1 Temporal & Identity Correlation
   ├─ 2.2 Topological Correlation
   ├─ 2.3 Cross-Domain Pathway Correlation
   └─ 2.4 Service & Blast Radius Correlation
   ↓
Stage 3  HYPOTHESIS GENERATION
   ↓
Stage 4  HYPOTHESIS TESTING
   ↓
Stage 5  CONVERGENCE & KNOWLEDGE GAP DETECTION
   ↓
Stage 6  DOMAIN ATTRIBUTION & AFFECTED SERVICES
   ↓
Stage 7  NEXT-BEST EVIDENCE & OPERATOR VALIDATION
   ↓
Stage 8  KNOWLEDGE GRAPH PROMOTION
```

This is the **Zaki v1 execution contract** for incident investigation. fileciteturn45file0L126-L154

## 1.2 Existing Correlation model

The current backend explicitly treats Correlation as the overarching engine with four dimensions:

1. Temporal & Identity
2. Topological
3. Cross-Domain Pathway
4. Service & Blast Radius

The Cross-Domain Pathway layer currently contains nine analytical funnels/lenses:

- Operational Evidence
- Service Dependency
- Subscriber Journey
- Change & Configuration
- Traffic & Capacity
- Control & Signaling
- Resilience & Failover
- Historical Pattern
- Knowledge Gap

Zaki must expose these as FikraCore capabilities/findings, not reimplement them. fileciteturn45file0L10-L22

## 1.3 Hypothesis language

Zaki v1 shall use **Ranked Hypotheses** / **Hypothesis Ranking**.

Do **not** use the product language:

Preferred operator language:

- Ranked Hypotheses
- Hypothesis Ranking
- Current Leading Hypothesis
- Competing Hypotheses
- Hypothesis Score
- Supporting Evidence
- Contradicting Evidence
- Missing Evidence
- Hypothesis Convergence
- Hypothesis Falsification

A hypothesis is always a hypothesis until the required validation state is reached.

Example:

```text
RANKED HYPOTHESES

#1  IP Transport Router-R21     0.82   LEADING
#2  PS / UPF                    0.61   COMPETING
#3  RAN                         0.38   COMPETING
#4  Infrastructure             0.21   WEAK
#5  Change                     0.12   WEAK
```

The number of hypotheses is dynamic. The harness must never assume a fixed count.

---

# 2. Zaki v1 Mission in the Dark NOC

Zaki provides the runtime fabric connecting:

```text
Operator Intent
      ↓
Task / Incident Context
      ↓
Agent Capability Selection
      ↓
Controlled Tool Access
      ↓
FikraCore Investigation
      ↓
Domain-Agent Collaboration
      ↓
Evidence / Validation Loop
      ↓
Action Governance
      ↓
Outcome Verification
      ↓
Incident Story
      ↓
Task Episode / Learning Signal
```

Zaki is responsible for:

- translating operator intent into structured tasks;
- maintaining session and incident context;
- selecting domain-agent capabilities;
- invoking FikraCore capabilities;
- controlling tool access;
- maintaining provenance and auditability;
- requesting or coordinating human validation;
- managing delegation and handover;
- presenting ranked hypotheses and execution progress;
- explaining FikraCore findings through the Storyteller;
- recording the completed task as a structured episode;
- enforcing separation between operational knowledge and evaluator truth.

Zaki is **not** responsible for independently determining telecom root cause.

---

# 3. Target Zaki v1 Architecture

```text
                           DARK NOC
                              │
                  Voice / Chat / Operations UI
                              │
                       ┌──────▼──────┐
                       │    ZAKI     │
                       │ Agent       │
                       │ Harness     │
                       └──────┬──────┘
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
┌─────────────┐        ┌──────────────┐       ┌──────────────┐
│ Intent &    │        │ Agent        │       │ Policy /     │
│ Task        │        │ Registry &   │       │ Governance   │
│ Manager     │        │ Capability   │       │ / HITL       │
└──────┬──────┘        └──────┬───────┘       └──────┬───────┘
       │                       │                      │
       └───────────────────────┼──────────────────────┘
                               ▼
                    ┌────────────────────┐
                    │ Agent Orchestrator │
                    │ / Execution Loop   │
                    └─────────┬──────────┘
                              │
       ┌──────────────────────┼─────────────────────────────┐
       │                      │                             │
       ▼                      ▼                             ▼
┌───────────────┐     ┌─────────────────┐        ┌───────────────────┐
│ Domain Agents │     │ FikraCore       │        │ Tool / API Gateway│
│               │     │ Telecom Brain   │        │                   │
│ PS            │     │                 │        │ TMF Open APIs     │
│ CS            │     │ Correlation     │        │ MCP               │
│ RAN           │     │ Layer           │        │ NMS / EMS         │
│ IP Transport  │     │ Reasoning       │        │ ITSM              │
│ IN / OCS      │     │ Engine          │        │ CMDB              │
│ VAS / IGW     │     │ Knowledge       │        │ LGTM              │
│ Infra / IT    │     │ Learning        │        │ Network tools     │
└──────┬────────┘     └───────┬─────────┘        └─────────┬─────────┘
       │                      │                            │
       └──────────────────────┼────────────────────────────┘
                              ▼
                ┌─────────────────────────────┐
                │ Telecom Operational Estate  │
                │ Network / OSS / BSS / Data  │
                └─────────────────────────────┘

              GOVERNANCE / AUDIT / MEMORY / EVALUATION
```

---

# 4. Architectural Boundaries

## 4.1 Zaki vs FikraCore

| Concern | Zaki | FikraCore |
|---|---|---|
| Operator interaction | Yes | No |
| Voice interface | Yes | No |
| Intent capture | Yes | No |
| Session/task context | Yes | No |
| Agent routing | Yes | No |
| Tool authorization | Yes | No |
| Policy enforcement | Yes | No |
| Incident execution state | Coordinates | Produces investigation state |
| Evidence collection orchestration | Yes | Consumes/evaluates evidence |
| Correlation algorithm | No | Yes |
| Hypothesis generation | No | Yes |
| Hypothesis testing | No | Yes |
| Hypothesis ranking | No | Yes |
| Convergence | No | Yes |
| Knowledge-gap detection | No | Yes |
| Domain attribution | No | Yes |
| Knowledge promotion | Requests/governs | Executes promotion logic |
| Incident storytelling | Presents/orchestrates | Supplies authoritative findings |
| Learning governance | Coordinates | Supplies validated knowledge/learning interfaces |

The existing backend explicitly decomposes investigation logic into EvidenceNormalizer, CausalDiGraphBuilder, CorrelationFunnelsEngine, BlastRadiusAnalyzer, HypothesisGenerator, SynthesisCoreAssessor, ConvergenceRanker and GapAndResidualDetector. Zaki should call these through stable application contracts instead of duplicating the classes. fileciteturn45file0L111-L122

## 4.2 Zaki vs Domain Agents

Zaki does not become a centralized FM worker.

The harness supports persistent domain-agent capabilities:

```text
CS Engineer        ↔ CS Agent
PS Engineer        ↔ PS Agent
RAN Engineer       ↔ RAN Agent
IP Transport Eng.  ↔ Transport Agent
IN/OCS Engineer    ↔ IN/OCS Agent
VAS Engineer       ↔ VAS Agent
IGW Engineer       ↔ IGW Agent
Infra Engineer     ↔ Infra Agent
IT Engineer        ↔ IT Agent
```

A single domain-agent capability may support multiple concurrent sessions.

The domain agent is the domain-specific operational assistant. Zaki is the runtime that discovers, authorizes, invokes and coordinates that capability.

---

# 5. TM Forum Alignment Strategy

Zaki v1 should be described as **TM Forum-aligned**, not as a claim of formal TM Forum certification.

The target alignment is to the current AI-Native ODA direction and associated TM Forum assets.

TM Forum's AI-Native ODA roadmap describes a component-based architecture, common telecom language including SID/eTOM/Intent Ontology, standardized Open APIs, MCP support, secure agent interaction, guardrails, managed agent access to data/products/models, lifecycle management and autonomous cross-domain flows. citeturn437779search1turn437779search2

TM Forum's AI-native ODA Canvas is specifically intended to provide the runtime environment for both ODA Components and AI agents, including identity/access, observability, automation, agent orchestration, data access, guardrails and external-system integration. citeturn437779search0

### Zaki alignment map

| Zaki v1 area | TM Forum target |
|---|---|
| Agent Manifest | ODA Component principles / machine-readable component model |
| Agent Registry | Composable ODA Components / component directory concepts |
| Agent Runtime | AI-Native ODA Canvas |
| Agent Lifecycle | AI-Native ODA lifecycle capabilities |
| Intent Manager | TM Forum Intent Ontology |
| Telecom semantics | SID / Information Framework |
| Operational processes | eTOM / Business Process Framework |
| API Gateway | TM Forum Open APIs |
| Event Gateway | TMF event-driven API patterns / event-driven ODA |
| MCP Gateway | AI-Native ODA MCP integration |
| Policy / IAM | AI-Native ODA governance and control |
| Data/Product access | Managed agent access to data products |
| Observability | ODA Canvas observability capabilities |
| Human governance | Guardrails / human control points |
| Cross-domain orchestration | AI-Native ODA autonomous flow direction |

TM Forum currently lists ODA Components as reusable cloud-native software building blocks exposing functionality through Open APIs and running on an ODA Canvas. citeturn972107search1

TM Forum's current Open API program emphasizes interoperability, portability, a shared API data model based on SID, and API lifecycle governance. citeturn972107search0

The current production eTOM release is v26.0 and the current production SID release is v26.0. citeturn661503search0turn661503search6

TM Forum's intent toolkit currently lists TIO references v3.6.0 and Intent Specification v3.6.0. citeturn661503search11

---

# 6. Zaki v1 Core Components

## 6.1 Intent Manager

Purpose:

```text
Natural Language / Voice
        ↓
Structured Operator Intent
        ↓
Task Creation
```

Example:

```json
{
  "intent_id": "INT-20260919-0001",
  "intent_type": "INVESTIGATE_SERVICE_DEGRADATION",
  "subject": {
    "service": "Mobile Data"
  },
  "scope": {
    "region": "Region-1"
  },
  "objective": "identify probable causal driver",
  "requested_by": "operator-123",
  "risk_mode": "ANALYZE_ONLY"
}
```

The Intent Manager should preserve the original operator statement and the normalized representation.

## 6.2 Task Manager

Creates a durable operational task around an intent.

```yaml
task_id: TASK-001
incident_id: INC-001
intent_id: INT-001
task_type: INVESTIGATION
status: ACTIVE
priority: HIGH
owner: NOC_SHIFT_B
created_at:
updated_at:
current_stage: HYPOTHESIS_TESTING
```

## 6.3 Incident Context Manager

Maintains:

- incident identity;
- current FikraCore run identifier;
- active evidence window;
- ranked hypotheses;
- evidence requests;
- domain involvement;
- pending validation;
- task ownership;
- current action authority;
- recovery state;
- learning state;
- provenance references.

The UI must consume this state rather than independently reconstructing it.

## 6.4 Agent Registry

The registry stores discoverable agent capabilities.

Required fields:

```yaml
agent_id:
name:
version:
domain:
ownership:
capabilities:
accepted_intents:
skills:
tools:
input_contracts:
output_contracts:
policy_profile:
risk_level:
knowledge_version:
skill_version:
health:
lifecycle_state:
certification_state:
```

## 6.5 Capability Registry

Separate **agent identity** from **capability identity**.

Example:

```text
PS Agent
   ├── pdu-session-investigation
   ├── upf-health-analysis
   ├── pfcp-analysis
   └── ps-change-analysis
```

This lets Zaki request a capability rather than hard-coding a specific agent implementation.

## 6.6 Orchestrator

The orchestrator executes a deterministic stateful loop around FikraCore and domain-agent contracts.

It must:

1. accept an intent/task;
2. resolve the incident context;
3. discover required capabilities;
4. authorize tools;
5. invoke FikraCore investigation;
6. evaluate returned execution state;
7. delegate domain work when needed;
8. collect returned evidence/findings;
9. feed new evidence back into the FikraCore loop;
10. request human validation when policy requires it;
11. propose or execute authorized action;
12. verify outcome;
13. close/update the task;
14. emit story and learning records.

The orchestrator must never calculate telecom RCA independently of FikraCore.

---

# 7. FikraCore Adapter Contract

Zaki should interact with FikraCore through a stable adapter boundary.

Suggested v1 capability interface:

```text
fikracore.start_investigation()
fikracore.get_state()
fikracore.get_correlation()
fikracore.get_ranked_hypotheses()
fikracore.test_hypothesis()
fikracore.get_convergence()
fikracore.get_knowledge_gaps()
fikracore.get_domain_attribution()
fikracore.get_affected_services()
fikracore.get_next_best_evidence()
fikracore.submit_validation()
fikracore.propose_knowledge_promotion()
fikracore.promote_validated_knowledge()
fikracore.rollback_promotion()
```

The exact implementation can initially wrap the existing Python/CLI functions and later move behind REST/event interfaces.

### Mandatory adapter property

The adapter must preserve the existing execution trace and IDs.

At minimum:

```yaml
run_id:
simulation_id:
scenario_id:
incident_id:
task_id:
revision:
sequence:
current_stage:
terminal_state:
```

Zaki must not create a second competing reasoning state machine.

---

# 8. Operational Evidence Gateway

The gateway provides controlled access to operational evidence.

```text
Network / OSS / NMS
       │
       ▼
     Kafka
       │
       ▼
Normalization / Enrichment
       │
       ▼
   Grafana LGTM
       │
       ├── Loki  → Logs
       ├── Mimir → Metrics / KPIs
       └── Tempo → Traces
       │
       ├── Alarm Manager
       ├── ITSM / Trouble Tickets
       ├── Change Management
       ├── CMDB / Inventory
       ├── Topology
       ├── Customer Impact
       └── Domain NMS / EMS
       │
       ▼
      Zaki Tool Gateway
       │
       ▼
    FikraCore / Domain Agents
```

The simulator master plan already defines operational observability this way and explicitly permits incomplete, delayed, noisy, contradictory or incorrect evidence. The production harness must retain the same discipline. 

### Evidence provenance

Every material observation returned to Zaki must have:

```yaml
evidence_id:
source:
source_type:
event_time:
ingestion_time:
domain:
entity:
service:
region:
observation:
provenance:
quality:
status:
```

Evidence status should support:

```text
SUPPORTING
CONTRADICTING
NEUTRAL
MISSING
UNTRUSTED
```

---

# 9. Domain-Agent Contract

Each domain agent must expose a common contract.

## 9.1 Agent request

```yaml
agent_task:
  task_id:
  incident_id:
  parent_task_id:
  intent:
  domain:
  objective:
  context:
  constraints:
  evidence:
  requested_capability:
  authority:
  deadline:
```

## 9.2 Agent response

```yaml
agent_result:
  task_id:
  agent_id:
  status:
  observations:
  findings:
  evidence_requests:
  recommendations:
  delegation_requests:
  human_validation_required:
  confidence:
  provenance:
  next_step:
```

### Rule

A domain-agent response is evidence or domain analysis. It does not automatically become authoritative FikraCore knowledge.

---

# 10. Investigation Runtime in Zaki

The harness should expose the current FikraCore execution visibly as one continuous investigation.

```text
             DARK NOC INVESTIGATION
                     │
                     ▼
            ┌──────────────────┐
            │ 1 TELEMETRY     │
            │    INGESTION     │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 2 CORRELATION   │
            │                  │
            │ Temporal         │
            │ Topological      │
            │ Cross-Domain     │
            │ Service/Impact   │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 3 HYPOTHESES    │
            │    GENERATION    │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 4 HYPOTHESIS    │
            │    TESTING       │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 5 CONVERGENCE   │
            │  + KNOWLEDGE GAP │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 6 ATTRIBUTION   │
            │  + IMPACT        │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 7 EVIDENCE      │
            │  + VALIDATION    │
            └────────┬─────────┘
                     ▼
            ┌──────────────────┐
            │ 8 KNOWLEDGE     │
            │    PROMOTION     │
            └──────────────────┘
```

The existing implementation explicitly supports optional deep inspection of the synthesized correlation vector and 12-factor synthesis mathematics while allowing the operator to proceed through summary output. Zaki should preserve this pattern as a **presentation depth control**, not a different reasoning path. fileciteturn45file0L239-L337

Suggested Zaki UI modes:

```text
EXECUTIVE
  high-level investigation story

OPERATOR
  evidence + ranked hypotheses + actions

DEEP TECHNICAL
  correlation vectors + mathematical details + provenance
```

All three views must project the same backend run state.

---

# 11. Ranked Hypothesis Experience

The central Dark NOC reasoning view should be a **Ranked Hypothesis Board**.

```text
┌──────────────────────────────────────────────────────────┐
│ RANKED HYPOTHESES                                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ #1  IP Transport — Router-R21         0.82  LEADING      │
│     + temporal precedence                              │
│     + upstream topology                                 │
│     + service coverage                                  │
│     + independent telemetry                             │
│     - no physical-link-down signal                      │
│                                                          │
│ #2  Mobile Core — UPF                  0.61  COMPETING    │
│     + downstream symptoms                               │
│     - healthy PFCP                                      │
│     - normal resource telemetry                         │
│                                                          │
│ #3  RAN                                0.38  COMPETING    │
│     + RAN alarms                                        │
│     - RF indicators healthy                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Operator actions

```text
[TEST] [REQUEST EVIDENCE] [ASK DOMAIN AGENT] [VIEW BASIS]
```

The board should show how evidence changes ranking over time.

Example:

```text
Evidence received
      ↓
Hypothesis score update
      ↓
Rank movement
      ↓
Falsified / retained
      ↓
Next-best evidence
```

### Required rank telemetry

Store:

```yaml
hypothesis_id:
rank:
score:
score_components:
rank_delta:
state:
role:
supporting_evidence:
contradicting_evidence:
missing_evidence:
provenance:
```

This enables benchmark metrics such as:

- correct hypothesis rank;
- rank convergence speed;
- false-leading rate;
- hypothesis elimination rate;
- rank movement after evidence;
- wrong-high-confidence rate;
- evidence efficiency.

---

# 12. Correlation Layer Exposure in Zaki

Zaki should show **one Correlation Layer** with selectable dimensions.

```text
CORRELATION LAYER

● Temporal & Identity
● Topological
● Cross-Domain Pathway
● Service & Blast Radius
```

Inside Cross-Domain Pathway:

```text
Operational Evidence
Service Dependency
Subscriber Journey
Change & Configuration
Traffic & Capacity
Control & Signaling
Resilience & Failover
Historical Pattern
Knowledge Gap
```

A dimension should be selected from the UI but must use shared backend state and common evidence.

The existing implementation plan explicitly defines these four Correlation phases and nine cross-domain analytical funnels. fileciteturn45file0L10-L15 fileciteturn45file0L206-L235

### Dimension detail contract

Use the standard operator presentation model:

```text
RECEIVED
    ↓
CHECKS PERFORMED
    ↓
FOUND
    ↓
WHY IT MATTERS
    ↓
FORWARDED TO REASONING ENGINE
```

Technical implementation fields remain behind a technical-details view.

---

# 13. Knowledge Gap / Discovery Mode

Knowledge gaps are first-class operational outcomes.

When FikraCore cannot explain observed propagation:

```text
Known Path
    ↓
Unexplained Residual
    ↓
KNOWLEDGE GAP
    ↓
Candidate Relationship / Evidence Request
    ↓
Domain Agent / Operator
    ↓
Human Validation
    ↓
Candidate Knowledge
```

Zaki must never silently fabricate the missing relationship.

Example UI:

```text
KNOWLEDGE GAP DETECTED

Known:
UPF-03 → Router-R21 → ? → DC-GW2

Missing:
Transport path between Router-R21 and DC-GW2

Next-best evidence:
1. Routing table
2. MPLS/LSP state
3. Path trace
4. Inventory lookup

[REQUEST EVIDENCE]
[ASK TRANSPORT AGENT]
```

The master plan explicitly requires detection of unexplained propagation, candidate relationship inference, discriminating evidence and human validation. 

---

# 14. Human-in-the-Loop Governance

HITL is part of the harness, not an afterthought.

## 14.1 Validation actions

```text
CONFIRM
REJECT
MODIFY
REQUEST MORE EVIDENCE
MARK ROOT CAUSE
MARK TRIGGER
MARK SYMPTOM
VALIDATE RELATIONSHIP
APPROVE LEARNING
```

## 14.2 Action authority levels

```text
LEVEL 0  OBSERVE
         Read-only investigation

LEVEL 1  ANALYZE
         Agent analysis / evidence requests

LEVEL 2  RECOMMEND
         Remediation recommendation

LEVEL 3  PLAN
         Create change/action plan

LEVEL 4  EXECUTE WITH HITL
         Explicit human approval

LEVEL 5  CONDITIONAL AUTO-EXECUTE
         Only for certified low-risk actions
```

v1 should stop at **Level 4** for production-impacting actions unless a later certification programme explicitly enables Level 5.

---

# 15. Policy & Guardrail Engine

Every tool invocation must pass through policy evaluation.

```yaml
policy_decision:
  actor:
  agent_id:
  capability:
  tool:
  resource:
  requested_action:
  data_classification:
  risk_level:
  authority_level:
  approval_required:
  decision:
  reason:
  policy_version:
```

Policy decisions:

```text
ALLOW
ALLOW_WITH_HITL
DENY
ESCALATE
```

The harness must enforce least privilege.

Example:

```text
PS Agent
 ├─ read topology           ALLOW
 ├─ read metrics            ALLOW
 ├─ analyze trace           ALLOW
 ├─ request evidence        ALLOW
 ├─ recommend restart       ALLOW_WITH_HITL
 ├─ execute restart         DENY / HITL
 └─ modify FikraCore        DENY / Promotion Workflow Only
```

This is aligned with the current AI-Native ODA direction of secure agent interactions, centralized policy control and guardrails. citeturn437779search0turn437779search1

---

# 16. Tool Gateway

Zaki should not expose raw infrastructure credentials to agents.

Use:

```text
Agent
  ↓
Capability
  ↓
Tool Gateway
  ↓
Policy Check
  ↓
API / MCP Adapter
  ↓
Operational System
```

## Tool classes

### Read tools

```text
alarm.query
metric.query
log.query
trace.query
kpi.query
topology.query
inventory.query
change.query
ticket.query
routing.query
service-impact.query
```

### Analysis tools

```text
trace.analyze
path.analyze
kpi.analyze
protocol.analyze
customer-journey.analyze
```

### FikraCore tools

```text
fikracore.correlate
fikracore.rank_hypotheses
fikracore.test_hypothesis
fikracore.detect_gap
fikracore.get_blast_radius
fikracore.get_attribution
```

### Action tools

```text
change.create
change.approve
network.action
service.restart
traffic.reroute
```

Action tools must be governed separately from read/analysis tools.

---

# 17. MCP Strategy

MCP should be used as an interoperability mechanism where useful, not as a replacement for TM Forum Open APIs.

Recommended:

```text
                        ZAKI
                         │
                  Tool / API Gateway
                         │
              ┌──────────┴───────────┐
              │                      │
         TMF Open APIs             MCP
              │                      │
        standardized           agent/tool access
        telco interface        and dynamic tools
              │                      │
              └──────────┬───────────┘
                         ▼
                 Operational Systems
```

TM Forum's AI-Native ODA roadmap explicitly identifies MCP support in ODA Components and the ODA Canvas, while Open APIs remain the standardized interoperability layer. citeturn437779search1turn972107search0

For existing FikraCore knowledge promotion, retain the current MCP-based Smart Delta Link Upsert contract and rollback journal rather than creating a parallel knowledge store. The current backend plan already defines this promotion path. fileciteturn45file0L383-L410

---

# 18. Memory Architecture

Zaki v1 should separate four memory types.

```text
┌─────────────────────────────────────┐
│ Episodic Memory                     │
│ What happened in a task/incident    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Workflow Memory                     │
│ How engineers perform workflows     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Semantic Memory                     │
│ Validated FikraCore knowledge       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Procedural Memory                   │
│ Certified reusable skills           │
└─────────────────────────────────────┘
```

Raw conversation history must not be treated as the learning unit.

---

# 19. Task Episode Contract

After task completion:

```yaml
task_episode:
  task_id:
  incident_id:
  operator_intent:
  fcaps:
    primary:
    secondary: []
    confidence:
    clarification_required:
  domains: []
  context: {}
  evidence_requested: []
  evidence_observed: []
  ranked_hypotheses: []
  selected_workflow:
  agent_recommendation:
  human_actions: []
  human_corrections: []
  outcome:
  learned_pattern:
  provenance:
```

The existing project specifies this task-episode model and explicitly separates episodic, workflow, semantic and procedural memory. 

---

# 20. FCAPS Lens Integration

For this project:

```text
F = Fault
C = Change
A = Acceptance
P = Performance
S = Security
```

FCAPS is **not an agent** and must not become a mandatory step inside the critical RCA path.

Zaki should invoke FCAPS classification around task context and learning workflows.

Example:

```yaml
fcaps:
  primary: Fault
  secondary:
    - Change
    - Performance
  domain: PS
  confidence: 0.91
  clarification_required: false
```

FCAPS then becomes useful for:

- task classification;
- workflow selection;
- learning organization;
- reporting;
- cross-domain analytics;
- operational knowledge management.

---

# 21. Shift & Handover Architecture

Dark NOC is a 24×7 operational environment. Zaki v1 must separate:

```text
Persistent Agent Identity
        ≠
User Session Context
        ≠
Durable Incident / Task State
```

Use an Incident/Task Ledger.

## Handover record

```yaml
handover:
  handover_id:
  incident_id:
  from_operator:
  to_operator:
  from_agent:
  to_agent:
  what:
  why:
  state:
  evidence:
  pending:
  sla:
  authority:
  acceptance:
  timestamp:
```

Ownership transfer requires explicit acknowledgement.

The next shift should receive structured incident state rather than a replay of chat history.

---

# 22. Zaki Storyteller

Storyteller is a **projection of authoritative execution state**.

It consumes:

```text
Events
Findings
Ranked Hypotheses
Decisions
Delegations
Actions
Outcomes
FikraCore Context
```

It produces:

```text
What happened
Impact
Timeline
Correlation findings
Ranked hypotheses
Evidence changes
Domain attribution
Validation
Actions
Outcome / RCA
```

Every material statement carries provenance:

```text
OBSERVED
INFERRED
CONFIRMED
REJECTED
```

The story does not automatically become authoritative knowledge.

The existing project defines Zaki as a curated incident storyteller consuming events, findings, decisions, delegations, actions, outcomes and FikraCore context while retaining provenance. fileciteturn45file0L398-L410

---

# 23. Zaki Presentation Model

Zaki should provide one backend investigation state with three presentation depths.

## Executive view

```text
INCIDENT
   ↓
SERVICE IMPACT
   ↓
LEADING HYPOTHESIS
   ↓
WHY
   ↓
NEXT ACTION
   ↓
OUTCOME
```

## Operator view

```text
Timeline
Correlation dimensions
Ranked hypotheses
Supporting / contradicting evidence
Knowledge gaps
Blast radius
Domain attribution
Next-best evidence
Validation
```

## Technical view

```text
Correlation vector
12-factor synthesis details
Graph traversal
Evidence provenance
Falsification calculations
Candidate relationship details
Promotion journal
```

The current backend already uses optional inspection gates for the synthesized correlation vector and the 12-factor mathematical breakdown. Preserve that behavior in the operator experience. fileciteturn45file0L26-L34

---

# 24. Runtime Event Model

Zaki should consume and emit standard runtime events.

Suggested events:

```text
INTENT_RECEIVED
TASK_CREATED
INCIDENT_ATTACHED
AGENT_SELECTED
TOOL_REQUESTED
TOOL_AUTHORIZED
TOOL_DENIED
EVIDENCE_RECEIVED
FIKRACORE_STAGE_STARTED
FIKRACORE_STAGE_COMPLETED
CORRELATION_UPDATED
HYPOTHESES_UPDATED
HYPOTHESIS_RANK_CHANGED
EVIDENCE_REQUESTED
DOMAIN_AGENT_DELEGATED
DOMAIN_AGENT_RESPONDED
KNOWLEDGE_GAP_DETECTED
HUMAN_VALIDATION_REQUESTED
HUMAN_VALIDATION_RECEIVED
ACTION_PROPOSED
ACTION_APPROVED
ACTION_EXECUTED
ACTION_VERIFIED
STORY_UPDATED
TASK_EPISODE_CREATED
LEARNING_CANDIDATE_CREATED
KNOWLEDGE_PROMOTION_REQUESTED
KNOWLEDGE_PROMOTED
KNOWLEDGE_PROMOTION_ROLLED_BACK
HANDOVER_REQUESTED
HANDOVER_ACCEPTED
INCIDENT_RESOLVED
```

Every event must contain:

```yaml
event_id:
event_type:
timestamp:
run_id:
task_id:
incident_id:
agent_id:
sequence:
revision:
payload:
provenance:
```

---

# 25. State Management

Zaki must have one authoritative execution state.

```text
                    AUTHORITATIVE RUN STATE
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
       Zaki UI          Zaki Voice         Storyteller
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                         FikraCore
```

The UI and voice layer must not independently infer stage completion, root cause or attribution.

Required consistency controls:

- run ID validation;
- sequence validation;
- revision/version validation;
- duplicate event rejection;
- stale event rejection;
- event provenance;
- idempotent command handling.

---

# 26. Agent Lifecycle

Every domain agent should move through:

```text
REGISTER
   ↓
VALIDATE
   ↓
CERTIFY
   ↓
DEPLOY
   ↓
ACTIVATE
   ↓
MONITOR
   ↓
EVALUATE
   ↓
UPDATE
   ↓
RETIRE
```

Agent lifecycle metadata:

```yaml
agent_id:
version:
lifecycle_state:
owner:
capabilities:
knowledge_version:
skill_version:
evaluation_status:
policy_profile:
health:
last_evaluated:
```

TM Forum's current AI-Native ODA work explicitly includes automated lifecycle management of AI agents alongside ODA Components. citeturn437779search0turn437779search1

---

# 27. Agent Versioning

Zaki must treat the following as independently versioned:

```text
Agent Version
Skill Version
Knowledge Version
Policy Version
Model Version
Tool Version
```

A task execution trace must record all six.

This enables reproducibility and benchmark comparison.

---

# 28. Benchmark-Gated Implementation Strategy

The current FikraCore implementation is a benchmark-driven experiment. Zaki v1 must follow the same discipline.

Do not implement broad autonomous behavior first.

Use:

```text
CURRENT FIKRACORE BACKEND
          ↓
BENCHMARK
          ↓
PASS / FAIL
          ↓
STABILIZE CONTRACT
          ↓
ADD ZAKI CAPABILITY
          ↓
BENCHMARK AGAIN
          ↓
PROMOTE
```

This prevents the harness from hiding weak reasoning behind a better presentation layer.

---

# 29. Zaki v1 Implementation Phases

## Phase 0 — Contract Freeze

### Goal

Freeze the interface between the current FikraCore backend and the future harness.

### Deliverables

- FikraCore Run Contract;
- Task Contract;
- Incident Contract;
- Ranked Hypothesis Contract;
- Evidence Contract;
- Finding Contract;
- Agent Manifest Contract;
- Tool Contract;
- Validation Contract;
- Action Contract;
- Handover Contract;
- Story Statement Contract;
- Task Episode Contract.

### Gate

All existing FikraCore regression tests pass.

---

## Phase 1 — Zaki Harness Core

### Components

```text
zaki/
  intent/
  tasks/
  incidents/
  agents/
  orchestration/
  policy/
  tools/
  events/
  audit/
```

### Implement

- Intent Manager;
- Task Manager;
- Incident Context Manager;
- Agent Registry;
- Capability Registry;
- basic Orchestrator;
- event bus/interface;
- audit trail;
- policy skeleton.

### No autonomous actions.

---

## Phase 2 — FikraCore Adapter

### Goal

Expose the existing FikraCore investigation flow to Zaki without moving its logic.

### Implement

```text
start
state
correlation
hypotheses
hypothesis-test
convergence
knowledge-gap
attribution
blast-radius
next-best-evidence
validation
promotion
```

### Acceptance

A Zaki investigation must produce the same backend investigation result as the current direct FikraCore execution path.

This is the most important v1 parity test.

---

## Phase 3 — Ranked Hypothesis Experience

### Implement

- ranked hypothesis stream;
- rank history;
- score components;
- support/contradiction/missing evidence;
- test hypothesis action;
- evidence request action;
- hypothesis convergence visualization;
- technical deep dive.

### Acceptance

Zaki does not alter hypothesis ordering or scores.

It only presents and orchestrates the FikraCore output.

---

## Phase 4 — Domain-Agent Harness

### Initial agents

```text
PS Agent
CS Agent
RAN Agent
IP Transport Agent
IN/OCS Agent
VAS Agent
IGW Agent
Infra Agent
IT Agent
```

### Implement

- Agent Manifest;
- capability discovery;
- task delegation;
- agent response contract;
- agent health;
- agent versioning;
- policy profiles;
- domain-specific tool scopes.

### Acceptance

The same incident can invoke multiple domain agents without contaminating their contexts.

---

## Phase 5 — Tool / API Gateway

### Implement

```text
TMF API adapters
MCP adapters
Kafka/event adapters
LGTM adapters
NMS/EMS adapters
ITSM adapters
CMDB/inventory adapters
network-analysis adapters
```

### Important

The initial adapters can be simulator/local implementations.

Production adapters must be added without changing agent contracts.

---

## Phase 6 — Human Governance

### Implement

- validation inbox;
- approval requests;
- rejection/correction workflow;
- action authorization;
- policy engine;
- audit trail;
- approval expiry;
- escalation.

### Acceptance

Every production-impacting action has an auditable authority decision.

---

## Phase 7 — Shift Continuity

### Implement

- Incident Ledger;
- Task Ledger;
- persistent agent identity;
- concurrent sessions;
- handover records;
- shift acknowledgement;
- pending-work queue;
- SLA tracking.

### Acceptance

Shift B can continue a Shift A incident using structured state only.

---

## Phase 8 — Storyteller Integration

### Implement

- backend state projection;
- provenance-aware statements;
- synchronized voice narration;
- executive/operator/technical story modes;
- story correction capture.

### Acceptance

Story statements match the authoritative FikraCore state and provenance.

---

## Phase 9 — Learning Integration

### Implement

```text
Task
 ↓
Task Episode
 ↓
Pattern Extraction
 ↓
Learning Evaluation
 ↓
SME Validation
 ↓
FikraCore / Skill Registry
```

### Acceptance

No raw chat history or simulator ground truth is directly promoted to production knowledge.

---

## Phase 10 — TM Forum Alignment Hardening

### Implement

- ODA Component-style manifests;
- standardized API metadata;
- TMF semantic mappings;
- intent metadata;
- lifecycle metadata;
- policy profiles;
- agent observability;
- MCP integration boundaries;
- event contract standardization;
- deployment/runtime packaging suitable for an ODA Canvas integration path.

### Acceptance

All Zaki interfaces are documented with explicit mapping to the selected TM Forum concepts.

---

# 30. Suggested Repository Structure

```text
zaki/
├── domain/
│   ├── contracts/
│   │   ├── intent.py
│   │   ├── task.py
│   │   ├── incident.py
│   │   ├── evidence.py
│   │   ├── hypothesis.py
│   │   ├── finding.py
│   │   ├── action.py
│   │   ├── validation.py
│   │   ├── handover.py
│   │   ├── story.py
│   │   └── task_episode.py
│   │
│   └── enums.py
│
├── runtime/
│   ├── orchestrator.py
│   ├── state.py
│   ├── event_loop.py
│   ├── command_dispatch.py
│   └── lifecycle.py
│
├── intent/
│   ├── manager.py
│   └── normalizer.py
│
├── agents/
│   ├── registry.py
│   ├── manifest.py
│   ├── capability_registry.py
│   ├── dispatcher.py
│   └── health.py
│
├── fikracore/
│   ├── adapter.py
│   ├── run_client.py
│   ├── hypothesis_client.py
│   ├── evidence_client.py
│   ├── validation_client.py
│   └── knowledge_client.py
│
├── tools/
│   ├── gateway.py
│   ├── policy.py
│   ├── tmf/
│   ├── mcp/
│   ├── kafka/
│   ├── lgtm/
│   ├── itsm/
│   └── nms/
│
├── governance/
│   ├── policy_engine.py
│   ├── authorization.py
│   ├── hitl.py
│   └── audit.py
│
├── operations/
│   ├── incident_ledger.py
│   ├── task_ledger.py
│   ├── handover.py
│   ├── delegation.py
│   └── sla.py
│
├── memory/
│   ├── episodic.py
│   ├── workflow.py
│   ├── semantic.py
│   └── procedural.py
│
├── storyteller/
│   ├── storyteller.py
│   ├── provenance.py
│   └── presentation.py
│
├── learning/
│   ├── episode_recorder.py
│   ├── pattern_extractor.py
│   ├── evaluator.py
│   └── promotion.py
│
└── observability/
    ├── tracing.py
    ├── metrics.py
    └── agent_events.py
```

---

# 31. Required v1 Contracts

## 31.1 Agent Manifest

```yaml
api_version: zaki.ai/v1
kind: Agent
metadata:
  id:
  name:
  version:
  domain:
  owner:
spec:
  capabilities: []
  accepted_intents: []
  tools: []
  inputs: []
  outputs: []
  policies:
    risk_level:
    authority_level:
  knowledge:
    version:
  skills:
    versions: []
  lifecycle:
    state:
    certification:
  observability:
    trace_enabled: true
```

## 31.2 Intent Contract

```yaml
api_version: zaki.ai/v1
kind: Intent
metadata:
  id:
  created_at:
spec:
  type:
  natural_language:
  subject:
  scope:
  objective:
  constraints:
  requested_authority:
```

## 31.3 Ranked Hypothesis Contract

```yaml
api_version: zaki.ai/v1
kind: HypothesisRanking
metadata:
  run_id:
  revision:
  generated_at:
spec:
  hypotheses:
    - hypothesis_id:
      rank:
      score:
      state:
      causal_role:
      root_entity:
      domain:
      supporting_evidence: []
      contradicting_evidence: []
      missing_evidence: []
      score_components: {}
      provenance: []
```

## 31.4 Tool Contract

```yaml
api_version: zaki.ai/v1
kind: Tool
metadata:
  id:
  name:
  version:
spec:
  type: READ | ANALYZE | ACTION
  interface: TMF_API | MCP | EVENT | INTERNAL
  input_schema:
  output_schema:
  policy_profile:
  risk_level:
```

## 31.5 Validation Contract

```yaml
api_version: zaki.ai/v1
kind: HumanValidation
metadata:
  id:
  task_id:
  incident_id:
spec:
  decision: CONFIRM | REJECT | MODIFY | REQUEST_EVIDENCE | APPROVE_LEARNING
  target_type:
  target_id:
  reason:
  validator_role:
  authority:
  timestamp:
  provenance:
```

---

# 32. Observability & Audit

Every meaningful agent operation must be traceable.

Required trace dimensions:

```text
trace_id
span_id
run_id
simulation_id
scenario_id
incident_id
task_id
agent_id
capability_id
tool_id
policy_decision
knowledge_version
skill_version
model_version
human_decision
outcome
```

Metrics should include:

### Runtime

- investigation duration;
- time to first useful hypothesis;
- time to hypothesis convergence;
- tool latency;
- evidence requests;
- domain-agent delegation count;
- policy denials;
- HITL wait time.

### Reasoning

- hypothesis rank movement;
- evidence support/contradiction count;
- knowledge-gap count;
- unexplained residual count;
- false-leading hypotheses;
- wrong-high-confidence rate.

### Learning

- human correction rate;
- FCAPS classification accuracy;
- workflow recommendation accuracy;
- knowledge promotion count;
- knowledge rejection count;
- post-learning improvement.

---

# 33. Security & Trust Boundaries

## 33.1 Hard boundary

```text
SIMULATION WORLD
       │
       │ hidden truth
       ▼
   EVALUATOR

OPERATIONAL EVIDENCE + HUMAN VALIDATION
       │
       ▼
   FIKRACORE
       │
       ▼
    ZAKI / DOMAIN AGENTS
```

Zaki must have no operational API that exposes hidden simulator truth.

## 33.2 Ground truth rule

```text
Ground truth evaluates.
Human-validated operational evidence teaches.
```

## 33.3 Knowledge authority

```text
OBSERVED
   ↓
INFERRED / CANDIDATE
   ↓
HUMAN / SME VALIDATION
   ↓
CONFIRMED
   ↓
FIKRACORE / SKILL REGISTRY
```

Zaki must never auto-promote a candidate relationship because an LLM stated it.

---

# 34. Failure Modes the Harness Must Handle

## Agent unavailable

```text
Agent unavailable
   ↓
mark capability unavailable
   ↓
try alternate authorized capability
   ↓
request human assistance if required
```

## Tool failure

```text
Tool timeout / error
   ↓
record failure
   ↓
retry according to policy
   ↓
select alternate evidence source
   ↓
report evidence gap if unresolved
```

## Conflicting domain agents

```text
PS Agent: UPF hypothesis
Transport Agent: Transport hypothesis
             ↓
       FikraCore evidence fusion
             ↓
       Ranked Hypotheses update
```

Zaki must not choose between them independently.

## Incomplete evidence

Return:

```text
INSUFFICIENT_EVIDENCE
```

rather than fabricating certainty.

## Missing topology

Return:

```text
KNOWLEDGE_GAP
MODEL_INSUFFICIENT
```

rather than inventing a relation.

---

# 35. Dark NOC Operator Journey

## Journey A — Investigate

```text
Operator:
"Investigate mobile data degradation in Region-1"

Zaki
 ↓
Intent Manager
 ↓
Create Task / Attach Incident
 ↓
FikraCore investigation
 ↓
Correlation
 ↓
Ranked hypotheses
 ↓
Domain-agent evidence
 ↓
Hypothesis testing
 ↓
Convergence
 ↓
Validation
 ↓
Story
```

## Journey B — Ask why

```text
Operator:
"Why is Transport ranked first?"

Zaki
 ↓
FikraCore hypothesis basis
 ↓
Supporting evidence
Contradicting evidence
Topology
Temporal evidence
Blast radius
Negative evidence
 ↓
Explain
```

## Journey C — Ask what is missing

```text
Operator:
"What don't we know?"

Zaki
 ↓
FikraCore knowledge-gap state
 ↓
Missing relationship / residual
 ↓
Next-best evidence
```

## Journey D — Handover

```text
Shift A
 ↓
Task / Incident Ledger
 ↓
Structured handover
 ↓
Shift B
 ↓
Continue same incident
```

## Journey E — Action

```text
Operator:
"Prepare remediation"
 ↓
Zaki
 ↓
Domain Agent
 ↓
FikraCore impact / dependency context
 ↓
Action proposal
 ↓
Policy
 ↓
HITL
 ↓
Execution
 ↓
Verification
```

---

# 36. Relationship to the Simulator

The FikraCore simulator remains the **qualification environment** for Zaki v1.

The simulator should exercise the same harness interfaces used by the future production system.

```text
                 SCENARIO ENGINE
                       │
                       ▼
                  OBSERVABILITY
                       │
                       ▼
                    ZAKI
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
       FikraCore              Domain Agents
           │                       │
           └───────────┬───────────┘
                       ▼
                   EVALUATOR
```

The simulator's hidden world remains outside Zaki's operational interface.

This preserves the master plan's non-leakage architecture.

---

# 37. Benchmark Programme for Zaki v1

Zaki should be qualified against the existing simulator scenarios.

## A. Incident Reasoning

Measure:

- correct hypothesis rank;
- rank convergence speed;
- root domain accuracy;
- false correlation rate;
- alarm reduction ratio;
- blast-radius precision;
- blast-radius recall;
- evidence requests;
- time to useful hypothesis;
- time to validated RCA.

## B. Discovery

Measure:

- knowledge-gap detection;
- missing-node discovery;
- missing-edge precision;
- missing-edge recall;
- false relationship rate;
- evidence required for discovery;
- human acceptance/rejection.

## C. Learning

Measure:

- FCAPS classification accuracy;
- workflow recommendation accuracy;
- human correction rate;
- confidence calibration;
- wrong-high-confidence rate;
- knowledge stability;
- post-learning improvement on independently varied runs.

## D. Storytelling

Measure:

- factual accuracy;
- provenance coverage;
- unsupported-statement rate;
- rank consistency with backend;
- timeline consistency.

The current FikraCore master plan already defines these categories of evaluation. fileciteturn45file0L1001-L1013

---

# 38. Benchmark Gates Before Expanding Zaki

| Gate | Requirement | Zaki expansion |
|---|---|---|
| G0 | Existing FikraCore regression stable | Begin harness contracts |
| G1 | Correlation stable | Expose investigation API |
| G2 | Hypothesis ranking stable | Build hypothesis UI |
| G3 | Knowledge-gap detection stable | Build discovery workflow |
| G4 | Domain attribution stable | Add domain agents |
| G5 | Validation/promotion stable | Add learning harness |
| G6 | Story provenance stable | Productionize Zaki Storyteller |
| G7 | Cross-scenario improvement measurable | Enable certified skills |
| G8 | Security/governance tests pass | Enable controlled actions |

No gate should be bypassed because the demonstration UI looks successful.

---

# 39. Implementation Priorities

## Priority 1

**Preserve backend parity.**

Zaki must reproduce the existing FikraCore execution behavior without changing investigation results.

## Priority 2

**Standardize contracts.**

Agents, tools, evidence, hypotheses and tasks must plug into a common harness interface.

## Priority 3

**Govern access.**

No agent gets unrestricted operational access.

## Priority 4

**Persist operational state.**

A Dark NOC must survive shift changes, concurrent sessions and agent restarts.

## Priority 5

**Make uncertainty explicit.**

Unknown, missing, stale, conflicting and candidate states must remain visible.

## Priority 6

**Only then add autonomy.**

Action authority should increase only as benchmark and certification gates succeed.

---

# 40. Definition of Done — Zaki v1

Zaki v1 is complete when an operator can:

1. express an investigation intent through voice/chat/UI;
2. create or attach to an operational incident;
3. invoke the existing FikraCore investigation flow;
4. observe the eight investigation stages;
5. inspect the four Correlation dimensions;
6. view dynamically ranked hypotheses;
7. understand why rank changes occur;
8. request evidence;
9. delegate work to authorized domain agents;
10. receive domain-agent findings without losing provenance;
11. detect and explain knowledge gaps;
12. request human validation;
13. maintain incident state across shifts;
14. produce a provenance-backed incident story through Zaki;
15. record a structured task episode;
16. create a learning candidate without auto-promoting it;
17. promote only validated knowledge through the existing FikraCore path;
18. audit every significant agent, tool and human decision;
19. run the same workflows against simulator scenarios;
20. demonstrate that adding the harness does not change the underlying FikraCore reasoning result.

---

# 41. Longer-Term Expansion After v1

These are intentionally outside the v1 critical path.

## Predictive / What-if Operations

```text
Zaki
 ↓
Intent: WHAT_IF
 ↓
FikraCore Predict
 ↓
Propagation
 ↓
Blast Radius
 ↓
Resilience Gap
 ↓
Mitigation Options
```

## AI-Native closed-loop operations

```text
Intent
 ↓
Observe
 ↓
Correlate
 ↓
Reason
 ↓
Plan
 ↓
Approve
 ↓
Act
 ↓
Verify
 ↓
Learn
```

## ODA Canvas deployment

Target deployment where Zaki's runtime capabilities can be mapped onto an AI-Native ODA Canvas environment, using ODA Component interfaces, Open APIs, MCP, IAM, policy, observability and agent lifecycle controls.

TM Forum's current AI-Native ODA Canvas specifically identifies these runtime capabilities and is evolving toward interoperable agents and ODA Components. citeturn437779search0turn437779search8

---

# 42. TM Forum Conformance Roadmap

Do not claim formal conformance in v1 unless tested and certified.

Use a progressive alignment programme:

```text
LEVEL 1 — ARCHITECTURAL ALIGNMENT

Zaki concepts mapped to:
ODA / SID / eTOM / Intent / Open APIs / MCP

        ↓

LEVEL 2 — CONTRACT ALIGNMENT

Machine-readable agent/tool/API contracts
Common semantics
Lifecycle metadata
Policy metadata

        ↓

LEVEL 3 — INTEROPERABILITY

TMF Open APIs
Event APIs
MCP
ODA component integration

        ↓

LEVEL 4 — RUNTIME ALIGNMENT

Canvas-compatible packaging
IAM
Observability
Guardrails
Agent lifecycle
Data/model access controls

        ↓

LEVEL 5 — FORMAL CONFORMANCE

Apply the applicable TM Forum conformance processes and test kits.
```

TM Forum provides Open API conformance certification and an ODA Component/Canvas ecosystem; these should be treated as future validation activities rather than assumed compliance. citeturn972107search0turn972107search9

---

# 43. Final Architectural Principle

Zaki v1 should **grow around the current FikraCore execution flow**.

Do not create:

```text
Zaki Reasoning Engine
Zaki RCA Engine
Zaki Correlation Engine
Zaki competing Knowledge Graph
```

Create:

```text
                 ZAKI
         DARK NOC AGENT HARNESS
                 │
        ┌────────┼────────┐
        │        │        │
      Intent   Agents   Governance
        │        │        │
        └────────┼────────┘
                 ▼
           Orchestration
                 │
       ┌─────────┴──────────┐
       ▼                    ▼
 Domain Agents          FikraCore
                        TELECOM BRAIN
                             │
                  ┌──────────┴──────────┐
                  │                     │
           Correlation Layer      Reasoning Engine
                  │                     │
                  └──────────┬──────────┘
                             │
                       Knowledge / Learning
                             │
                        telecombrain
```

The resulting product boundary is:

> **Zaki provides the governed agent execution fabric for Dark NOC operations; FikraCore provides the telecom correlation, hypothesis ranking, reasoning, discovery and validated operational knowledge.**

---

# 44. Recommended First Coding Sprint

Do not start by building all domain agents.

Implement only this thin vertical slice:

```text
Operator Intent
      ↓
Zaki Intent Manager
      ↓
Task / Incident
      ↓
Zaki Orchestrator
      ↓
FikraCore Adapter
      ↓
Existing 8-stage investigation
      ↓
Ranked Hypotheses
      ↓
Zaki Presentation
      ↓
Zaki Audit Trace
```

Then run it against the existing DEMO-001 / cross-domain outage flow.

### Acceptance test

```text
Direct FikraCore execution
        VS
Zaki-mediated FikraCore execution
```

The backend outputs must be equivalent for:

- correlation results;
- hypothesis identities;
- hypothesis ranking;
- scores;
- convergence;
- knowledge gaps;
- domain attribution;
- affected services;
- next-best evidence;
- validation state;
- knowledge promotion state.

Only after this parity test passes should domain-agent delegation and additional harness capabilities be expanded.

---

# 45. References

## User-provided architecture

- `demo-v.md` — current implemented/target FikraCore investigation execution plan.
- `fikracore-simulator-master-prompt.md` — simulator, domain-agent, HITL, learning, Zaki and benchmark master specification.

## TM Forum references checked 2026-09-19

- TM Forum AI-Native ODA Roadmap, TMF448 v1.0.0.
- TM Forum AI-native ODA Canvas.
- TM Forum ODA Components & Canvas.
- TM Forum Open APIs.
- TM Forum ODA Component Inventory v24.0.0.
- TM Forum SID / Information Framework v26.0.
- TM Forum eTOM / Business Process Framework v26.0.
- TM Forum Intent Toolkit / Intent Ontology v3.6.0 lineage.

Official references:

- https://www.tmforum.org/resources/introductory-guide/tmf448-ai-native-oda-roadmap-v1-0-0/
- https://www.tmforum.org/oda/deployment-and-runtime/oda-canvas
- https://www.tmforum.org/open-digital-architecture/components-canvas/
- https://www.tmforum.org/oda/open-apis
- https://www.tmforum.org/resources/introductory-guide/oda-component-inventory-v24-0-0-ig1242/
- https://www.tmforum.org/resources/model/gb922-information-framework-models-suite-v26-0/
- https://www.tmforum.org/resources/collection/gb921-business-process-framework-etom-suite-v26-0/
- https://www.tmforum.org/toolkits/intent/

---

# Appendix A — Current FikraCore Stage-to-Zaki Mapping

| Current FikraCore stage | Zaki harness responsibility |
|---|---|
| 1. Telemetry Ingestion | Start task, establish evidence context |
| 2. Correlation Engine | Present progress and dimension findings |
| 3. Hypothesis Generation | Present dynamically generated ranked candidates when available |
| 4. Hypothesis Testing | Coordinate evidence/test requests and show ranking movement |
| 5. Convergence & Gap Detection | Explain leading hypothesis and knowledge gaps |
| 6. Domain Attribution & Services | Show primary/contributing/affected roles and blast radius |
| 7. Next-Best Evidence & Validation | Request evidence, delegate, invoke HITL |
| 8. Knowledge Graph Promotion | Govern promotion request and audit the outcome |

The stage mapping intentionally leaves the underlying stage semantics unchanged. fileciteturn45file0L126-L154

---

# Appendix B — Recommended Operator Vocabulary

| Avoid | Use |
|---|---|
| RCA engine inside Zaki | FikraCore Reasoning |
| Zaki correlation engine | FikraCore Correlation Layer |
| Worker agent | Domain Agent |
| Configuration in FCAPS | Change in FCAPS |
| Accounting in FCAPS | Acceptance in FCAPS |
| AI guessed topology | Candidate Relationship |
| AI learned truth | Validated Operational Knowledge |
| Chat history learning | Task Episode Learning |
| Autonomous RCA certainty | Ranked / evidence-backed hypothesis |
| Hidden truth | Evaluator-only ground truth |

---

# Appendix C — One-Sentence Product Definition

> **Zaki v1 is a TM Forum-aligned Dark NOC Agent Harness that safely orchestrates telecom domain agents, FikraCore investigation, operational tools and human decisions while preserving one authoritative, provenance-backed execution state.**
