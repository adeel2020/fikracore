# FikraCore & Zaki Conceptual Model Alignment Roadmap

> **Status:** Authoritative & Phased  
> **Source Documents:** [`docs/conceptual model/architecture-indepth.md`](file:///Users/adeelarshad/FikraCore/docs/conceptual%20model/architecture-indepth.md) and [`docs/conceptual model/cm-w-zaki.md`](file:///Users/adeelarshad/FikraCore/docs/conceptual%20model/cm-w-zaki.md)  
> **Last Updated:** October 2, 2026  

---

## 1. Architectural Philosophy & Roles

1. **FikraCore = Semantic Authority**  
   - Source of invariant operational and causal truth (Topology, Entities, Rules, Golden Runs, Cross-Domain Links).
   - Sits beside/behind runtime operations, resolving semantic truth into contextual references.

2. **OperationalContext = Runtime Observation Boundary**  
   - Answers: *"What is authorized, relevant, and visible right now?"*
   - Strictly enforces the **Truth-Blind Boundary** (hiding simulator ground truth; admitting only telemetry and authorized topology).
   - Assembles the runtime sub-envelopes and supplies them as typed inputs into the Correlation Engine.

3. **Zaki = Cognitive NOC Operator**  
   - Active agent operating across Perception $\to$ Cognition $\to$ Interaction.
   - Governed by Cross-Cutting Fabric (`BehaviorContract`, `ProsodyContract`, `CuratedResponseContract`).
   - Does **not** sit inside `IncidentContextContract` or `OperationalContextContract`.

4. **Incident Decoupling**  
   - `IncidentContract`: The ITSM / OSS trouble ticket record (what was reported).
   - `IncidentContextContract`: The active cognitive workspace (blast radius, hypotheses, evidence window).

5. **TaskEpisode = The Cognitive Spine & Closed Loop**  
   - Binds the temporal cognitive work: Evidence $\to$ Reasoning $\to$ Action $\to$ HITL $\to$ Outcome $\to$ Learning.
   - Promotes validated operational learnings back into FikraCore.

---

## 2. Target Execution Roadmap & Data Flow

```
                         FIKRACORE (Semantic Authority)
                                       │
                      semantic resolution / references
                                       ▼
       ╔═══════════════════════════════════════════════════════════════╗
       ║                OPERATIONAL CONTEXT ENVELOPE                   ║
       ║                                                               ║
       ║  Session Identity & Scope [Phase 2]                           ║
       ║  ├── ContextIdentityContract / OperationalModeContract        ║
       ║  └── AuthorizationScopeContract (Truth-Blind Boundary Barrier)║
       ║                                                               ║
       ║  Reasoning Input Envelopes [Phase 1b]                         ║
       ║  ├── TemporalContextContract  ──► Time window, freshness decay║
       ║  ├── TopologyContextContract  ──► Authorized causal subgraph  ║
       ║  └── ChangeContextContract    ──► Maintenance windows, CRs    ║
       ╚═══════════════════════════════╤═══════════════════════════════╝
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │ typed parameters                                    │ context presented to
            ▼                                                     ▼
 ┌─────────────────────────┐                            ┌──────────────────┐
 │   CORRELATION ENGINE    │                            │     Z A K I      │
 │                         │                            │  Cognitive Agent │
 │ • 2.1 Temporal Normaliz.│                            └─────────┬────────┘
 │ • 2.2 Topology Inversion│                                      │
 │ • 2.3 10-Pathway Spine  │                                      ▼ operates on
 │ • 2.4 Blast Radius Det. │                            ┌──────────────────┐
 └──────────┬──────────────┘                            │ IncidentContract │ [Phase 1a]
            │                                           │  (ITSM Ticket)   │
            ▼ produces                                  └─────────┬────────┘
 ┌─────────────────────────┐                                      ▼ referenced by
 │    CorrelationResult    │ ───► populates ──────────► ┌──────────────────┐
 └─────────────────────────┘                            │ IncidentContext  │
                                                        └─────────┬────────┘
                                                                  ▼ dispatches
                                                        ┌──────────────────┐
                                                        │   TaskEpisode    │ [Phase 3]
                                                        │ (Cognitive Spine)│
                                                        └─────────┬────────┘
                                                                  ▼
                                                               OUTCOME
                                                                  │
                                                                  ▼
                                                               LEARNING      [Phase 4]
                                                                  │ promotion
                                                                  ▼
                                                        FIKRACORE (Updated)

 ═══════════════════════════════════════════════════════════════════════════════════
  CROSS-CUTTING COGNITIVE FABRIC: Multimodal Interaction & War Room Intelligence
 ═══════════════════════════════════════════════════════════════════════════════════
       ┌──────────────────────────────────────────────────────────────────┐
       │                    CuratedResponseContract                       │
       │  • Governed by BehaviorContract & ProsodyContract                │
       │  • Dual-Channel: Acoustic Speech (≤35w) + Console Markdown Tables│
       │  • Anti-Readout Certification & Collegial Rapport Handshake      │
       └──────────────────────────────────────────────────────────────────┘
       ┌──────────────────────────────────────────────────────────────────┐
       │            Advanced Cognitive War Room Intelligence [Phase 3b]   │
       │  • ExecutiveBriefingContract       (C-Suite SLAs & Revenue Risk) │
       │  • CounterfactualScenarioContract  (What-If & N-1/N-2 Cascades)  │
       │  • TopologyProjectionContract      (Heatmap Overlays on Map UI)  │
       │  • WarRoomDiscussionContract       (Multi-SME Debate Arbitration)│
       └──────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases & Prioritization Matrix

> **Note on Phase 1:** **Phase 1a and Phase 1b are 100% independent and parallelizable.** They share zero files, zero imports, and zero schema couplings. They can be executed concurrently or in either order.

| Phase | Milestone | Scope & Core Deliverables | Urgency / Trigger Condition | Code Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1a** | **Incident Decoupling** | Extract `IncidentContract` (trouble ticket entity) from `IncidentContextContract` (workspace). | **Immediate.** Eliminates domain conflation between ticket record and cognitive workspace. | `zaki/contracts/incident.py`<br>`zaki/contracts/incident_record.py` |
| **Phase 1b** | **Reasoning Input Envelopes** | Create `TemporalContextContract`, `TopologyContextContract`, and `ChangeContextContract`; pass as typed inputs to `CorrelationEngine`. | **Immediate.** Replaces ad-hoc loose lists and unconstrained `CanonicalKnowledge` with typed contracts feeding Phases 2.1, 2.2, and Pathway 5. | `correlation/engine.py`<br>`correlation/temporal_identity.py`<br>`correlation/topological.py`<br>`investigator.py` |
| **Fabric** | **Humane Interaction Envelope** | Implement `CuratedResponseContract` in cross-cutting fabric, formalizing the output of `dispatch_intent_contract()` across voice and UI console. | **Immediate / High.** Guarantees dynamic, anti-readout, empathetic speech delivery and eliminates unvalidated string returns. | `zaki/contracts/curated_response.py`<br>`zaki/contracts/intent_dispatcher.py`<br>`zaki/contracts/prosody.py` |
| **Phase 2** | **Truth-Blind Boundary & Scope** | Formalize `AuthorizationScopeContract` (Safety Boundary) and `ContextIdentityContract` (Session metadata). | **High (for Safety Barrier)** / Low (for Identity metadata). Guarantees zero ground-truth leakage into prompts. | `zaki/contracts/operational_context.py` |
| **Phase 3a** | **Typed TaskEpisode Sub-Contracts** | Promote internal dictionaries in `TaskEpisodeContract` to discrete models (`ActionProposalContract`, `ApprovalContract`, `TaskOutcomeContract`). | **Gated.** Triggered when Multi-Agent Specialist Roles or HITL MCP tools require standalone schema interfaces. | `zaki/contracts/task_episode.py` |
| **Phase 3b** | **360° War Room Intelligence** | Formalize `ExecutiveBriefingContract`, `CounterfactualScenarioContract`, `TopologyProjectionContract`, and `WarRoomDiscussionContract`. | **Gated.** Triggered when war-room collaborative bridging, executive queries, or what-if simulations are integrated. | `zaki/contracts/executive_briefing.py`<br>`zaki/contracts/counterfactual.py`<br>`zaki/contracts/topology_projection.py`<br>`zaki/contracts/war_room.py` |
| **Phase 4** | **Closed-Loop Learning Promotion** | Build `LearningPromotionContract` and gbrain promotion pipeline from verified episode outcomes back to FikraCore. | **Future.** Requires stable, validated runtime contracts across preceding phases. | `gbrain_mcp_client.py`<br>`simulator/story_compiler.py` |

---

## 4. Detailed Implementation Anchor Specifications

### Phase 1a: Incident Decoupling (`IncidentContract` vs `IncidentContextContract`)
* **Files Affected**:
  - Create: `services/agents/src/zaki/contracts/incident_record.py`
  - Modify: `services/agents/src/zaki/contracts/incident.py`
  - Modify: `services/agents/src/zaki/contracts/intent_dispatcher.py` (`IncidentContractHandler`)
* **`IncidentContract` Schema**:
  - `incident_id: str`, `ticket_number: Optional[str]`, `title: str`, `severity: str` (P1–P4), `category: str`, `status: str` (OPEN, INVESTIGATING, MITIGATED, RESOLVED).
  - Source system provenance: `source_system: str` (`ServiceNow`, `Netcool`, `SimulatedRun`), `opened_at: datetime`, `target_sla_resolution: Optional[datetime]`.
  - Primary service jurisdiction: `jurisdiction_domain: str` (`IP_TRANSPORT`, `5G_CORE`, `RAN`).
* **`IncidentContextContract` Refactor**:
  - Remove ticket fields (`title`, `status`) which conflated the ticket with working memory.
  - Add explicit reference: `incident: Optional[IncidentContract] = None` and `incident_ref: str`.
  - Retain purely diagnostic working memory: `current_stage`, `ranked_hypotheses`, `blast_radius`, `service_impact`, `active_evidence_window`.

---

### Phase 1b: Reasoning Input Envelopes (Correlation Engine Feeds)
* **Creation & Instantiation Point**:
  - Instantiated in `Investigator.investigate()` during Stage 1 Ingestion, assembling the inputs before invoking the Correlation Engine.
* **Contracts & Replacement Mapping**:
  1. **`TemporalContextContract`**:
     - *Wraps / Replaces*: Raw `min_t`, `max_t`, and ad-hoc sliding window calculation in `investigator.py:L52–L55`.
     - *Fields*: `window_start: datetime`, `window_end: datetime`, `time_span_seconds: float`, `freshness_half_life_hours: float = 4.0`, `raw_events: list[Evidence]`.
     - *Consumer*: Feeds `Phase 2.1 (normalize_evidence)`.
  2. **`TopologyContextContract`**:
     - *Wraps / Replaces*: Unconstrained `CanonicalKnowledge` passing into topological builder. Restricts graph traversal to authorized nodes.
     - *Fields*: `authorized_nodes: set[str]`, `known_relationships: dict[str, Relationship]`, `adjacency_matrix: Optional[dict]`, `graph_version: str`.
     - *Consumer*: Feeds `Phase 2.2 (build_knowledge_graph)` and `Phase 2.4 (analyze_blast_radius)`.
  3. **`ChangeContextContract`**:
     - *Wraps / Replaces*: Loose `changes` evidence queries in `investigator.py`.
     - *Fields*: `recent_change_requests: list[dict]`, `active_maintenance_windows: list[dict]`, `recent_config_commits: list[dict]`.
     - *Consumer*: Feeds `Phase 2.3 (Pathway 5: Change & Configuration)` and equation `change_relevance` ($+0.01$).
* **Updated `CorrelationEngine.run()` Signature**:
  ```python
  def run(
      self,
      temporal_context: TemporalContextContract,
      topology_context: TopologyContextContract,
      change_context: ChangeContextContract,
      step_callback: Optional[Callable] = None,
  ) -> CorrelationResult:
  ```

---

### Cross-Cutting Fabric: Humane Interaction (`CuratedResponseContract`)
* **Creation Point**: `services/agents/src/zaki/contracts/curated_response.py`
* **Purpose**: Encapsulates Zaki's dual-channel communication act, ensuring every spoken delivery sounds natural and humane (Senior NOC Lead persona) while presenting dense technical evidence in the console.
* **Schema**:
  - `response_id: str`, `intent: str`, `target_persona: str = "SENIOR_TELECOM_NOC_LEAD"`, `tone_profile: str` (`EMPATHETIC_COLLEGIAL`, `CALM_AUTHORITY`, `RAPID_TRIAGE`).
  - **Acoustic Speech Channel**:
    - `spoken_briefing: str`: Governed by `ProsodyContract` (max 2 sentences, ≤ 35 words, acoustic breathing pauses `...`).
    - `speaking_rate_wpm: int = 155`, `tts_voice_id: str = "bm_george"`.
    - `phonetic_expansions_applied: List[str]` (e.g. `["UPF -> U-P-F", "SCTP -> S-C-T-P"]`).
  - **Console Visual Channel**:
    - `visual_markdown: str`: Dense tabular evidence, graph markdown, and ASCII/Mermaid call-flows.
    - `highlighted_entities: List[str]`: Primary network elements to focus on the topology canvas.
  - **Interactivity & Safeguards**:
    - `collegial_prompt: str`: Conversational next-step inquiry (e.g. *"Shall I pull SCTP traces, or review blast radius first?"*).
    - `anti_readout_certified: bool = True`: Hard assertion that raw JSON/tables/UUIDs are absent from the speech payload.
    - `grounded_in_contract_ref: str`: Domain contract ID supplying truth.

---

### Phase 2: Truth-Blind Safety Barrier & Session Metadata
* **`AuthorizationScopeContract` (High Urgency Safety Barrier)**:
  - *Purpose*: The cryptographic/epistemic barrier preventing simulated ground truth from leaking into prompts or agent tool queries.
  - *Fields*: `visible_entity_slugs: set[str]`, `authorized_domains: set[str]`, `human_sme_role: str`, `ground_truth_redacted: bool = True`.
* **`ContextIdentityContract` & `OperationalModeContract` (Session Metadata)**:
  - *Fields*: `context_id: str`, `version: str`, `created_at: datetime`, `execution_mode: str` (`PRODUCTION`, `SIMULATION`, `CANARY`), `run_id: str`.

---

### Phase 3a: Typed TaskEpisode Sub-Contracts
* **Trigger Condition**: Gated on the creation of Multi-Agent Specialist Roles (e.g. Transport SME, Core SME) or external HITL approval MCP tools.
* **Models Promoted**:
  - `ActionProposalContract` & `ActionExecutionContract`: Remediation and rollback steps.
  - `HumanInteractionContract` & `ApprovalContract`: SME digital sign-offs, overrides, and authority gates.
  - `TaskOutcomeContract`: Evaluates hypothesis validity, service recovery verification, and residual impact.

---

### Phase 3b: 360° War Room & Cognitive Intelligence Contracts
* **Trigger Condition**: Gated on the integration of live crisis bridge participation, executive stakeholder reporting, and What-If contingency analysis.
* **Contracts Specified**:
  1. **`ExecutiveBriefingContract` (`zaki/contracts/executive_briefing.py`)**:
     - *Executive & Business Lens*: Translates technical degradation into C-suite KPIs.
     - *Fields*: `business_impact_summary` (plain-language), `revenue_at_risk_per_hour`, `regulatory_reporting_countdown` (e.g. FCC/TRA 60-min clock), `sla_penalty_exposure`, `public_relations_risk`.
  2. **`CounterfactualScenarioContract` (`zaki/contracts/counterfactual.py`)**:
     - *Worst-Case & What-If Cascades*: Solves N-1 $\to$ N-2 contingency scenarios.
     - *Fields*: `contingency_hypothesis` (e.g. *"If secondary spine SW-02 fails while primary is isolated"*), `cascade_probability`, `worst_case_blast_radius`, `preemptive_safeguards`.
  3. **`TopologyProjectionContract` (`zaki/contracts/topology_projection.py`)**:
     - *Incident Projection Over Topology*: Binds diagnostic inference directly to UI canvas rendering.
     - *Fields*: `node_heat_levels: dict[str, str]` (`FAULT_ORIGIN`, `IMPACTED`, `AT_RISK_SHADOW`, `HEALTHY_BYPASS`), `link_saturation_vectors`, `suggested_viewport_focus`.
  4. **`WarRoomDiscussionContract` (`zaki/contracts/war_room.py`)**:
     - *Multi-Turn Bridge Dialogue & Arbitration*: Participates as an objective peer in multi-engineer war rooms.
     - *Fields*: `differing_hypotheses: list[dict]` (tracks Engineer A vs Engineer B theories), `unbiased_arbitration` (telemetry evidence weighing), `consensus_status`.

---

### Phase 4: Closed-Loop Knowledge Promotion to FikraCore
* **Trigger Condition**: Gated on stabilization of Phases 1 through 3.
* **Deliverables**:
  - `LearningPromotionContract`: Captures extracted operational signatures (`learned_pattern`) from successful task episodes.
  - Promotion pipeline and gating validation writing back to `gbrain` active snapshot.
