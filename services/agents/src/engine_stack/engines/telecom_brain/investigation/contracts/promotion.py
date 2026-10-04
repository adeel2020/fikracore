"""
Validated Knowledge Learning & Promotion Contracts
===================================================
This module defines the governance, audit ledger, and continuous learning contracts
governing the promotion of candidate operational insights into canonical gbrain knowledge.

Continuous Learning Lifecycle:
1. Validation Decision: Human SME or automated authority reviews candidate findings
   (ACCEPT, REJECT, MODIFY, NEED_MORE_EVIDENCE).
2. Promotion Record: Accepted candidate relationships and patterns are promoted to
   canonical status with immutable provenance tracking and rollback capability.
3. Learning Ledger & Performance Delta: Quantifies positive vs negative knowledge transfer,
   tracking whether promoted knowledge accelerates future incident triage or introduces
   harmful negative transfer.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import Field
from .base import Contract


class ValidationDecisionType(str, Enum):
    """
    Formal decision rendered by a human SME or authorized agent reviewing candidate knowledge.
    """
    ACCEPT = "ACCEPT"                           # Candidate accepted as canonical truth without modification
    REJECT = "REJECT"                           # Candidate determined to be incorrect, spurious, or misleading
    MODIFY = "MODIFY"                           # Candidate accepted with manual parameter or relation adjustments
    NEED_MORE_EVIDENCE = "NEED_MORE_EVIDENCE"   # Review paused; further discrimination telemetry required


class KnowledgePromotionState(str, Enum):
    """
    Lifecycle maturation states of operational knowledge in the canonical graph.
    """
    CANDIDATE = "CANDIDATE"         # Proposed hypothesis or discovered relationship awaiting review
    UNDER_REVIEW = "UNDER_REVIEW"   # Actively under evaluation in human SME inbox
    VALIDATED = "VALIDATED"         # Approved by SME, pending ingestion into active graph
    PROMOTED = "PROMOTED"           # Promoted to canonical status, actively used in triage reasoning
    REJECTED = "REJECTED"           # Refuted and archived with rationale
    SUPERSEDED = "SUPERSEDED"       # Replaced by newer or more accurate topology/causal model
    STALE = "STALE"                 # Flagged as obsolete due to topology or configuration shifts
    CONTRADICTED = "CONTRADICTED"   # Contradicted by subsequent empirical telemetry
    REVOKED = "REVOKED"             # Administratively retracted from the operational brain


class ValidationRecord(Contract):
    """
    Immutable audit record documenting an SME's review of a candidate knowledge element.

    Attributes:
        validation_id: Unique audit record identifier.
        candidate_id: Identifier of the candidate relationship or pattern under review.
        decision: Final review determination (ACCEPT, REJECT, MODIFY, NEED_MORE_EVIDENCE).
        validated_by_role: Human engineering title or persona (e.g. 'Transport Domain SME').
        reason: Technical justification for the decision.
        timestamp: Time at which the validation decision was signed.
        evidence_refs: Supporting evidence IDs reviewed during the validation process.
        modified_relation: Corrected dictionary payload if decision was MODIFY.
    """
    validation_id: str = Field(description="Unique audit record identifier")
    candidate_id: str = Field(description="Reference ID of the candidate item being validated")
    decision: ValidationDecisionType = Field(description="Formal determination rendered by reviewer")
    validated_by_role: str = Field(
        default="Transport Domain SME",
        description="Engineering persona or stakeholder role authoring this validation"
    )
    reason: str = Field(description="Explanatory rationale and technical justification")
    timestamp: datetime = Field(description="Timestamp when validation was signed")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Evidence item identifiers reviewed in reaching this determination"
    )
    modified_relation: dict[str, Any] | None = Field(
        default=None,
        description="Modified payload applied if decision was MODIFY"
    )


class PromotionRecord(Contract):
    """
    Authoritative record capturing the formal promotion of knowledge into canonical gbrain.

    Attributes:
        promotion_id: Unique promotion event identifier.
        candidate_id: Originating candidate ID.
        validation_id: Associated ValidationRecord establishing audit trail.
        canonical_from: Source entity canonical slug.
        relation: Promoted edge relationship type.
        canonical_to: Destination entity canonical slug.
        display_from: Source entity display name.
        display_relation: Human-readable relationship label.
        display_to: Destination entity display name.
        status: Current status (default PROMOTED).
        provenance: Metadata tracing originating episode, author, and timestamp.
        rollback_supported: Whether this promotion can be safely un-promoted.
    """
    promotion_id: str = Field(description="Unique promotion event identifier")
    candidate_id: str = Field(description="Originating candidate ID")
    validation_id: str = Field(description="Reference to supporting ValidationRecord")
    canonical_from: str = Field(description="Canonical slug of source entity")
    relation: str = Field(description="Promoted relation type (e.g. 'routes-through')")
    canonical_to: str = Field(description="Canonical slug of target entity")
    display_from: str = Field(description="Human-friendly label of source entity")
    display_relation: str = Field(description="Human-friendly label of relationship")
    display_to: str = Field(description="Human-friendly label of target entity")
    status: KnowledgePromotionState = Field(
        default=KnowledgePromotionState.PROMOTED,
        description="Current promotion lifecycle state"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed origin provenance (incident_id, episode_id, agent_id)"
    )
    rollback_supported: bool = Field(
        default=True,
        description="Indicates whether this entry supports zero-impact rollback"
    )


class LearningLedgerEntry(Contract):
    """
    Longitudinal tracking ledger recording how promoted knowledge performs across operational episodes.

    Attributes:
        knowledge_id: Promoted knowledge identifier.
        display_name: Concise descriptive label.
        canonical_from: Source node canonical slug.
        relation: Edge type.
        canonical_to: Target node canonical slug.
        state: Current lifecycle state.
        discovered_in: Incident ID where this knowledge was first discovered.
        validated_by: SME role or validator identifier.
        reused_in: List of subsequent incident IDs where this knowledge was applied.
        helpful_reuse_count: Incidents where this knowledge accelerated accurate triage.
        harmful_reuse_count: Incidents where this knowledge introduced negative transfer or delays.
        last_verified_at: Most recent timestamp when validity was empirically confirmed.
    """
    knowledge_id: str = Field(description="Canonical knowledge identifier")
    display_name: str = Field(description="Human-readable title of knowledge item")
    canonical_from: str = Field(description="Canonical slug of source node")
    relation: str = Field(description="Relationship type")
    canonical_to: str = Field(description="Canonical slug of target node")
    state: KnowledgePromotionState = Field(description="Current promotion lifecycle state")
    discovered_in: str = Field(description="Originating incident ID where discovery occurred")
    validated_by: str = Field(description="Validator identifier or role")
    reused_in: list[str] = Field(
        default_factory=list,
        description="List of subsequent incident IDs where this knowledge was applied"
    )
    helpful_reuse_count: int = Field(default=0, description="Count of episodes where knowledge assisted resolution")
    harmful_reuse_count: int = Field(default=0, description="Count of episodes where knowledge misdirected reasoning")
    last_verified_at: datetime = Field(description="Timestamp of most recent empirical verification")


class LearningUnit(Contract):
    """
    Evaluation unit pairing discovery and future validation episodes to benchmark continuous learning.

    Attributes:
        learning_unit_id: Unique benchmark unit identifier.
        cohort: Transfer test cohort ('positive_transfer', 'cross_domain_transfer', 'stale_topology', 'poisoned_validation').
        discovery_incident: First incident where pattern/relationship was identified.
        candidate_knowledge_id: Candidate finding extracted from discovery.
        validation_decision: Review decision applied to the finding.
        promoted_knowledge: Resulting promoted records injected into graph.
        future_incident: Subsequent test incident evaluating transfer efficacy.
        expected_learning_value: Hypothesized diagnostic delta or benchmark expectation.
    """
    learning_unit_id: str = Field(description="Unique learning benchmark unit identifier")
    cohort: str = Field(
        description="Evaluation cohort: positive_transfer, cross_domain_transfer, stale_topology, poisoned_validation"
    )
    discovery_incident: str = Field(description="Incident ID where insight originated")
    candidate_knowledge_id: str = Field(description="Candidate knowledge identifier")
    validation_decision: ValidationDecisionType = Field(description="Review decision applied")
    promoted_knowledge: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Serialized knowledge records promoted to the graph"
    )
    future_incident: str = Field(description="Subsequent test incident ID testing transfer")
    expected_learning_value: str = Field(description="Anticipated diagnostic speedup or accuracy gain")


class LearningPerformanceDelta(Contract):
    """
    Empirical quantitative measurement of performance change achieved through knowledge promotion.

    Attributes:
        learning_unit_id: Reference to evaluated LearningUnit.
        cohort: Evaluation cohort name.
        root_cause_rank_before: Rank of true root cause hypothesis prior to knowledge injection.
        root_cause_rank_after: Rank of true root cause hypothesis after knowledge injection.
        rank_improvement: Arithmetic improvement in ranking position.
        terminal_state_before: Investigation terminal outcome before knowledge.
        terminal_state_after: Investigation terminal outcome after knowledge.
        explanation_coverage_before: Coverage fraction without knowledge.
        explanation_coverage_after: Coverage fraction with knowledge.
        evidence_requests_count_before: Number of queries needed without knowledge.
        evidence_requests_count_after: Number of queries needed with knowledge.
        knowledge_reused: True if promoted knowledge was active in reasoning.
        learning_value_score: Composite score quantifying net learning utility (-1.0 to +1.0).
        negative_transfer_flag: True if promoted knowledge degraded performance.
        stale_detected_flag: True if stale knowledge was encountered and flagged.
        contradiction_flag: True if empirical telemetry contradicted promoted knowledge.
    """
    learning_unit_id: str = Field(description="Reference to evaluated LearningUnit")
    cohort: str = Field(description="Evaluation cohort classification")
    root_cause_rank_before: int | None = Field(default=None, description="Hypothesis rank before knowledge")
    root_cause_rank_after: int | None = Field(default=None, description="Hypothesis rank after knowledge")
    rank_improvement: int = Field(default=0, description="Improvement in rank position (positive is better)")
    terminal_state_before: str = Field(description="Terminal state prior to knowledge promotion")
    terminal_state_after: str = Field(description="Terminal state following knowledge promotion")
    explanation_coverage_before: float = Field(default=0.0, description="Symptom coverage ratio before")
    explanation_coverage_after: float = Field(default=0.0, description="Symptom coverage ratio after")
    evidence_requests_count_before: int = Field(default=0, description="Query count prior to knowledge")
    evidence_requests_count_after: int = Field(default=0, description="Query count after knowledge")
    knowledge_reused: bool = Field(default=False, description="Flag indicating whether promoted knowledge was utilized")
    learning_value_score: float = Field(default=0.0, description="Normalized score reflecting diagnostic acceleration")
    negative_transfer_flag: bool = Field(default=False, description="Indicates negative transfer / misleading inference")
    stale_detected_flag: bool = Field(default=False, description="Indicates outdated knowledge was detected")
    contradiction_flag: bool = Field(default=False, description="Indicates conflict with active telemetry")
