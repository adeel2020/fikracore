"""
Pattern & Failure Signature Contracts (Plane 4 - Enterprise Intelligence)
========================================================================
This module defines recurring failure mode patterns and runtime pattern recognition
evaluations in the FikraCore telecom knowledge graph (Plane 4).

Key Architectural Rules:
1. No Directory Silos: Patterns are indexed under the canonical PATTERNS index node in gbrain,
   scoped cleanly by `scope_domains` metadata (not by filesystem path).
2. "Similar != Same": The `PatternRecognitionContract` enforces that high historical similarity
   does not blindly bypass discrimination. Novel features and distinct operational differences
   must be explicitly articulated in `distinction_notes`.
3. Actionable Association: Validated patterns link directly to standard operating procedures
   via `associated_playbook_ref`.
"""

from typing import Any
from pydantic import Field
from .base import Contract, KnowledgeState


class PatternContract(Contract):
    """
    Reusable operational failure signature or incident pattern with cross-episode history.

    Attributes:
        pattern_id: Semantic pattern identifier (e.g. 'PAT_N3_FLAP_UPF_CONGESTION').
        name: Concise technical title describing the failure mode.
        description: Detailed explanation of symptom mechanics and propagation.
        scope_domains: Operational domains where this pattern applies (e.g. ['IP_TRANSPORT', 'PS_CORE']).
        symptoms: Observable alarm, log, or metric signatures characterising the pattern.
        dependencies: Prerequisites or topological relationships required for pattern to emerge.
        affected_services: Telecommunication services degraded when pattern manifests.
        required_entities: Entity types involved in this failure profile (e.g. ['UPF', 'PE_ROUTER']).
        required_signals: Specific metrics exhibiting deviation (e.g. ['interface_crc_errors', 'n3_drop_rate']).
        status: KnowledgeState (CANDIDATE, SUPPORTED, CONFIRMED, STALE).
        matched_incident_count: Lifetime count of operational incidents exhibiting this pattern.
        associated_playbook_ref: Optional RemediationPlaybookContract ID registered to resolve this pattern.
    """
    pattern_id: str = Field(description="Unique semantic pattern identifier (e.g., 'PAT_N3_FLAP_UPF_CONGESTION')")
    name: str = Field(description="Concise technical name describing the failure pattern")
    description: str = Field(default="", description="Comprehensive narrative of causal mechanism and symptoms")
    scope_domains: list[str] = Field(
        default_factory=list,
        description="Target domains where this pattern applies (e.g. ['IP_TRANSPORT', 'PS_CORE'])"
    )
    symptoms: list[str] = Field(
        default_factory=list,
        description="Specific alarm descriptions, metric anomalies, or syslog signatures"
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description="Topological or protocol dependencies required for this pattern"
    )
    affected_services: list[str] = Field(
        default_factory=list,
        description="Subscriber-facing or transport services affected by this failure"
    )
    required_entities: list[str] = Field(
        default_factory=list,
        description="Network node classes that must be present in the blast radius"
    )
    required_signals: list[str] = Field(
        default_factory=list,
        description="Telemetry signals that must exhibit abnormal polarity"
    )
    status: KnowledgeState = Field(
        default=KnowledgeState.CANDIDATE,
        description="Epistemic validation state in gbrain"
    )
    matched_incident_count: int = Field(
        default=0,
        description="Total historical incidents matched against this pattern"
    )
    associated_playbook_ref: str | None = Field(
        default=None,
        description="Reference to RemediationPlaybookContract ID associated with this pattern"
    )


class PatternRecognitionContract(Contract):
    """
    Runtime pattern matching evaluation contract generated during live triage.
    Enforces rigorous comparison between incoming incident telemetry and historical patterns.

    Attributes:
        recognition_id: Semantic recognition evaluation ID.
        incident_id: Active incident being evaluated.
        matched_pattern_id: Historical pattern matched against.
        similarity_score: Mathematical feature overlap score (0.0 to 1.0).
        matched_features: Signatures and symptoms matching the historical template.
        missing_features: Historical symptoms expected by template but absent in this incident.
        novelty_score: Degree of unprecedented symptoms observed (0.0 to 1.0).
        distinction_notes: Explicit SME narrative explaining why "similar != same",
                           preventing premature cognitive lock-in.
    """
    recognition_id: str = Field(description="Unique pattern match evaluation identifier")
    incident_id: str = Field(description="Active incident ID under investigation")
    matched_pattern_id: str = Field(description="Reference ID of the candidate PatternContract")
    similarity_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Multi-feature vector similarity score against pattern profile"
    )
    matched_features: list[str] = Field(
        default_factory=list,
        description="Constituent alarms and metric deviations corroborated by active incident"
    )
    missing_features: list[str] = Field(
        default_factory=list,
        description="Expected pattern signatures that are missing from active telemetry"
    )
    novelty_score: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Metric indicating proportion of unexplained or unpredicted symptoms"
    )
    distinction_notes: str = Field(
        default="",
        description="Critical NOC SME analysis explaining why similar is not identical"
    )
