"""
Topology & Blast Radius Contracts (Plane 1 - Topology Plane)
============================================================
This module defines the canonical structural contracts representing physical, logical,
and redundancy topologies within the FikraCore telecom knowledge graph (Plane 1).

Key Capabilities:
1. Typed Edge Relationships:
   - Physical/Virtual: connected-to, routes-through, depends-on, carried-by, backhauled-by
   - High Availability (HA) & Redundancy: HA_PAIR_WITH, BACKUP_PATH_FOR, STANDBY_REDUNDANT_TO
   - Causal & Operational: CAUSED, SUPPORTS, CONTRADICTS, MITIGATED_BY
2. Candidate Relationships:
   - Discovered multi-hop dependencies awaiting SME promotion.
3. Blast Radius Assessment:
   - Multi-tier impact quantification across entities, services, domains, and regions.
"""

from enum import Enum
from pydantic import Field
from .base import Contract, KnowledgeState


class TypedEdgeType(str, Enum):
    """
    Canonical edge classifications connecting nodes in the telecom knowledge graph.
    Covers physical connectivity, logical encapsulation, high availability, and causal links.
    """
    # Physical & Virtual Connectivity
    CONNECTED_TO = "connected-to"                 # Direct physical or L2 link between elements
    ROUTES_THROUGH = "routes-through"             # IP/MPLS forwarding hop or routing adjacency
    DEPENDS_ON = "depends-on"                     # Functional or control plane dependency
    CARRIED_BY = "carried-by"                     # Optical/WDM transport payload mapping
    BACKHAULED_BY = "backhauled-by"               # Midhaul/backhaul transport segment
    SUPPORTS_SERVICE = "supports-service"         # Infrastructure underpinning a subscriber service
    AUTHENTICATES_VIA = "authenticates-via"       # AAA, HSS, UDM authentication pathway
    MONITORED_BY = "monitored-by"                 # OSS/EMS telemetry collector attachment

    # High Availability (HA) & Redundancy Relationships
    HA_PAIR_WITH = "HA_PAIR_WITH"                 # Active/Standby or Active/Active 1:1 redundancy pair
    BACKUP_PATH_FOR = "BACKUP_PATH_FOR"           # Alternative routing path or failover circuit
    STANDBY_REDUNDANT_TO = "STANDBY_REDUNDANT_TO" # Cold or warm standby node

    # Causal & Operational Relationships
    CAUSED = "CAUSED"                             # Confirmed causal trigger or propagation
    SUPPORTS = "SUPPORTS"                         # Evidence corroborating a hypothesis
    CONTRADICTS = "CONTRADICTS"                   # Evidence refuting a hypothesis
    MITIGATED_BY = "MITIGATED_BY"                 # Playbook or action neutralizing a failure mode


class Relationship(Contract):
    """
    Standard FikraCore relationship contract (100% backward compatible).
    Represents an edge between two network entities or concepts in the knowledge graph.

    Attributes:
        relationship_id: Unique edge identifier.
        source: Canonical ID of source node.
        target: Canonical ID of target node.
        link_type: Relationship string or TypedEdgeType.
        state: Knowledge validation state (CONFIRMED, INFERRED, CANDIDATE, etc.).
        confidence: Epistemic confidence score (0.0 to 1.0).
        provenance: Originating provider or telemetry source.
    """
    relationship_id: str = Field(description="Unique edge identifier")
    source: str = Field(description="Canonical source node ID")
    target: str = Field(description="Canonical target node ID")
    link_type: str = Field(description="Edge semantic type")
    state: KnowledgeState = Field(default=KnowledgeState.UNKNOWN, description="Epistemic validation state")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Epistemic confidence weight")
    provenance: str = Field(default="operational-provider", description="Originating provider or discovery engine")


class RelationshipContract(Contract):
    """
    Governs first-class typed edges in the Canonical Telecom Knowledge Graph.
    Includes explicit support for redundancy attributes, available failover capacity,
    and live link health.

    Attributes:
        relationship_id: Semantic edge identifier (e.g., 'REL_PE1_PE2_HA').
        source_entity: Source entity canonical slug.
        target_entity: Target entity canonical slug.
        edge_type: Strongly typed edge classification.
        is_redundancy_edge: True if edge represents an HA or backup bypass.
        redundancy_capacity_percent: Available failover throughput capacity (0-100%).
        health_status: Live operational state ('OPERATIONAL', 'DEGRADED', 'FAILED').
        verified_by_graph: True if verified against authoritative network inventory.
    """
    relationship_id: str = Field(description="Semantic unique edge identifier")
    source_entity: str = Field(description="Canonical slug of origin node")
    target_entity: str = Field(description="Canonical slug of destination node")
    edge_type: TypedEdgeType = Field(description="Strongly typed relationship type")
    is_redundancy_edge: bool = Field(default=False, description="Flag indicating high availability protection link")
    redundancy_capacity_percent: float = Field(
        default=100.0, ge=0.0, le=100.0,
        description="Available traffic throughput capacity during failover"
    )
    health_status: str = Field(
        default="OPERATIONAL",
        description="Live status of the link: OPERATIONAL, DEGRADED, or FAILED"
    )
    verified_by_graph: bool = Field(
        default=True,
        description="Whether link has been verified against authoritative inventory"
    )


class CandidateRelationship(Contract):
    """
    Represents an unverified or newly discovered relationship proposed by an agent.
    Awaits SME review or automated discrimination validation before promotion.

    Attributes:
        candidate_id: Unique candidate proposal ID.
        source: Proposed source node.
        target: Proposed target node.
        proposed_type: Proposed TypedEdgeType string.
        state: Always CANDIDATE until promoted or rejected.
        supporting_evidence: List of evidence IDs that prompted this proposal.
        reason: Diagnostic justification from proposing agent.
    """
    candidate_id: str = Field(description="Unique candidate proposal identifier")
    source: str = Field(description="Source network node slug")
    target: str = Field(description="Target network node slug")
    proposed_type: str = Field(default="connected-to", description="Proposed edge classification")
    state: KnowledgeState = Field(default=KnowledgeState.CANDIDATE, description="Lifecycle promotion state")
    supporting_evidence: list[str] = Field(description="Evidence IDs justifying this candidate link")
    reason: str = Field(description="Causal or diagnostic rationale articulated by proposing agent")


class BlastRadiusLevel(str, Enum):
    """
    Geographic and functional blast radius impact tiers.
    """
    LOCAL = "LOCAL"                 # Isolated to single element or port
    DOMAIN = "DOMAIN"               # Constrained within single domain (e.g. RAN site cluster)
    MULTI_DOMAIN = "MULTI_DOMAIN"   # Crossing domain boundaries (e.g. Transport affecting Core)
    REGIONAL = "REGIONAL"           # Affecting an entire metro or administrative region
    NETWORK_WIDE = "NETWORK_WIDE"   # Threatening nationwide or catastrophic blackout


class BlastRadiusAssessment(Contract):
    """
    Quantifies the cumulative blast radius of an incident, failure, or planned change.

    Attributes:
        directly_affected_entities: Nodes with immediate failure or alarm state.
        indirectly_affected_entities: Upstream/downstream nodes suffering secondary impact.
        affected_services: User-facing services impacted (e.g. VoLTE, 5G Data, Enterprise VPN).
        affected_domains: Technical domains breached by incident propagation.
        affected_regions: Geographic areas impacted.
        blast_radius_level: Overall blast radius classification level.
        confidence: Certainty score of the assessment.
        customer_facing_impact: Summary of end-user subscriber degradation.
    """
    directly_affected_entities: list[str] = Field(
        default_factory=list,
        description="Entities exhibiting direct failure or active primary alarms"
    )
    indirectly_affected_entities: list[str] = Field(
        default_factory=list,
        description="Downstream entities affected by traffic shift or loss of dependency"
    )
    affected_services: list[str] = Field(
        default_factory=list,
        description="Subscriber-facing services degraded by this condition"
    )
    affected_domains: list[str] = Field(
        default_factory=list,
        description="Operational domains traversed by the degradation path"
    )
    affected_regions: list[str] = Field(
        default_factory=list,
        description="Geographic operational territories affected"
    )
    blast_radius_level: BlastRadiusLevel = Field(
        default=BlastRadiusLevel.LOCAL,
        description="Categorical blast radius tier"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Epistemic confidence in assessment")
    customer_facing_impact: str = Field(
        default="",
        description="Human-readable assessment of subscriber impact"
    )
