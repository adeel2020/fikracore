"""
Root Cause Analysis Contract
============================
Defines the authoritative diagnostic conclusion identifying the origin entity,
fault classification, and empirical evidence backing a diagnosed operational condition.
Fully incident- and event-agnostic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class RootCauseCandidate(BaseContract):
    """Ranked root cause candidate hypothesis."""
    entity_id: str = Field(description="Identifier of candidate network element, interface, or process")
    entity_type: Optional[str] = Field(default=None, description="Category of entity")
    domain: str = Field(description="Technical domain of candidate")
    confidence: float = Field(default=0.0, description="Bayesian or heuristic confidence score (0.0 to 1.0)")
    fault_type: str = Field(description="Classification of suspected fault mechanism")
    rationale: str = Field(default="", description="Explanatory summary justifying candidate ranking")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Associated evidence IDs")


class RootCauseAnalysisContract(BaseContract):
    """
    Authoritative Root Cause Analysis result produced by diagnostic reasoning.
    Agnostic to incident type, event trigger, or network vendor.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="RootCauseAnalysis", description="Contract kind identifier")
    
    analysis_id: str = Field(description="Unique diagnostic analysis identifier")
    event_ref: Optional[str] = Field(default=None, description="Associated event, ticket, or investigation identifier")
    
    # Primary Diagnosed Culprit
    primary_culprit_entity: str = Field(
        description="Authoritative root culprit network element, link, or software component"
    )
    primary_domain: str = Field(description="Originating technical domain of the root cause")
    fault_classification: str = Field(
        description="Standardized technical fault type (e.g. HARDWARE_FAILURE, CONFIG_DRIFT, OPTICAL_DEGRADATION, PROTOCOL_FLAP)"
    )
    confidence_score: float = Field(
        default=0.0,
        description="Normalized confidence score of the diagnosis (0.0 to 1.0)"
    )
    
    # Empirical Evidence & Chain of Reasoning
    supporting_evidence_ids: List[str] = Field(
        default_factory=list,
        description="Admitted telemetry, alarm, or probe evidence records directly substantiating the diagnosis"
    )
    ranked_alternatives: List[RootCauseCandidate] = Field(
        default_factory=list,
        description="Competing alternative candidates evaluated and eliminated or ranked lower"
    )
    diagnostic_summary: str = Field(
        default="",
        description="Concise human-interpretable technical explanation of the failure mechanism"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extension metadata")
