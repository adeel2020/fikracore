# FikraCore & Zaki NOC SME: Authoritative Architectural Enhancement Plan

---

## 1. Executive Architecture Axioms

1. **The Separation of Concerns**: FikraCore owns authoritative network physics, causality, and canonical knowledge; Zaki owns operational orchestration, governance, and explanation.
2. **The Experience Spine**: The `TaskEpisodeContract` binds all other contracts around **one unit of operational work** over time without owning or duplicating their domain semantics.
3. **The Crucial Separation**: 
   $$\text{Telemetry} \neq \text{Evidence} \neq \text{Correlation} \neq \text{Pattern} \neq \text{Incident} \neq \text{Hypothesis} \neq \text{Root Cause}$$
4. **One Canonical Graph, Many Capability Clusters**: No separate database clusters for index nodes or capabilities. Everything operates against the single canonical graph in `gbrain`.
5. **Cross-Domain by Design**: Knowledge patterns and learning episodes are **not siloed under mobile-core**. Scope is an explicit attribute (`scope: domains: [...]`), and patterns are stored under cross-domain and domain-specific hierarchies.
6. **Domain-Scoped Governed HITL**: Specialized domain agents (Transport, Core, RAN, Cloud, Voice, Security) execute diagnostics and connect to Zaki for domain-scoped Human-in-the-Loop (HITL) authorization.
7. **Stage-Synchronized Executive Voice**: Live speech prosody is synchronized with network simulation stage progression with zero audio overlap, zero queuing lag, and zero dropouts.

---

## 2. Canonical Graph Conceptual Model: The 4-Plane Architecture

In accordance with FikraCore Architecture Rules (Sections 1, 3 & 4), `gbrain` models the telecom operational universe as **The 4-Plane Conceptual Model**, realized by a **Single Canonical Graph** with dedicated **Index Nodes** for sub-millisecond retrieval without data duplication.

### 2.1 The 4 Operational Planes
1. **Plane 1: Topology Plane (`TOPOLOGY` Index)**:
   - Physical and virtual telecom reality: RAN, IP Transport, Mobile Core, IMS Voice, Optical DWDM, Cloud NFVI, and OSS Management Systems.
   - Sourced deterministically from network inventory and configuration graphs.
   - Houses explicit redundancy edges (`HA_PAIR_WITH`, `BACKUP_PATH_FOR`).
2. **Plane 2: Incident State Plane (`INCIDENTS` Index)**:
   - Dynamic degradation states exhibiting live alarm and metric deviations.
   - Anchored directly to affected Topology nodes with blast-radius projection edges.
3. **Plane 3: Cognitive Reasoning & Actions Plane (`EPISODES` Index)**:
   - The operational experience spine (`TaskEpisode`) binding active investigations.
   - Evaluates competing hypotheses, dispatches Step 3 discrimination probes, logs agent findings, and gates HITL desk signoffs.
   - **Never floats as an isolated network domain**; visualized as an active overlay anchored to impacted entities.
4. **Plane 4: Enterprise Intelligence & Procedures Plane (`PATTERNS` & `PLAYBOOKS` Indexes)**:
   - Reusable multi-domain failure signatures (`PATTERNS`) with `scope.domains` attributes.
   - Executable Method of Procedure (MOP) runbooks (`PLAYBOOKS`) with verified preconditions and rollback plans.

### 2.2 Graph Index Nodes & Entity Topology in `gbrain`
```text
gbrain Canonical Graph
├── TOPOLOGY (Index Node) ◄─── THE NETWORK REALITY (Ground Truth)
│    ├── RAN (gNodeB, eNodeB)
│    ├── IP_TRANSPORT (Edge Routers, Core Routers, VRFs)
│    ├── MOBILE_CORE (UPF, AMF, SMF)
│    ├── IMS_VOICE (P-CSCF, S-CSCF)
│    ├── CLOUD_INFRA (K8s Nodes, Ceph Storage)
│    └── OSS_MANAGEMENT (Fault, Perf, ITSM, Telemetry Stream)
│
├── INCIDENTS (Index Node) ◄─── THE OPERATIONAL PERCEPTION
│    └── [Incident Entity] (e.g., "Dubai South User Plane Degradation")
│         ├── primary_domain: "PS_CORE"
│         ├── ANCHORED_TO ───► [TOPOLOGY Entity] (e.g., UPF-03)
│         └── BOUND_TO_EPISODE ───► [TaskEpisode Entity]
│
├── EPISODES (Index Node) ◄─── COGNITIVE REASONING & ACTIONS (Zaki's Spine)
│    └── [TaskEpisode Entity] (e.g., "Task Episode: Dubai South UPF-03 Anomaly")
│         ├── INVESTIGATES ───► [Incident Entity]
│         ├── FORMULATES ───► [Hypothesis Entity]
│         ├── DISPATCHES ───► [Discrimination Probe]
│         └── EXECUTES ───► [Playbook Entity]
│
├── PATTERNS (Index Node) ◄─── REUSABLE KNOWLEDGE
│    └── [Pattern Entity] (e.g., "Backhaul Buffer Overflow Under Traffic Burst")
│         ├── scope.domains: ["IP_TRANSPORT", "PS_CORE"]
│         ├── MATCHES ───► [Incident Entity]
│         └── HAS_REMEDIAL_PLAYBOOK ───► [Playbook Entity]
│
└── PLAYBOOKS (Index Node) ◄─── REUSABLE RUNBOOKS & MOPS
     └── [Playbook Entity] (e.g., "Edge Router Traffic Drain & Reroute")
          ├── target_domains: ["IP_TRANSPORT"]
          ├── safety_tier: "CONTROLLED_REVERSIBLE"
          └── REQUIRES_GRAPH_EDGE: "BACKUP_PATH_FOR"
```

### 2.3 Index Node Rules (FikraCore Specification Rules 2, 3, 14)
- **`TOPOLOGY` Index Node**: Contains pointer edges to all physical and virtual network elements, services, and management nodes.
- **`INCIDENTS` Index Node**: Contains lightweight pointer edges with matching metadata (symptoms, affected service, root cause). **Never duplicates full incident bodies.**
- **`PATTERNS` Index Node**: Contains pointer edges with matching signatures, recurrence frequency, and `scope.domains`. **Never duplicates full pattern specifications.**
- **`PLAYBOOKS` Index Node**: Contains pointer edges with target fault modes, safety tiers, and verified precondition graph queries. **Never duplicates full playbook bodies.**
- **`EPISODES` Index Node**: Contains pointer edges to active and completed TaskEpisodes, enabling historical case retrieval and cross-shift handover.
- **Multi-Domain Traversal**: Domains (`IP_TRANSPORT`, `PS_CORE`, etc.) are attributes inside entity scopes, allowing cross-domain pattern matching and blast-radius graph traversal via `gbrain` MCP (`find_patterns`, `get_topology`).
- **Retrieval**: Sub-millisecond lookup via `gbrain` MCP (`get_page`, `list_links`) grounds incoming Task Episodes before investigation begins.

---

## 3. Two-Tier Contract Architecture

### Tier 1: System Level (FikraCore — Canonical Truth)
*Modular domain package located at `services/agents/src/engine_stack/engines/telecom_brain/investigation/contracts/` with top-level `__init__.py` facade for 100% backward compatibility.*

```text
telecom_brain/investigation/contracts/
├── __init__.py                # Top-level facade re-exporting all symbols (zero breaking changes)
├── base.py                    # Contract base class, Pydantic v1/v2 compatibility shim, common Enums
├── agent.py                   # AgentManifestContract (Actor identity, capabilities, authority ceilings)
├── domain.py                  # DomainContract (Operational jurisdictions: IP_TRANSPORT, PS_CORE, RAN)
├── evidence.py                # RawEvidence, EmergingEvidence (The Bridge), ValidatedEvidence
├── hypothesis.py              # InvestigationHypothesis, DiscriminationProbeContract
├── topology.py                # RelationshipContract (HA_PAIR_WITH, BACKUP_PATH_FOR), BlastRadius
├── pattern.py                 # PatternRecognitionContract, PatternContract (cross-domain)
├── remediation.py             # RemediationPlaybookContract (MOPs, preconditions, rollback plans)
├── promotion.py               # KnowledgePromotionContract, KnowledgePromotionRecord (Audit Trail)
└── simulation.py              # WhatIfSimulationResult, ResilienceGap, MitigationOption
```

#### 1. Evidence Hierarchy (3 States) — `evidence.py`
- **`RawEvidenceContract`**: Pristine network telemetry (alarms, metrics, logs, traces, counters). Emitted by OSS/Kafka with zero interpretation.
- **`EmergingEvidenceContract` (The Bridge)**: Windowed sequences of `INFO`/`WARN` alarms, rate deviations, and weak signals (*"Not yet an incident, but becoming operationally significant"*). Prevents telemetry noise from polluting Incident or Hypothesis contracts.
- **`ValidatedEvidenceContract`**: Evidence checked in the crucible of an active investigation; explicitly marked as `SUPPORTS`, `CONTRADICTS`, `CONFIRMS`, or `RULES_OUT`.

#### 2. Pattern, Topology, Agent & Remediation Contracts
- **`AgentManifestContract` (`agent.py`)**: Formal contract defining autonomous telecom agent identities, capability sets, tool bindings, and authority ceilings (`LEVEL_1_ANALYZE` to `LEVEL_3_EXECUTE`).
- **`DomainContract` (`domain.py`)**: Operational network jurisdictions (`IP_TRANSPORT`, `PS_CORE`, `RAN`, `CLOUD_INFRA`, `IMS_VOICE`, `SECURITY`), managed entities, and authorized engineering roles.
- **`RelationshipContract` (`topology.py`)**: Governs first-class typed edges in the Canonical Graph (`HA_PAIR_WITH`, `BACKUP_PATH_FOR`, `DEPENDS_ON`, `SUPPORTS`, `CAUSED`). Redundancy and failover paths are **explicit graph edges**, never LLM guesses.
- **`DiscriminationProbeContract` (`hypothesis.py`)**: Active diagnostic probes dispatched to distinguish between competing hypotheses.
- **`PatternContract` (`pattern.py`)**: Reusable operational signature with occurrence history across episodes.
- **`RemediationPlaybookContract` (`remediation.py`)**: Operational procedures (`FAILOVER`, `DRAIN`, `RATE_LIMIT`, `RESTART`), mandatory preconditions, and verified rollback plans.
- **`KnowledgePromotionContract` (`promotion.py`)**: Governs the transition from validated findings/episodes to `CANONICAL` graph knowledge. Produces an immutable, auditable `KnowledgePromotionRecord` capturing **WHAT** was promoted, **WHY** (recurrence count, zero contradictions), on what **EVIDENCE**, and by **WHOM** (desk signoff).

---

### Tier 2: Harness Level (Zaki — Operational Experience & Governance)
*Located in `services/agents/src/zaki/`.*

#### 1. `TaskEpisodeContract` (`zaki/contracts/task_episode.py`)
Binds one unit of work across time, causality, and ownership dynamically at runtime (no hardcoding):
```yaml
TaskEpisodeContract:
  # Dynamic Identifiers & Classification
  episode_id: str                      # Dynamic: {region}_{component}_{timestamp}
  display_title: str                   # Dynamic: "{severity} {service_impact} in {cluster_name}"
  task_type: TaskTypeEnum              # INCIDENT_INVESTIGATION | PROACTIVE_HUNT | CHANGE_VERIFICATION
  status: EpisodeStatusEnum            # DETECTING | CORRELATING | INVESTIGATING | MITIGATING | RESOLVED
  
  # Operational Roles (resolved from active shift/desk)
  initiated_by: OperationalActor       # { role: str, actor_id: str, channel: str }
  assigned_desk_lead: OperationalActor # { role: str, actor_id: str, email: str }
  lead_domain_agent: DomainAgentEnum   # TRANSPORT_AGENT | PACKET_CORE_AGENT | RAN_AGENT | CLOUD_AGENT
  
  # Temporal Bounds (synced with Kafka telemetry timestamps)
  start_time: ISO8601Timestamp         # Dynamic anomaly detection time
  resolved_time: Optional[ISO8601]     # None while active; stamped on recovery
  duration_minutes: float              # Computed: (now - start_time)
  
  # Topology Anchor (traversed dynamically from gbrain via MCP)
  target_cluster_ref: str              # Regional cluster identifier
  affected_service_paths: List[str]    # End-to-end user planes impacted
  
  # Dynamic Telemetry Accumulator (populated as evidence emerges)
  evidence_records: List[EvidenceItem]
    - evidence_name: str               # Human-readable: "{node_name} {metric_name} Spike"
      evidence_tier: EvidenceTierEnum  # RAW | EMERGING | VALIDATED
      telemetry_source: str            # "gnmi" | "kafka" | "snmp"
      observed_value: Any              # Live measured reading
      baseline_value: Any              # Normal operating threshold
      timestamp: ISO8601Timestamp
      
  # Active Hypotheses Engine (managed by Causal Reasoning Engine)
  hypotheses: List[HypothesisItem]
    - hypothesis_name: str             # Descriptive: "{component} {fault_mode}"
      status: HypothesisStatusEnum     # SUSPECTED | UNDER_VALIDATION | RULED_OUT | CONFIRMED
      supporting_evidence: List[str]   # Dynamic list of corroborating evidence names
      contradicting_evidence: List[str]# Dynamic list of conflicting evidence names
      missing_probes: List[str]        # Gaps required before RCA declaration
      
  # Diagnostic & Remediation History (dispatched to Domain Agents)
  action_history: List[ActionItem]
    - action_name: str                 # Descriptive: "Check QoS queue drops on {interface}"
      originating_agent: str           # Exact domain agent name
      safety_tier: ActionSafetyEnum    # READ_ONLY_DIAGNOSTIC | CONTROLLED_REVERSIBLE | DISRUPTIVE
      execution_status: StatusEnum     # PROPOSED | APPROVED | EXECUTING | COMPLETED | FAILED
      output_summary: str              # Telemetry findings in human telecom words
      
  # Human-In-The-Loop Governance
  hitl_gate: Optional[HITLApproval]
    - required: bool                   # True for CONTROLLED or DISRUPTIVE actions
      authorized_role: str             # Desk with authority: e.g. "TRANSPORT_DESK_LEAD"
      approver_name: Optional[str]     # Set when human engineer approves in Common Room
      decision: ApprovalDecisionEnum   # PENDING | APPROVED | REJECTED
      decision_timestamp: Optional[ISO8601Timestamp]
      
  # Lifecycle Closure & Knowledge Capture
  resolution_summary: Optional[str]    # Human-readable restoration narrative
  extracted_pattern_id: Optional[str]  # Linked to PATTERNS index node in gbrain
```

#### 2. `OperationalContextContract` (`zaki/contracts/operational_context.py`)
- Populates the pre-prompt operational state deterministically from telemetry and graph.
- Bridges `incident_anchor`, `temporal_baseline`, `topology_and_redundancy` (via `gbrain`), `investigation_memory`, `blast_radius`, and `operational_activity`.

#### 3. `BehaviorContract` (`zaki/governance/behavior.py`)
Formal behavioral specification enforcing NOC SME benchmark rules:
```yaml
BehaviorContract:
  # Causal Discipline & Evidence Accounting
  causal_reasoning_rules:
    forbid_arbitrary_percentages: true     # Bans "68% confidence"; enforces evidence counts
    confidence_accounting:
      supporting_evidence_count: int       # Number of corroborating signals
      contradicting_evidence_count: int    # Number of conflicting signals
      untested_knowledge_gaps_count: int   # Remaining gaps before declaration
      confidence_status: str               # "OBSERVED" | "CORRELATED" | "SUPPORTED" | "CONFIRMED"
    forbid_premature_rca: true             # "It is not yet confirmed" if knowledge gaps exist
    observation_not_causation: true        # Symptom != Root Cause
    forbid_hidden_oracle_leakage: true     # Cannot expose simulation hidden ground truth

  # Action Safety & Governance
  action_governance:
    safety_tier: ActionSafetyEnum          # READ_ONLY_DIAGNOSTIC | CONTROLLED_REVERSIBLE | DISRUPTIVE
    require_hitl_for_disruptive: true      # Mandatory desk signoff for traffic shift/restart
    require_verified_rollback_plan: true   # Cannot propose action without rollback MOP
    target_desk: str                       # e.g., "TRANSPORT_DESK" | "CORE_DESK"

  # Pattern Grounding Discipline
  pattern_grounding:
    mandate_difference_articulation: true  # Must distinguish "similar" from "same"
    required_similarity_threshold: 0.85
    cite_historical_episodes: true         # Must reference specific previous TaskEpisodes

  # Natural Telecom Phrasing & Executive Voice
  speech_and_pacing:
    narration_mode: "SPEECH_PACED"         # Stage progression holds advancement until speech completes
    drop_voice_allowed: false              # Zero audio cutoffs
    queue_overlap_allowed: false           # Zero overlapping speech
    acronym_prosody_expansion: true        # "HTTP 502" -> "HTTP 5, 0, 2"; "18.4%" -> "18 point 4 percent"
    human_readable_telecom_terms: true     # Canonical component names; bans raw internal codes
```

#### 4. Specialist Agent Runtime & HITL Work Order Contracts (`zaki/`)
- **`AgentRegistry` (`zaki/agents/registry.py`)**: Runtime registration and activation of specialist agents based on `AgentManifestContract`.
- **`HumanValidationContract` (`zaki/governance/validation.py`)**: Domain-scoped approval work order routed through Zaki's hub-and-spoke Common Room HITL inbox.

---

## 4. Extensible Architecture: Ownership of Registries

In strict adherence to **Axiom 1 (Separation of Concerns)**, registries are owned where their authority resides:

### 4.1 FikraCore System Layer (Authoritative Physics & Tools)
*Located in `services/agents/src/engine_stack/engines/telecom_brain/`*
- **`DomainToolRegistry` (`capabilities/tool_registry.py`)**:
  - Central registry for diagnostic probes and telemetry interrogators (`interface_buffer_probe`, `bgp_neighbor_health`, `upf_session_audit`).
  - FikraCore's causal reasoning engine uses these tools for **Step 3 Discrimination Probes** regardless of whether Zaki is in the loop.
  - Pluggable: Domain teams register new diagnostic tools with typed safety metadata (`READ_ONLY_DIAGNOSTIC` vs `DISRUPTIVE`) and target graph entities (`ROUTER`, `UPF`, `GNODEB`).
- **`PlaybookRegistry` (`gbrain` + `services/playbook_service.py`)**:
  - Runbooks and MOPs live in `gbrain` under `knowledge/playbooks/*`.
  - FikraCore validates preconditions, verifies graph redundancy before execution, and validates automated rollback procedures.

### 4.2 Zaki Harness Layer (Operational Orchestration & HITL)
*Located in `services/agents/src/zaki/agents/`*
- **`AgentRegistry` & `CapabilityRegistry` (`agents/registry.py`, `agents/capability_registry.py`)**:
  - Discovers and routes tasks to domain specialist agents (`IP_TRANSPORT`, `PS_CORE`, `RAN`, `CLOUD_INFRA`, `IMS_VOICE`, `SECURITY`).
  - Enforces authority ceilings, maps intents to domain capabilities, and coordinates Common Room collaboration.
  - Domain agents invoke tools from FikraCore's `DomainToolRegistry` and request playbook execution through Zaki's HITL gate.

### 4.3 Common Incident Room Live Attribution
Every interaction in the NOC collaboration room is attributed by agent badge and name:
1. `Zaki (NOC Copilot)` dispatches an `EvidenceRequest` to the assigned domain agent in the `AgentRegistry`.
2. The domain agent executes its registered diagnostic tool from `DomainToolRegistry` and posts findings in human-readable telecom terms.
3. If remediation is required, the matching registered playbook is loaded and Zaki prompts the authorized engineering desk lead.
4. The authorized engineer signs off, the action executes, and the complete audit trail binds to the active `TaskEpisode`.

---

## 5. Stage-Synchronized Speech Engine (Speech-Paced: Zero Voice Drop)

To guarantee that **no voice is dropped** and stage progression is synchronized with speech completion:

1. **Speech-Paced Progression (Zero Voice Drop)**:
   - **Rule**: If the simulation stage moves fast, the voice must **never drop or cut off**.
   - **Mechanism**: The simulation stage runner registers a barrier callback with the Speech Engine (`on_speech_completed`).
   - The stage **holds advancement** until Zaki finishes narrating the active stage's flash summary.
   - Once narration completes (`speech_end` event), the barrier opens and the next simulation stage triggers automatically.
   - Prevents audio truncation, eliminates queue buildup, and guarantees 100% audio fidelity for operators.
2. **Natural Telecom Prosody & Phrasing**:
   - **Digit & Acronym Phrasing**: `"HTTP 502"` $\rightarrow$ *"HTTP 5, 0, 2"*; `"18.4%"` $\rightarrow$ *"18 point 4 percent"*; `"PE-RTR-21"` $\rightarrow$ *"Edge Router 21"*.
   - **Clause Breathing Pauses**: `200ms` comma pause, `350ms` sentence pause, `420ms` question pause, `500ms` paragraph shift.
   - **Human-Readable Telecom Naming**: Never speak raw database IDs or code labels (`REQ-04`, `EVD-TRANS-009`); speak canonical operational names (`Edge Router 21 Output Buffer Drop`).

---

## 6. Zaki Operational Scaffolding & Structured gbrain MCP Contract (Section 22 Alignment)

### Section 22 NOC Context Scaffolding
Before dispatching any prompt or answering operator queries, the **Context Engine** deterministically populates the operational envelope:
1. **Current Incident Anchor**: Incident ID, start time, active duration, status, and hidden simulation ground truth barrier.
2. **Temporal & Baseline Context**: Pre-incident changes (active CRs/MOPs within last 60 mins), baseline metrics, first observed anomaly timestamp.
3. **Topology & Redundancy**: Primary service path, downstream dependencies, and HA backup paths deterministically queried from `gbrain` via MCP (`HA_PAIR_WITH`, `BACKUP_PATH_FOR`).
4. **Investigation Memory**: Completed checks, ruled-out hypotheses, active checks, and pending probes to eliminate duplicate inquiries.
5. **Blast Radius**: Explicit separation of direct physical impact, transitive service impact, observed customer impact, and potential unmitigated risk.
6. **Operational Activity**: Lead domain agent, assigned desk lead, shift handover notes, and active remediation playbooks.

### Structured gbrain MCP Interface (4-Plane Typed Tools)
All graph interactions strictly use typed MCP tools mapped to the 4 planes:
- **Plane 1 (Topology)**: `gbrain.get_topology(node_id, depth=2)` & `gbrain.get_redundant_paths(node_id)` $\rightarrow$ returns deterministic graph neighbors and explicit redundancy edges (`HA_PAIR_WITH`, `BACKUP_PATH_FOR`).
- **Plane 2 (Incidents)**: `gbrain.get_active_incidents()` & `gbrain.get_blast_radius(incident_id)` $\rightarrow$ returns direct physical, transitive service, and observed customer impact.
- **Plane 3 (Episodes)**: `gbrain.record_episode(task_episode_payload)` & `gbrain.get_episode_state(episode_id)` $\rightarrow$ queries/patches the live investigation trail under `EPISODES` index.
- **Plane 4 (Knowledge & Playbooks)**: `gbrain.find_patterns(symptom_vector, domains)` & `gbrain.get_playbook(playbook_id)` $\rightarrow$ returns matched patterns and verified runbooks with rollback steps.

---

## 7. Phased Implementation Roadmap

### Phase 1: Canonical System Contracts (`telecom_brain/investigation/contracts/`)
- [x] Refactor monolithic `contracts.py` into a modular package `contracts/` with top-level `__init__.py` facade (100% backward compatibility).
- [x] Create `base.py`: Base `Contract` model, Pydantic v1/v2 compatibility shim, common enums.
- [x] Create `agent.py`: `AgentManifestContract` (Actor identity, capabilities, tool bindings, and authority ceilings).
- [x] Create `domain.py`: `DomainContract` defining network operational jurisdictions (`IP_TRANSPORT`, `PS_CORE`, etc.).
- [x] Create `evidence.py`: `RawEvidenceContract`, `EmergingEvidenceContract` (The Bridge), `ValidatedEvidenceContract`.
- [x] Create `topology.py`: `RelationshipContract` with typed edge semantics (`HA_PAIR_WITH`, `BACKUP_PATH_FOR`) and `BlastRadiusAssessment`.
- [x] Create `hypothesis.py`: `InvestigationHypothesis` and `DiscriminationProbeContract` for active validation.
- [x] Create `pattern.py`: `PatternContract` and `PatternRecognitionContract` (with cross-domain scope).
- [x] Create `remediation.py`: `RemediationPlaybookContract` defining executable MOPs and rollback schemas.
- [x] Create `promotion.py`: `KnowledgePromotionContract` and `KnowledgePromotionRecord` (Audit Trail).
- [x] Create `simulation.py`: `WhatIfSimulationResult`, `ResilienceGap`, `MitigationOption`.
- [x] Verify all existing unit tests and simulator runs import cleanly from `contracts` with zero regressions.

### Phase 2: Zaki Orchestration & Governance Contracts
- [x] Migrate & update `task_episode.py` (`zaki/contracts/`): Enhance contract into the dynamic Operational Spine.
- [x] Create `operational_context.py` (`zaki/contracts/`): `OperationalContextContract` (Section 22 Context Scaffolding Envelope).
- [x] Migrate & update `validation.py` (`zaki/governance/`): `HumanValidationContract` with domain jurisdiction and originating agent scoping.
- [x] Create `behavior.py` (`zaki/governance/`): `BehaviorContract` enforcing NOC SME causal, action, and speech-pacing guardrails.

### Phase 3: Domain Capabilities & Agent Roster
- [x] Implement `DomainToolRegistry` in FikraCore (`telecom_brain/capabilities/tool_registry.py`): Pluggable diagnostic probes for Step 3 Discrimination testing.
- [x] Implement `PlaybookRegistry` in FikraCore (`telecom_brain/services/playbook_service.py`): Integrates with `gbrain` `PLAYBOOKS` index node for runbook validation and execution.
- [x] Enhance Zaki's `AgentRegistry` and `DomainCapabilityRegistry` (`zaki/agents/`): Wire the extensible domain agents to FikraCore's `DomainToolRegistry` and Zaki's HITL gate.

### Phase 4: Engine Orchestration & Ingestion Bridge
- [x] Build `EmergingEvidenceFilter` in the ingestion pipeline to group `INFO`/`WARN` sequences before incident creation.
- [x] Build `DiscriminationProbeDispatcher` to actively test competing hypotheses using domain diagnostic tools.
- [x] Connect `ZakiOrchestrator` to anchor all investigations in `TaskEpisode`.
- [x] Implement `KnowledgePromotionService`: Evaluates recurrence criteria, prompts domain leads for signoff, and commits auditable `KnowledgePromotionRecord` updates to `gbrain`.
- [x] Wire `gbrain` MCP integration to query/patch index nodes (`TOPOLOGY`, `INCIDENTS`, `EPISODES`, `PATTERNS`, `PLAYBOOKS`).

### Phase 5: Knowledge Graph Visualization & Frontend Scaffolding
- [x] Rewire `build_graph.py` for the 4-Plane Canonical Model:
  - Disentangle `Observability & Remediation`: Rename to `OSS & Management Systems` (Fault/Perf/ITSM); move `VAS/Messaging` and `IN SCP` to core telecom services.
  - Eliminate detached `Cross-Domain Operations` bubble: Project active incident and reasoning planes as visual overlays anchored directly to affected network nodes.
  - Add interactive Plane Filter toggles (Topology Plane, Incident Plane, Cognitive Reasoning Plane, Pattern Plane).
- [x] Create `scripts/export_contract_types.py` to auto-generate `contracts.generated.ts`.
- [x] Implement `SpeechCompletionBarrier` in `frontend/src/lib/voice.ts` so simulation stage progression awaits speech completion (zero voice drop).
- [x] Connect `ZakiLiveStoryOverlay.tsx` to narrate stage advancements without voice drop or queue overlap.
- [x] Render the NOC Common Room activity stream showing explicit agent badges.

### Phase 6: Automated Verification & Certification Test Suite
- [x] `test_evidence_lifecycle`: Raw $\rightarrow$ Emerging $\rightarrow$ Validated progression.
- [x] `test_task_episode_spine`: Verifies zero duplication and foreign key references.
- [x] `test_domain_scoped_hitl`: Rejects cross-domain approvals; verifies agent name attribution.
- [x] `test_speech_paced_progression`: Verifies that simulation stage runner holds advancement until speech finishes (zero audio drops).
- [x] `test_section22_scaffolding`: Validates envelope population matches Benchmark Spec Section 22.
- [x] `test_4plane_graph_topology`: Verifies index node integrity (`TOPOLOGY`, `INCIDENTS`, `EPISODES`, `PATTERNS`, `PLAYBOOKS`) and `build_graph.py` layout.
