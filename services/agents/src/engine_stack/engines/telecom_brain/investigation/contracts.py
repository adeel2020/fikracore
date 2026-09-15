"""Strict operational contracts; no simulator world or answer labels are accepted."""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, AwareDatetime


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Terminal(str, Enum):
    EXPLAINED = "EXPLAINED"
    PARTIALLY_EXPLAINED = "PARTIALLY_EXPLAINED"
    UNRESOLVED = "UNRESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    MODEL_INSUFFICIENT = "MODEL_INSUFFICIENT"


class KnowledgeState(str, Enum):
    CONFIRMED = "CONFIRMED"
    SUPPORTED = "SUPPORTED"
    INFERRED = "INFERRED"
    CANDIDATE = "CANDIDATE"
    REJECTED = "REJECTED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class CausalRole(str, Enum):
    ROOT = "ROOT"
    TRIGGER = "TRIGGER"
    CONTRIBUTING_CONDITION = "CONTRIBUTING_CONDITION"
    PROPAGATION_MECHANISM = "PROPAGATION_MECHANISM"
    AMPLIFIER = "AMPLIFIER"
    SYMPTOM = "SYMPTOM"
    COINCIDENTAL = "COINCIDENTAL"
    UNKNOWN = "UNKNOWN"


class GeneratedRunInput(Contract):
    run_id: str
    scenario_id: str
    difficulty_profile: Literal["L1", "L2", "L3", "L4", "L5"]
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


class Evidence(Contract):
    evidence_id: str
    event_time: AwareDatetime
    ingestion_time: AwareDatetime
    domain: str
    entity: str
    canonical_entity: str
    entity_type: str = "unknown"
    service: list[str] = Field(default_factory=list)
    evidence_type: str
    value: Any = None
    signal: str = ""
    source: str
    source_vendor: str = "unknown"
    source_native_entity: str
    source_reliability: float = Field(default=0.5, ge=0, le=1)
    freshness: float = Field(default=1, ge=0, le=1)
    observed_or_inferred: Literal["OBSERVED", "INFERRED", "CONFIRMED", "REJECTED"] = "OBSERVED"
    polarity: Literal["abnormal", "healthy", "context", "unknown"] = "unknown"
    severity: str = "UNKNOWN"
    observed_path: list[str] = Field(default_factory=list)
    duplicate_ids: list[str] = Field(default_factory=list)


class Relationship(Contract):
    relationship_id: str
    source: str
    target: str
    link_type: str
    state: KnowledgeState = KnowledgeState.UNKNOWN
    confidence: float = Field(default=0.5, ge=0, le=1)
    provenance: str = "operational-provider"


class Assumption(Contract):
    statement: str
    state: Literal["CONFIRMED", "SUPPORTED", "UNCERTAIN", "UNTESTED", "CONTRADICTED", "REJECTED"]
    evidence_ids: list[str] = Field(default_factory=list)


class Hypothesis(Contract):
    hypothesis_id: str
    statement: str
    candidate_root_domain: str
    candidate_root_entity: str
    canonical_root_entity: str
    root_entities: list[str]
    causal_role: CausalRole
    assumptions: list[Assumption]
    expected_observations: list[str]
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    missing_evidence: list[str]
    knowledge_relationships_used: list[str]
    status: KnowledgeState
    hypothesis_confidence: float
    causal_confidence: float
    explanation_coverage: float
    score_dimensions: dict[str, float]
    failed_assumptions: list[str] = Field(default_factory=list)


class EvidenceRequest(Contract):
    request_id: str
    question: str
    target_entities: list[str]
    discriminates: list[str]
    information_gain: float
    cost: float = 1
    latency: float = 1
    risk: float = 0
    reliability: float = 0.9
    availability: float = 1
    priority: float


class CandidateRelationship(Contract):
    candidate_id: str
    source: str
    target: str
    proposed_type: str = "connected-to"
    state: KnowledgeState = KnowledgeState.CANDIDATE
    supporting_evidence: list[str]
    reason: str


class InvestigationResult(Contract):
    run_id: str
    scenario_id: str
    terminal_state: Terminal
    ranked_hypotheses: list[Hypothesis]
    selected_hypothesis_id: str | None
    supporting_evidence: list[str]
    contradicting_evidence: list[str]
    missing_evidence: list[str]
    explanation_coverage: float
    unexplained_observations: list[str]
    knowledge_gaps: list[str]
    candidate_relationships: list[CandidateRelationship]
    canonical_entities_used: list[str]
    reasoning_summary: str
    provenance: list[dict[str, Any]]
    next_best_evidence: list[EvidenceRequest]
    discovery_mode: bool
    causal_event_graph: list[dict[str, Any]]
    metadata: dict[str, Any]
    diagnostics: dict[str, Any]

    @property
    def unexplained_residuals(self) -> list[Any]:
        return self.diagnostics.get("unexplained_residuals", self.unexplained_observations)



class ValidationDecision(Contract):
    candidate: CandidateRelationship
    validator: str = Field(min_length=1)
    decision: Literal["validate", "reject"]
    reason: str = Field(min_length=1)
    timestamp: AwareDatetime


# ==========================================
# STEP 4.2 / H2 CONTRACTS
# ==========================================

class KnowledgeGapType(str, Enum):
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    MISSING_INTERMEDIATE_NODE = "MISSING_INTERMEDIATE_NODE"
    MISSING_SHARED_DEPENDENCY = "MISSING_SHARED_DEPENDENCY"
    MISSING_SERVICE_TO_FUNCTION = "MISSING_SERVICE_TO_FUNCTION"
    MISSING_FAILURE_DOMAIN_MEMBERSHIP = "MISSING_FAILURE_DOMAIN_MEMBERSHIP"
    MISSING_HOSTING_CONTAINER = "MISSING_HOSTING_CONTAINER"
    MISSING_TRANSPORT_PATH = "MISSING_TRANSPORT_PATH"
    MISSING_EXTERNAL_DEPENDENCY = "MISSING_EXTERNAL_DEPENDENCY"
    STALE_TOPOLOGY_RELATIONSHIP = "STALE_TOPOLOGY_RELATIONSHIP"
    WRONG_TOPOLOGY_DIRECTION = "WRONG_TOPOLOGY_DIRECTION"
    INCORRECTLY_MERGED_ENTITIES = "INCORRECTLY_MERGED_ENTITIES"
    ALIAS_CANONICAL_AMBIGUITY = "ALIAS_CANONICAL_AMBIGUITY"
    MISSING_REDUNDANCY_FAILOVER = "MISSING_REDUNDANCY_FAILOVER"
    MISSING_MONITORING_DEPENDENCY = "MISSING_MONITORING_DEPENDENCY"
    MISSING_DB_CACHE_MESSAGE_BUS = "MISSING_DB_CACHE_MESSAGE_BUS"
    MISSING_POWER_ENVIRONMENT = "MISSING_POWER_ENVIRONMENT"
    MISSING_ROAMING_INTERCONNECT = "MISSING_ROAMING_INTERCONNECT"
    MISSING_PROVISIONING_BSS = "MISSING_PROVISIONING_BSS"
    MISSING_SECURITY_CONTROL = "MISSING_SECURITY_CONTROL"
    MULTIPLE_SIMULTANEOUS_GAPS = "MULTIPLE_SIMULTANEOUS_GAPS"


class SuspectedMissingRelation(Contract):
    from_entity: str
    relation: str = "ROUTES_THROUGH"
    to_entity: str | None = None


class KnowledgeGap(Contract):
    gap_id: str
    gap_type: KnowledgeGapType
    status: KnowledgeState = KnowledgeState.CANDIDATE
    affected_entities: list[str] = Field(default_factory=list)
    suspected_missing_relation: SuspectedMissingRelation
    reason: str
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    unexplained_residual: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.64, ge=0, le=1)
    required_validation: bool = True
    display_name: str = ""


class UnexplainedResidual(Contract):
    residual_id: str
    evidence_ids: list[str]
    affected_services: list[str] = Field(default_factory=list)
    known_path_exhausted_at: str
    severity: float = Field(default=0.5, ge=0, le=1)
    structural_suspicion: bool = True


class ModelContradiction(Contract):
    contradiction_id: str
    expected_behavior: str
    observed_behavior: str
    evidence_ids: list[str] = Field(default_factory=list)
    severity: float = Field(default=0.5, ge=0, le=1)


class NextBestEvidenceRequest(Contract):
    request_id: str
    question: str
    evidence_type: str = "TOPOLOGY_NEIGHBOR"
    target: str
    expected_information_gain: float = Field(default=0.8, ge=0, le=1)
    cost: float = Field(default=0.2, ge=0)
    risk: float = Field(default=0.05, ge=0, le=1)
    latency: float = Field(default=1.0, ge=0)
    reliability: float = Field(default=0.9, ge=0, le=1)
    availability: float = Field(default=1.0, ge=0, le=1)
    priority: float
    hypotheses_discriminated: list[str] = Field(default_factory=list)


class CuratedDemoMetadata(Contract):
    enabled: bool = True
    title: str
    audience: str = "leadership"
    duration_minutes: int = 4
    learning_objective: str
    steps: list[str] = Field(default_factory=list)
    final_message: str


class StandardPresentationModel(Contract):
    scenario: dict[str, Any]
    impact: dict[str, Any]
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    topology: dict[str, Any] = Field(default_factory=dict)
    reasoning: dict[str, Any] = Field(default_factory=dict)
    next_best_evidence: list[dict[str, Any]] = Field(default_factory=list)
    candidate_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    validation: dict[str, Any] = Field(default_factory=dict)
    presentation: dict[str, Any] = Field(default_factory=dict)
    learning: dict[str, Any] | None = None
    resilience: dict[str, Any] | None = None
    knowledge_inventory: dict[str, Any] | None = None
    session: dict[str, Any] | None = None


class SharedStructuredState(Contract):
    """Unified Shared Structured State Contract (§55).
    
    Powers CLI, Simulator UI, Curated Demo Mode, Mark / Zaki, and API identically.
    """
    session: dict[str, Any] = Field(default_factory=dict)
    scenario: dict[str, Any] = Field(default_factory=dict)
    capability: dict[str, Any] = Field(default_factory=dict)
    impact: dict[str, Any] = Field(default_factory=dict)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    topology: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: dict[str, Any] = Field(default_factory=dict)
    knowledge_gap: dict[str, Any] = Field(default_factory=dict)
    learning: dict[str, Any] = Field(default_factory=dict)
    resilience: dict[str, Any] = Field(default_factory=dict)
    knowledge_inventory: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    presentation: dict[str, Any] = Field(default_factory=dict)


class ZakiContextContract(Contract):
    active_scenario: str
    active_stage: str = "H2"
    active_presentation_mode: Literal["INVESTIGATION", "DEMO"] = "INVESTIGATION"
    current_presentation_step: int = 1
    visible_evidence: list[dict[str, Any]] = Field(default_factory=list)
    visible_topology: dict[str, Any] = Field(default_factory=dict)
    current_hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    current_terminal_state: str = "MODEL_INSUFFICIENT"
    knowledge_gap_state: dict[str, Any] = Field(default_factory=dict)
    next_best_evidence: list[dict[str, Any]] = Field(default_factory=list)
    candidate_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    validation_status: str = "PENDING"
    human_readable_display_names: dict[str, str] = Field(default_factory=dict)
    learning_state: dict[str, Any] | None = None
    resilience_state: dict[str, Any] | None = None


# --- Step 4.3 / H3 Validated Knowledge Learning & Promotion Contracts ---


class ValidationDecisionType(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"


class KnowledgePromotionState(str, Enum):
    CANDIDATE = "CANDIDATE"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATED = "VALIDATED"
    PROMOTED = "PROMOTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    STALE = "STALE"
    CONTRADICTED = "CONTRADICTED"
    REVOKED = "REVOKED"


class ValidationRecord(Contract):
    validation_id: str
    candidate_id: str
    decision: ValidationDecisionType
    validated_by_role: str = "Transport Domain SME"
    reason: str
    timestamp: AwareDatetime
    evidence_refs: list[str] = Field(default_factory=list)
    modified_relation: dict[str, Any] | None = None


class PromotionRecord(Contract):
    promotion_id: str
    candidate_id: str
    validation_id: str
    canonical_from: str
    relation: str
    canonical_to: str
    display_from: str
    display_relation: str
    display_to: str
    status: KnowledgePromotionState = KnowledgePromotionState.PROMOTED
    provenance: dict[str, Any] = Field(default_factory=dict)
    rollback_supported: bool = True


class LearningLedgerEntry(Contract):
    knowledge_id: str
    display_name: str
    canonical_from: str
    relation: str
    canonical_to: str
    state: KnowledgePromotionState
    discovered_in: str
    validated_by: str
    reused_in: list[str] = Field(default_factory=list)
    helpful_reuse_count: int = 0
    harmful_reuse_count: int = 0
    last_verified_at: AwareDatetime


class LearningUnit(Contract):
    learning_unit_id: str
    cohort: str  # positive_transfer, cross_domain_transfer, stale_topology, poisoned_validation
    discovery_incident: str
    candidate_knowledge_id: str
    validation_decision: ValidationDecisionType
    promoted_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    future_incident: str
    expected_learning_value: str


class LearningPerformanceDelta(Contract):
    learning_unit_id: str
    cohort: str
    root_cause_rank_before: int | None = None
    root_cause_rank_after: int | None = None
    rank_improvement: int = 0
    terminal_state_before: str
    terminal_state_after: str
    explanation_coverage_before: float = 0.0
    explanation_coverage_after: float = 0.0
    evidence_requests_count_before: int = 0
    evidence_requests_count_after: int = 0
    knowledge_reused: bool = False
    learning_value_score: float = 0.0
    negative_transfer_flag: bool = False
    stale_detected_flag: bool = False
    contradiction_flag: bool = False


# --- Step 4.4 / H4 Proactive What-If & Resilience Contracts ---


class BlastRadiusLevel(str, Enum):
    LOCAL = "LOCAL"
    DOMAIN = "DOMAIN"
    MULTI_DOMAIN = "MULTI_DOMAIN"
    REGIONAL = "REGIONAL"
    NETWORK_WIDE = "NETWORK_WIDE"


class PropagationSemantics(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    REDUNDANT = "REDUNDANT"
    CAPACITY = "CAPACITY"
    CONTROL_PLANE = "CONTROL_PLANE"
    MONITORING = "MONITORING"
    OPTIONAL = "OPTIONAL"


class ResilienceActionCategory(str, Enum):
    OBSERVATION = "OBSERVATION"
    RISK = "RISK"
    CANDIDATE_ACTION = "CANDIDATE_ACTION"
    VALIDATED_ACTION = "VALIDATED_ACTION"


class WhatIfTrigger(Contract):
    entity_display_name: str
    canonical_id: str
    event_type: str = "FAILURE"  # FAILURE, DEGRADATION, REBOOT, CONFIG_CHANGE
    severity: str = "CRITICAL"


class WhatIfAssumptions(Contract):
    failover_available: bool = True
    failover_capacity: str = "FULL"  # FULL, LIMITED, NONE
    duration_minutes: int = 30
    traffic_load_profile: str = "NORMAL"  # NORMAL, PEAK, SURGE


class WhatIfScenario(Contract):
    what_if_id: str
    title: str
    trigger: WhatIfTrigger
    assumptions: WhatIfAssumptions
    cohort: str = "single_point_failure"
    failure_domain_tags: list[str] = Field(default_factory=list)


class PropagationPathStep(Contract):
    step_index: int
    from_entity: str
    from_canonical_id: str
    relation: str
    relation_semantics: str = "HARD"
    to_entity: str
    to_canonical_id: str
    impact_severity: str = "CRITICAL"
    explanation: str = ""


class BlastRadiusAssessment(Contract):
    directly_affected_entities: list[str] = Field(default_factory=list)
    indirectly_affected_entities: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    affected_domains: list[str] = Field(default_factory=list)
    affected_regions: list[str] = Field(default_factory=list)
    blast_radius_level: BlastRadiusLevel = BlastRadiusLevel.LOCAL
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    customer_facing_impact: str = ""


class CriticalFailureSurface(Contract):
    surface_id: str
    components: list[str] = Field(default_factory=list)
    risk_type: str = "SPOF"  # SPOF, SHARED_DEPENDENCY, FAILOVER_BOTTLENECK, CAPACITY_EXHAUSTION, COMMON_POWER, COMMON_TRANSPORT
    dependent_services: list[str] = Field(default_factory=list)
    criticality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""


class ResilienceGap(Contract):
    gap_id: str
    type: str
    primary_entity: str
    backup_entity: str | None = None
    risk: str
    severity: str = "HIGH"
    recommended_action: str


class MitigationOption(Contract):
    option_id: str
    title: str
    description: str
    risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0)
    protected_services: list[str] = Field(default_factory=list)
    implementation_complexity: str = "LOW"  # LOW, MEDIUM, HIGH
    operational_disruption: str = "NONE"   # NONE, MINIMAL, DISRUPTIVE
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ResilienceRecommendation(Contract):
    recommendation_id: str
    category: ResilienceActionCategory = ResilienceActionCategory.CANDIDATE_ACTION
    title: str
    action: str
    priority: str = "HIGH"
    expected_risk_reduction: float = Field(default=0.0, ge=0.0, le=1.0)
    target_entity: str


class WhatIfSimulationResult(Contract):
    what_if_id: str
    terminal_state: Terminal = Terminal.EXPLAINED
    trigger: WhatIfTrigger
    assumptions: WhatIfAssumptions
    propagation_paths: list[list[PropagationPathStep]] = Field(default_factory=list)
    blast_radius: BlastRadiusAssessment
    critical_failure_surfaces: list[CriticalFailureSurface] = Field(default_factory=list)
    resilience_gaps: list[ResilienceGap] = Field(default_factory=list)
    mitigation_options: list[MitigationOption] = Field(default_factory=list)
    recommended_actions: list[ResilienceRecommendation] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    knowledge_limitations: list[str] = Field(default_factory=list)



