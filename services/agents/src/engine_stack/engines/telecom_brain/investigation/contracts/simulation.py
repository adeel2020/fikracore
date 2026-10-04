"""
Simulation, Presentation, & What-If Resilience Contracts
=========================================================
This module defines the runtime state contracts, presentation models, and proactive
What-If resilience evaluation engines in FikraCore and Zaki.

Key Architectural Components:
1. Knowledge Gaps (§Step 4.2 / H2):
   Formal categorization of missing topology paths, unmapped dependencies,
   and structural contradictions between observed symptoms and graph models.
2. Presentation & State (§55 Unified State):
   `SharedStructuredState`, `StandardPresentationModel`, and `ZakiContextContract`
   ensuring the CLI, Simulator UI, Demo Mode, and Zaki share identical synchronized state.
3. Proactive What-If & Resilience (§Step 4.4 / H4):
   Evaluates single points of failure (SPOF), propagation paths across redundancy
   boundaries, and generates actionable resilience recommendations.
"""

from enum import Enum
from typing import Any, Literal
from pydantic import Field
from .base import Contract, KnowledgeState, Terminal
from .topology import BlastRadiusLevel, BlastRadiusAssessment


# =========================================================================
# Knowledge Gap & Residual Contracts (Step 4.2 / H2)
# =========================================================================

class KnowledgeGapType(str, Enum):
    """
    Taxonomy of structural knowledge deficits in the network topology graph.
    Identifies why an observed symptom cannot be explained by known adjacency models.
    """
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"                                 # Missing functional or service-to-node link
    MISSING_INTERMEDIATE_NODE = "MISSING_INTERMEDIATE_NODE"                   # Missing transit switch, firewall, or gateway
    MISSING_SHARED_DEPENDENCY = "MISSING_SHARED_DEPENDENCY"                   # Unrecognized shared fate (e.g. common line card)
    MISSING_SERVICE_TO_FUNCTION = "MISSING_SERVICE_TO_FUNCTION"               # Unmapped relationship between service and VNF
    MISSING_FAILURE_DOMAIN_MEMBERSHIP = "MISSING_FAILURE_DOMAIN_MEMBERSHIP"   # Missing rack, DC hall, or zone tag
    MISSING_HOSTING_CONTAINER = "MISSING_HOSTING_CONTAINER"                   # Missing hypervisor or k8s node container link
    MISSING_TRANSPORT_PATH = "MISSING_TRANSPORT_PATH"                         # Unmapped MPLS/IP transport forwarding path
    MISSING_EXTERNAL_DEPENDENCY = "MISSING_EXTERNAL_DEPENDENCY"               # Third-party DNS, NTP, roaming peer, or cloud link
    STALE_TOPOLOGY_RELATIONSHIP = "STALE_TOPOLOGY_RELATIONSHIP"               # Graph contains edge that was decommissioned
    WRONG_TOPOLOGY_DIRECTION = "WRONG_TOPOLOGY_DIRECTION"                     # Edge arrow is reversed in causal model
    INCORRECTLY_MERGED_ENTITIES = "INCORRECTLY_MERGED_ENTITIES"               # Two distinct elements collapsed into one slug
    ALIAS_CANONICAL_AMBIGUITY = "ALIAS_CANONICAL_AMBIGUITY"                   # Vendor native name maps to multiple canonical slugs
    MISSING_REDUNDANCY_FAILOVER = "MISSING_REDUNDANCY_FAILOVER"               # Missing HA standby or secondary bypass path
    MISSING_MONITORING_DEPENDENCY = "MISSING_MONITORING_DEPENDENCY"           # Unmapped telemetry probe attachment
    MISSING_DB_CACHE_MESSAGE_BUS = "MISSING_DB_CACHE_MESSAGE_BUS"             # Unmapped backend database/Kafka bus dependency
    MISSING_POWER_ENVIRONMENT = "MISSING_POWER_ENVIRONMENT"                   # Unmapped UPS, generator, or HVAC dependency
    MISSING_ROAMING_INTERCONNECT = "MISSING_ROAMING_INTERCONNECT"             # Unmapped GRX/IPX international interconnect
    MISSING_PROVISIONING_BSS = "MISSING_PROVISIONING_BSS"                     # Unmapped order entry / provisioning pipe
    MISSING_SECURITY_CONTROL = "MISSING_SECURITY_CONTROL"                     # Unmapped security firewall or SEPP filter
    MULTIPLE_SIMULTANEOUS_GAPS = "MULTIPLE_SIMULTANEOUS_GAPS"                 # Compound gap spanning multiple categories


class SuspectedMissingRelation(Contract):
    """
    Hypothesized missing relationship between two nodes proposed to bridge a knowledge gap.

    Attributes:
        from_entity: Canonical slug of source entity.
        relation: Proposed relationship type (default 'ROUTES_THROUGH').
        to_entity: Canonical slug of target entity (or None if unknown sink).
    """
    from_entity: str = Field(description="Canonical slug of source entity")
    relation: str = Field(default="ROUTES_THROUGH", description="Hypothesized relationship type")
    to_entity: str | None = Field(default=None, description="Hypothesized target entity slug")


class KnowledgeGap(Contract):
    """
    Formally documented topological deficit preventing complete root cause explanation.

    Attributes:
        gap_id: Unique semantic knowledge gap identifier.
        gap_type: Classification from KnowledgeGapType taxonomy.
        status: Epistemic status (default CANDIDATE).
        affected_entities: Network entities impacted by this missing knowledge.
        suspected_missing_relation: Proposed topological edge to resolve gap.
        reason: Diagnostic justification explaining why current model is insufficient.
        supporting_evidence: Evidence IDs indicating existence of the missing link.
        contradicting_evidence: Evidence IDs arguing against the proposed link.
        unexplained_residual: Symptoms that remain unexplained until this gap is resolved.
        confidence: Certainty score regarding the gap's existence.
        required_validation: Whether human SME validation is required before graph update.
        display_name: Formatted label for user interface presentation.
    """
    gap_id: str = Field(description="Unique knowledge gap identifier")
    gap_type: KnowledgeGapType = Field(description="Taxonomic classification of gap")
    status: KnowledgeState = Field(default=KnowledgeState.CANDIDATE, description="Epistemic validation state")
    affected_entities: list[str] = Field(default_factory=list, description="Entities involved in knowledge void")
    suspected_missing_relation: SuspectedMissingRelation = Field(description="Hypothesized missing link")
    reason: str = Field(description="Technical rationale for hypothesizing this gap")
    supporting_evidence: list[str] = Field(default_factory=list, description="Evidence IDs pointing to gap")
    contradicting_evidence: list[str] = Field(default_factory=list, description="Evidence IDs conflicting with gap")
    unexplained_residual: list[str] = Field(default_factory=list, description="Residual symptoms explained by this gap")
    confidence: float = Field(default=0.64, ge=0.0, le=1.0, description="Epistemic confidence in gap hypothesis")
    required_validation: bool = Field(default=True, description="Enforces SME sign-off prior to graph promotion")
    display_name: str = Field(default="", description="Display title for UI presentation")


class UnexplainedResidual(Contract):
    """
    Residual anomaly observation that cannot be accounted for by the leading hypothesis.

    Attributes:
        residual_id: Unique residual identifier.
        evidence_ids: Telemetry evidence records comprising this residual.
        affected_services: Services impacted by unexplained symptom.
        known_path_exhausted_at: Node slug where known graph traversal terminated.
        severity: Operational severity coefficient (0.0 to 1.0).
        structural_suspicion: True if symptom strongly suggests an unmapped graph edge.
    """
    residual_id: str = Field(description="Unique unexplained residual identifier")
    evidence_ids: list[str] = Field(description="Evidence IDs that cannot be causally explained")
    affected_services: list[str] = Field(default_factory=list, description="Degraded subscriber services")
    known_path_exhausted_at: str = Field(description="Canonical node where known graph traversal dead-ended")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Severity score of residual")
    structural_suspicion: bool = Field(default=True, description="Indicates strong likelihood of missing topology link")


class ModelContradiction(Contract):
    """
    Direct contradiction between observed empirical telemetry and the topology model.

    Attributes:
        contradiction_id: Unique contradiction identifier.
        expected_behavior: What the graph/protocol model predicts.
        observed_behavior: What the live telemetry actually demonstrates.
        evidence_ids: Evidence records proving the contradiction.
        severity: Diagnostic severity score.
    """
    contradiction_id: str = Field(description="Unique contradiction identifier")
    expected_behavior: str = Field(description="Behavior expected according to graph model")
    observed_behavior: str = Field(description="Actual behavior observed in telemetry")
    evidence_ids: list[str] = Field(default_factory=list, description="Evidence records demonstrating conflict")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Severity score")


class NextBestEvidenceRequest(Contract):
    """
    Calculated highest-value telemetry query to resolve current diagnostic ambiguity.

    Attributes:
        request_id: Semantic request ID.
        question: Diagnostic question to resolve.
        evidence_type: Category of observation (e.g. 'TOPOLOGY_NEIGHBOR').
        target: Target network element or interface.
        expected_information_gain: Anticipated reduction in hypothesis entropy.
        cost: Resource overhead coefficient.
        risk: Live network disturbance risk score.
        latency: Expected response latency coefficient.
        reliability: Collector reliability score.
        availability: Data source availability score.
        priority: Final composite scheduling priority.
        hypotheses_discriminated: List of hypothesis IDs separated by this query.
    """
    request_id: str = Field(description="Unique query request identifier")
    question: str = Field(description="Diagnostic question formulating measurement")
    evidence_type: str = Field(default="TOPOLOGY_NEIGHBOR", description="Target telemetry type")
    target: str = Field(description="Network node or interface target")
    expected_information_gain: float = Field(default=0.8, ge=0.0, le=1.0, description="Expected entropy reduction")
    cost: float = Field(default=0.2, ge=0.0, description="Computational or operational cost")
    risk: float = Field(default=0.05, ge=0.0, le=1.0, description="Execution risk score")
    latency: float = Field(default=1.0, ge=0.0, description="Latency coefficient")
    reliability: float = Field(default=0.9, ge=0.0, le=1.0, description="Collector reliability")
    availability: float = Field(default=1.0, ge=0.0, le=1.0, description="Target availability")
    priority: float = Field(description="Final computed priority score")
    hypotheses_discriminated: list[str] = Field(default_factory=list, description="Hypotheses resolved by this query")


# =========================================================================
# Presentation & Synchronized Shared Structured State (§55)
# =========================================================================

class CuratedDemoMetadata(Contract):
    """
    Metadata governing scripted walkthroughs in Curated Demo Mode.

    Attributes:
        enabled: Whether curated demo mode is active.
        title: Demo scenario title.
        audience: Target stakeholder group (e.g. 'leadership', 'engineering').
        duration_minutes: Target walkthrough duration.
        learning_objective: Key architectural takeaway demonstrated by scenario.
        steps: Ordered titles of the presentation steps.
        final_message: Concluding takeaway message.
    """
    enabled: bool = Field(default=True, description="Enables scripted demo guidance")
    title: str = Field(description="Demo presentation title")
    audience: str = Field(default="leadership", description="Target stakeholder audience")
    duration_minutes: int = Field(default=4, description="Target duration in minutes")
    learning_objective: str = Field(description="Pedagogical objective demonstrated")
    steps: list[str] = Field(default_factory=list, description="Sequential presentation step titles")
    final_message: str = Field(description="Closing takeaway summary")


class StandardPresentationModel(Contract):
    """
    Unified presentation model consumed by frontend visualizations and reports.

    Attributes:
        scenario: Scenario description payload.
        impact: Impact assessment dictionary.
        timeline: Sequential timeline events.
        topology: Active topology subgraph dictionary.
        reasoning: Evaluated hypotheses and confidence scores.
        next_best_evidence: Prioritized evidence requests.
        candidate_knowledge: Proposed relationships or patterns.
        validation: Review status and HITL approval states.
        presentation: Viewport and rendering layout directives.
        learning: Continuous learning deltas (optional).
        resilience: What-If simulation results (optional).
        knowledge_inventory: Active graph node/edge counts (optional).
        session: Active session metadata (optional).
    """
    scenario: dict[str, Any] = Field(description="Scenario metadata payload")
    impact: dict[str, Any] = Field(description="Impact assessment metrics")
    timeline: list[dict[str, Any]] = Field(default_factory=list, description="Timeline progression entries")
    topology: dict[str, Any] = Field(default_factory=dict, description="Visual topology subgraph")
    reasoning: dict[str, Any] = Field(default_factory=dict, description="Hypothesis reasoning payload")
    next_best_evidence: list[dict[str, Any]] = Field(default_factory=list, description="Prioritized telemetry queries")
    candidate_knowledge: list[dict[str, Any]] = Field(default_factory=list, description="Candidate discoveries")
    validation: dict[str, Any] = Field(default_factory=dict, description="Validation decisions")
    presentation: dict[str, Any] = Field(default_factory=dict, description="UI rendering directives")
    learning: dict[str, Any] | None = Field(default=None, description="Learning ledger state")
    resilience: dict[str, Any] | None = Field(default=None, description="Resilience simulation metrics")
    knowledge_inventory: dict[str, Any] | None = Field(default=None, description="Graph inventory counters")
    session: dict[str, Any] | None = Field(default=None, description="Session state dictionary")


class SharedStructuredState(Contract):
    """
    Unified Shared Structured State Contract (§55).
    Guarantees that CLI, Simulator UI, Curated Demo Mode, and Zaki interact
    over an identical, deterministic state representation.
    """
    session: dict[str, Any] = Field(default_factory=dict, description="Active user session metadata")
    scenario: dict[str, Any] = Field(default_factory=dict, description="Active scenario configuration")
    capability: dict[str, Any] = Field(default_factory=dict, description="Platform capabilities enabled")
    impact: dict[str, Any] = Field(default_factory=dict, description="Service degradation impact state")
    timeline: list[dict[str, Any]] = Field(default_factory=list, description="Chronological event journal")
    topology: dict[str, Any] = Field(default_factory=dict, description="Live network topology state")
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="Captured evidence records")
    reasoning: dict[str, Any] = Field(default_factory=dict, description="Hypothesis evaluation state")
    knowledge_gap: dict[str, Any] = Field(default_factory=dict, description="Knowledge gaps identified")
    learning: dict[str, Any] = Field(default_factory=dict, description="Knowledge promotion ledger state")
    resilience: dict[str, Any] = Field(default_factory=dict, description="What-If evaluation state")
    knowledge_inventory: dict[str, Any] = Field(default_factory=dict, description="Canonical graph inventory counts")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Audit provenance records")
    presentation: dict[str, Any] = Field(default_factory=dict, description="UI viewport controls")


class ZakiContextContract(Contract):
    """
    Operational context scaffolding envelope passed to Zaki during simulation execution.
    Provides visible telemetry and topology without exposing hidden ground truth.

    Attributes:
        active_scenario: Identifier of scenario being solved.
        active_stage: Current stage of the investigation (e.g. 'H1', 'H2', 'H3', 'H4').
        active_presentation_mode: Presentation mode ('INVESTIGATION' or 'DEMO').
        current_presentation_step: 1-indexed step in curated walkthrough.
        visible_evidence: Telemetry observations permitted to be seen at current stage.
        visible_topology: Topology nodes and edges permitted to be seen at current stage.
        current_hypotheses: Active hypotheses under consideration.
        current_terminal_state: Current diagnostic termination state.
        knowledge_gap_state: Active knowledge gaps identified.
        next_best_evidence: Prioritized evidence requests.
        candidate_knowledge: Novel candidate edges discovered.
        validation_status: HITL approval state ('PENDING', 'APPROVED', etc.).
        human_readable_display_names: Map from canonical slugs to friendly display labels.
        learning_state: Optional continuous learning metrics.
        resilience_state: Optional proactive resilience metrics.
    """
    active_scenario: str = Field(description="Scenario identifier currently being solved")
    active_stage: str = Field(default="H2", description="Active investigation stage (H1, H2, H3, H4)")
    active_presentation_mode: Literal["INVESTIGATION", "DEMO"] = Field(
        default="INVESTIGATION",
        description="Operational UI mode"
    )
    current_presentation_step: int = Field(default=1, description="Current step index in demo progression")
    visible_evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Telemetry observations authorized for Zaki's visibility"
    )
    visible_topology: dict[str, Any] = Field(
        default_factory=dict,
        description="Topology subgraph authorized for Zaki's visibility"
    )
    current_hypotheses: list[dict[str, Any]] = Field(default_factory=list, description="Active competing hypotheses")
    current_terminal_state: str = Field(default="MODEL_INSUFFICIENT", description="Current diagnostic outcome")
    knowledge_gap_state: dict[str, Any] = Field(default_factory=dict, description="Knowledge gaps uncovered")
    next_best_evidence: list[dict[str, Any]] = Field(default_factory=list, description="Recommended telemetry queries")
    candidate_knowledge: list[dict[str, Any]] = Field(default_factory=list, description="Candidate discoveries")
    validation_status: str = Field(default="PENDING", description="Human validation approval status")
    human_readable_display_names: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from canonical slugs to friendly labels"
    )
    learning_state: dict[str, Any] | None = Field(default=None, description="Learning transfer state")
    resilience_state: dict[str, Any] | None = Field(default=None, description="Resilience simulation state")


# =========================================================================
# Step 4.4 / H4 Proactive What-If & Resilience Contracts
# =========================================================================

class PropagationSemantics(str, Enum):
    """
    Mechanics of failure propagation across network relationships.
    """
    HARD = "HARD"                   # Direct physical or hard control break; failure immediately cascades
    SOFT = "SOFT"                   # Performance degradation; latency increase or jitter without total drop
    REDUNDANT = "REDUNDANT"         # Redundant link exists; failure is absorbed unless capacity is exceeded
    CAPACITY = "CAPACITY"           # Failure occurs only if diverted traffic exceeds remaining link headroom
    CONTROL_PLANE = "CONTROL_PLANE" # Signaling or routing table impact; data plane persists temporarily
    MONITORING = "MONITORING"       # Telemetry collector failure; network operational but unobservable
    OPTIONAL = "OPTIONAL"           # Non-critical auxiliary service; core connectivity unaffected


class ResilienceActionCategory(str, Enum):
    """
    Classification of resilience recommendations produced by What-If simulations.
    """
    OBSERVATION = "OBSERVATION"             # Noteworthy topological pattern or capacity observation
    RISK = "RISK"                           # Latent architectural risk or unmitigated SPOF
    CANDIDATE_ACTION = "CANDIDATE_ACTION"   # Proposed architectural or configuration enhancement
    VALIDATED_ACTION = "VALIDATED_ACTION"   # SME-approved operational hardening work order


class WhatIfTrigger(Contract):
    """
    Initial simulated failure event or perturbation initiating a What-If analysis.

    Attributes:
        entity_display_name: Display name of element being failed.
        canonical_id: Canonical slug of failed element.
        event_type: Category of failure: FAILURE, DEGRADATION, REBOOT, CONFIG_CHANGE.
        severity: Severity classification of perturbation.
    """
    entity_display_name: str = Field(description="Display label of injected failure target")
    canonical_id: str = Field(description="Canonical slug of injected failure target")
    event_type: str = Field(
        default="FAILURE",
        description="Perturbation event type: FAILURE, DEGRADATION, REBOOT, CONFIG_CHANGE"
    )
    severity: str = Field(default="CRITICAL", description="Severity tier of simulated event")


class WhatIfAssumptions(Contract):
    """
    Operating assumptions framing a What-If resilience simulation.

    Attributes:
        failover_available: Whether redundancy paths are enabled during test.
        failover_capacity: Throughput headroom on backup paths: FULL, LIMITED, NONE.
        duration_minutes: Projected duration of outage in minutes.
        traffic_load_profile: Offered subscriber load: NORMAL, PEAK, SURGE.
    """
    failover_available: bool = Field(default=True, description="Whether automated failover protection is active")
    failover_capacity: str = Field(
        default="FULL",
        description="Backup path throughput capacity: FULL, LIMITED, or NONE"
    )
    duration_minutes: int = Field(default=30, description="Simulated perturbation duration in minutes")
    traffic_load_profile: str = Field(
        default="NORMAL",
        description="Offered network traffic profile: NORMAL, PEAK, or SURGE"
    )


class WhatIfScenario(Contract):
    """
    Complete configuration specification for a proactive resilience simulation.

    Attributes:
        what_if_id: Unique scenario identifier (e.g. 'WHAT_IF_AGG01_FAILURE').
        title: Human-readable scenario title.
        trigger: The simulated initial failure trigger.
        assumptions: Baseline operating assumptions.
        cohort: Testing cohort (e.g. 'single_point_failure', 'double_link_failure').
        failure_domain_tags: Geographic or topological tags bounding the test.
    """
    what_if_id: str = Field(description="Unique What-If scenario identifier")
    title: str = Field(description="Descriptive scenario title")
    trigger: WhatIfTrigger = Field(description="Simulated failure event trigger")
    assumptions: WhatIfAssumptions = Field(description="Baseline operational assumptions")
    cohort: str = Field(
        default="single_point_failure",
        description="Resilience test cohort category"
    )
    failure_domain_tags: list[str] = Field(
        default_factory=list,
        description="Failure domain boundary tags"
    )


class PropagationPathStep(Contract):
    """
    Single step along a simulated failure cascade propagation path.

    Attributes:
        step_index: Sequential hop index (1, 2, 3...).
        from_entity: Originating entity display name.
        from_canonical_id: Originating entity canonical slug.
        relation: Edge relationship traversed.
        relation_semantics: Hard, soft, or capacity cascade mechanics.
        to_entity: Downstream entity display name.
        to_canonical_id: Downstream entity canonical slug.
        impact_severity: Impact level on downstream entity.
        explanation: Technical explanation of the failure transition.
    """
    step_index: int = Field(description="Sequential hop number in cascade")
    from_entity: str = Field(description="Originating node label")
    from_canonical_id: str = Field(description="Originating node slug")
    relation: str = Field(description="Traversed graph relationship type")
    relation_semantics: str = Field(
        default="HARD",
        description="Propagation mechanics: HARD, SOFT, REDUNDANT, CAPACITY, CONTROL_PLANE"
    )
    to_entity: str = Field(description="Downstream affected node label")
    to_canonical_id: str = Field(description="Downstream affected node slug")
    impact_severity: str = Field(default="CRITICAL", description="Severity of downstream degradation")
    explanation: str = Field(default="", description="Technical narrative of cascade step")


class CriticalFailureSurface(Contract):
    """
    Identified structural vulnerability or Single Point of Failure (SPOF) in topology.

    Attributes:
        surface_id: Unique vulnerability identifier.
        components: List of entity slugs forming the failure surface.
        risk_type: Vulnerability pattern (SPOF, SHARED_DEPENDENCY, FAILOVER_BOTTLENECK, etc.).
        dependent_services: Subscriber services dependent on this surface.
        criticality_score: Vulnerability severity score (0.0 to 1.0).
        rationale: Architectural explanation of the hazard.
    """
    surface_id: str = Field(description="Unique failure surface identifier")
    components: list[str] = Field(default_factory=list, description="Network entities comprising the vulnerability")
    risk_type: str = Field(
        default="SPOF",
        description="Risk pattern: SPOF, SHARED_DEPENDENCY, FAILOVER_BOTTLENECK, CAPACITY_EXHAUSTION, COMMON_POWER, COMMON_TRANSPORT"
    )
    dependent_services: list[str] = Field(
        default_factory=list,
        description="Subscriber services exposed to outage"
    )
    criticality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk criticality score")
    rationale: str = Field(default="", description="Technical explanation of the structural flaw")


class ResilienceGap(Contract):
    """
    A concrete gap in high availability protection or redundant failover paths.

    Attributes:
        gap_id: Unique gap identifier.
        type: Gap category (e.g. 'NO_STANDBY_ROUTER', 'ASYMMETRIC_BANDWIDTH').
        primary_entity: Primary operating entity.
        backup_entity: Configured backup entity (or None if unconfigured).
        risk: Description of operational risk exposure.
        severity: Severity rating ('CRITICAL', 'HIGH', 'MEDIUM').
        recommended_action: Specific hardening work order to close the gap.
    """
    gap_id: str = Field(description="Unique resilience gap identifier")
    type: str = Field(description="Resilience gap category")
    primary_entity: str = Field(description="Primary node or circuit slug")
    backup_entity: str | None = Field(default=None, description="Backup node slug or None if missing")
    risk: str = Field(description="Operational risk narrative")
    severity: str = Field(default="HIGH", description="Severity classification: CRITICAL, HIGH, MEDIUM")
    recommended_action: str = Field(description="Prescriptive engineering recommendation")


class MitigationOption(Contract):
    """
    Architectural or configuration change proposed to eliminate a resilience vulnerability.

    Attributes:
        option_id: Unique option identifier.
        title: Concise title of the proposed change.
        description: Implementation details and engineering scope.
        risk_reduction: Anticipated reduction in failure surface risk (0.0 to 1.0).
        protected_services: Services that gain protection from this mitigation.
        implementation_complexity: Engineering effort required ('LOW', 'MEDIUM', 'HIGH').
        operational_disruption: Expected maintenance impact ('NONE', 'MINIMAL', 'DISRUPTIVE').
        confidence: Certainty score of the risk reduction projection.
    """
    option_id: str = Field(description="Unique mitigation option identifier")
    title: str = Field(description="Title of proposed mitigation")
    description: str = Field(description="Technical implementation specification")
    risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0, description="Projected risk reduction fraction")
    protected_services: list[str] = Field(default_factory=list, description="Services fortified by mitigation")
    implementation_complexity: str = Field(
        default="LOW",
        description="Complexity rating: LOW, MEDIUM, or HIGH"
    )
    operational_disruption: str = Field(
        default="NONE",
        description="Maintenance window impact: NONE, MINIMAL, or DISRUPTIVE"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Epistemic confidence in assessment")


class ResilienceRecommendation(Contract):
    """
    Actionable work order or hardening directive produced by What-If simulation.

    Attributes:
        recommendation_id: Unique recommendation identifier.
        category: Category (OBSERVATION, RISK, CANDIDATE_ACTION, VALIDATED_ACTION).
        title: Descriptive title.
        action: Concrete operational command or configuration directive.
        priority: Scheduling urgency ('CRITICAL', 'HIGH', 'MEDIUM').
        expected_risk_reduction: Estimated risk reduction score.
        target_entity: Network node or circuit to be modified.
    """
    recommendation_id: str = Field(description="Unique recommendation identifier")
    category: ResilienceActionCategory = Field(
        default=ResilienceActionCategory.CANDIDATE_ACTION,
        description="Recommendation classification tier"
    )
    title: str = Field(description="Title of recommendation")
    action: str = Field(description="Operational procedure or configuration change to execute")
    priority: str = Field(default="HIGH", description="Priority level: CRITICAL, HIGH, MEDIUM")
    expected_risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0, description="Expected risk reduction score")
    target_entity: str = Field(description="Target network element slug")


class WhatIfSimulationResult(Contract):
    """
    Complete output artifact of a proactive What-If failure simulation.

    Attributes:
        what_if_id: Scenario identifier.
        terminal_state: Outcome of simulation traversal (EXPLAINED, PARTIALLY_EXPLAINED, etc.).
        trigger: The simulated failure event.
        assumptions: Baseline operating assumptions used.
        propagation_paths: Evaluated failure cascade paths.
        blast_radius: Total quantified blast radius.
        critical_failure_surfaces: Identified SPOFs and shared vulnerabilities.
        resilience_gaps: Missing redundancy and failover deficits.
        mitigation_options: Evaluated mitigation options.
        recommended_actions: Prescriptive hardening recommendations.
        confidence: Overall confidence in simulation fidelity.
        knowledge_limitations: Unmapped topology regions bounding simulation certainty.
    """
    what_if_id: str = Field(description="Unique What-If scenario identifier")
    terminal_state: Terminal = Field(default=Terminal.EXPLAINED, description="Diagnostic resolution state")
    trigger: WhatIfTrigger = Field(description="Perturbation trigger evaluated")
    assumptions: WhatIfAssumptions = Field(description="Operational assumptions applied")
    propagation_paths: list[list[PropagationPathStep]] = Field(
        default_factory=list,
        description="Simulated failure cascade paths"
    )
    blast_radius: BlastRadiusAssessment = Field(description="Quantified blast radius impact")
    critical_failure_surfaces: list[CriticalFailureSurface] = Field(
        default_factory=list,
        description="Identified Single Points of Failure and shared fate hazards"
    )
    resilience_gaps: list[ResilienceGap] = Field(
        default_factory=list,
        description="Concrete deficits in redundancy protection"
    )
    mitigation_options: list[MitigationOption] = Field(
        default_factory=list,
        description="Proposed mitigation options to fortify topology"
    )
    recommended_actions: list[ResilienceRecommendation] = Field(
        default_factory=list,
        description="Prescriptive engineering recommendations"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Epistemic confidence in simulation")
    knowledge_limitations: list[str] = Field(
        default_factory=list,
        description="Identified knowledge gaps that limit simulation completeness"
    )
