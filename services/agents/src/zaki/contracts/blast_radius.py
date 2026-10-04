"""
Blast Radius Assessment Contract
================================
Defines the spatial and logical failure envelope of an operational disruption,
anomaly, or planned maintenance event across physical and logical domains.
Fully incident- and event-agnostic.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field

from .base import BaseContract


class BlastRadiusTier(str, Enum):
    """Normalized blast radius impact severity tier."""
    NETWORK_WIDE = "NETWORK_WIDE"   # Multi-region or backbone-wide failure
    REGIONAL = "REGIONAL"           # Spanning multiple metropolitan areas or core sites
    MULTI_DOMAIN = "MULTI_DOMAIN"   # Traversing cross-domain boundaries (e.g., transport to core)
    DOMAIN = "DOMAIN"               # Contained within a single technical domain
    LOCAL = "LOCAL"                 # Contained within a single node, cluster, or interface
    NONE = "NONE"                   # Zero detected downstream impact


class BlastRadiusAssessmentContract(BaseContract):
    """
    Quantifies the impacted infrastructure boundary and demarcated observational symptoms.
    Agnostic to incident type, event trigger, or specific network domain.
    """
    api_version: str = Field(default="zaki.ai/v1", description="Contract API schema version")
    kind: str = Field(default="BlastRadiusAssessment", description="Contract kind identifier")
    
    assessment_id: str = Field(description="Unique assessment identifier")
    event_ref: Optional[str] = Field(default=None, description="Reference to triggering incident, change, or event ID")
    
    # Impacted Infrastructure Boundary
    tier: BlastRadiusTier = Field(
        default=BlastRadiusTier.LOCAL,
        description="Overall blast radius containment tier"
    )
    impacted_domains: List[str] = Field(
        default_factory=list,
        description="List of technical domains exhibiting active degradation or alarm propagation"
    )
    affected_entities: List[str] = Field(
        default_factory=list,
        description="Identifiers of physical/logical network elements directly experiencing failure or degradation"
    )
    
    # Observational Symptoms (Explicitly demarcated from causal network nodes)
    observational_symptoms: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Demarcated symptoms, telemetry alarms, and customer trouble ticket summaries"
    )
    
    # Scope Metrics
    total_affected_nodes: int = Field(default=0, description="Total count of affected network elements")
    cross_domain_propagation: bool = Field(
        default=False,
        description="True if degradation crosses domain boundaries"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary extension properties")
